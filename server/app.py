from flask import Flask, request, jsonify, make_response, Response, send_from_directory
from flask_cors import CORS
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from pymongo.errors import DuplicateKeyError
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os
from bson import ObjectId
from datetime import datetime
from flask_socketio import SocketIO, emit
from twilio.rest import Client
import base64
import tempfile
import sys
import json
import time
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'voice'))
from voice import get_gemini_chat_response, speak_text, transcribe_speech_to_text, generate_lipsync_video

# Load environment variables
load_dotenv()

# Initialize OpenAI client
from openai import OpenAI
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

if not os.getenv('OPENAI_API_KEY'):
    raise ValueError("OPENAI_API_KEY not found in environment variables")

app = Flask(__name__, static_folder='static')
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:3000"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})
socketio = SocketIO(app, cors_allowed_origins="*")

# MongoDB connection
uri = os.getenv('MONGODB_URI')
client = MongoClient(uri, tlsAllowInvalidCertificates=True)
db = client.robot_control  # database name
users = db.users  # collection name

# Create indexes
users.create_index('username', unique=True)

# Test MongoDB connection
try:
    client.admin.command('ping')
    print("Successfully connected to MongoDB!")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")

# Create test user if it doesn't exist
test_user = {
    "username": "admin",
    "password": generate_password_hash("password123"),
    "phone_number": "1234567890",
    "created_at": datetime.utcnow()
}

try:
    # Only insert if user doesn't exist
    if not users.find_one({"username": "admin"}):
        users.insert_one(test_user)
        print("Test user created successfully")
except Exception as e:
    print(f"Error creating test user: {e}")

# Initialize Twilio client
twilio_client = Client(
    os.getenv('TWILIO_ACCOUNT_SID'),
    os.getenv('TWILIO_AUTH_TOKEN')
)


def send_sms_notification(message):
    """Send SMS notification using Twilio"""
    try:
        twilio_client.messages.create(
            body=message,
            from_=os.getenv('TWILIO_PHONE_NUMBER'),
            to=os.getenv('USER_PHONE_NUMBER')
        )
        print("SMS sent successfully: ", message)
        return True
    except Exception as e:
        print(f"Error sending SMS: {str(e)}")
        return False

def process_audio(audio_data):
    """Process audio data using OpenAI Whisper"""
    try:
        # Save base64 audio data to temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as temp_audio:
            audio_bytes = base64.b64decode(audio_data.split(',')[1])
            temp_audio.write(audio_bytes)
            temp_audio.flush()

            # Transcribe audio using Whisper
            with open(temp_audio.name, "rb") as audio_file:
                transcript = openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
            print("Transcript: ", transcript.text)
            return transcript.text
    except Exception as e:
        print(f"Error processing audio: {str(e)}")
        return None

def generate_summary(transcript):
    """Generate a summary using OpenAI GPT"""
    try:
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
            {"role": "system", "content": "You are a helpful assistant that summarizes completed tasks."},
            {"role": "user", "content": f"Please provide a brief, clear summary of this completed task: {transcript}"}
        ],
        max_tokens=150)
        print('summary: ', response.choices[0].message.content)
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating summary: {str(e)}")
        return None

@socketio.on('voice_data')
def handle_voice_data(data):
    """Handle incoming voice data"""
    try:
        # Process the audio
        transcript = process_audio(data['audio'])
        if not transcript:
            emit('voice_response', {'error': 'Failed to process audio'})
            return

        # Generate summary
        summary = generate_summary(transcript)
        if not summary:
            emit('voice_response', {'error': 'Failed to generate summary'})
            return

        # Send SMS notification
        print('summary: ', summary)
        sms_sent = send_sms_notification(summary)

        # Send response back to client
        emit('voice_response', {
            'success': True,
            'transcript': transcript,
            'summary': summary,
            'sms_sent': sms_sent
        })
    except Exception as e:
        emit('voice_response', {'error': str(e)})

@app.route('/api/register', methods=['POST', 'OPTIONS'])
def register():
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        return response

    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    phone = data.get('phone_number')

    if not username or not password or not phone:
        return jsonify({"error": "Missing required fields"}), 400

    # Basic phone number validation
    phone = ''.join(filter(str.isdigit, phone))
    if len(phone) < 10:
        return jsonify({'error': 'Invalid phone number'}), 400

    # Hash the password
    hashed_password = generate_password_hash(password)

    try:
        users.insert_one({
            "username": username,
            "password": hashed_password,
            "phone_number": phone,
            "created_at": datetime.utcnow()
        })
        return jsonify({"message": "User registered successfully"}), 201
    except DuplicateKeyError:
        return jsonify({"error": "Username already exists"}), 409
    except Exception as e:
        print(f"Registration error: {str(e)}")
        return jsonify({"error": "Registration failed"}), 500

@app.route('/api/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        return response

    data = request.get_json()

    if not data or 'username' not in data or 'password' not in data:
        return jsonify({"error": "Missing username or password"}), 400

    user = users.find_one({"username": data['username']})

    if user and check_password_hash(user['password'], data['password']):
        return jsonify({
            "message": "Login successful",
            "username": user['username']
        }), 200
    else:
        return jsonify({"error": "Invalid username or password"}), 401

@app.route('/handle_voice', methods=['POST'])
def handle_voice():
    print('handle_voice called')
    try:
        data = request.json
        if not data or 'audio' not in data:
            print('No audio data received')
            return jsonify({'error': 'No audio data received'}), 400

        # Process the audio using the existing Whisper transcription
        transcript = process_audio(data['audio'])
        if not transcript:
            print('Failed to process audio')
            return jsonify({'error': 'Failed to process audio'}), 400

        # Get AI response using Gemini
        ai_response = get_gemini_chat_response(transcript)
        if not ai_response:
            print('Failed to get AI response')
            return jsonify({'error': 'Failed to get AI response'}), 400

        # Generate lip-sync video using Gooey.ai
        video_filename = generate_lipsync_video(ai_response)
        if video_filename:
            # Store the video URL for the event stream
            app.current_video_url = f'http://localhost:5001/static/videos/{video_filename}'
            
        # Generate voice response using ElevenLabs
        try:
            speak_text(ai_response)
        except Exception as e:
            print(f'Error generating voice response: {e}')
            
        return jsonify({
            'success': True,
            'transcript': transcript,
            'response': ai_response,
            'videoUrl': app.current_video_url if hasattr(app, 'current_video_url') else None
        })
    except Exception as e:
        print(f"Error processing voice: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/video-stream')
def video_stream():
    def generate():
        while True:
            # Check if there's a new video
            if hasattr(app, 'current_video_url'):
                data = json.dumps({
                    'videoUrl': app.current_video_url
                })
                yield f"data: {data}\n\n"
                # Clear the current video URL
                delattr(app, 'current_video_url')
            time.sleep(0.1)

    return Response(generate(), mimetype='text/event-stream')

@app.route('/static/videos/<path:filename>')
def serve_video(filename):
    return send_from_directory('static/videos', filename)

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5001)
