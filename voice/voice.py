import os
import time
import json
import openai
import requests
import speech_recognition as sr
import subprocess
import tempfile
from urllib.request import urlretrieve

from dotenv import load_dotenv
from elevenlabs import generate, set_api_key

# -------------------------------------------------------------------
# 1. LOAD ENVIRONMENT VARIABLES
# -------------------------------------------------------------------
load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
GOOEY_API_KEY = os.getenv('GOOEY_API_KEY')

if not all([OPENAI_API_KEY, ELEVENLABS_API_KEY, GOOEY_API_KEY]):
    raise ValueError("Missing one or more required API keys in your .env file.")

openai.api_key = OPENAI_API_KEY
set_api_key(ELEVENLABS_API_KEY)

# -------------------------------------------------------------------
# 2. MAINTAIN CONVERSATION HISTORY
# -------------------------------------------------------------------
conversation_history = [
    {"role": "system", "content": "You are a friendly AI assistant. Keep responses concise and engaging."}
]

# -------------------------------------------------------------------
# 3. CAPTURE SPEECH FROM MICROPHONE
# -------------------------------------------------------------------
def transcribe_speech_to_text():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("\nListening... (Say 'end process' to stop)")
        recognizer.adjust_for_ambient_noise(source)  # reduce background noise
        audio_data = recognizer.listen(source)

    try:
        text = recognizer.recognize_google(audio_data).strip().lower()
        print(f"You said: {text}")
        return text
    except sr.UnknownValueError:
        print("Didn't catch that. Please repeat.")
        return None
    except sr.RequestError as e:
        print(f"Speech Recognition error: {e}")
        return None

# -------------------------------------------------------------------
# 4. GET A RESPONSE FROM OPENAI
# -------------------------------------------------------------------
def get_openai_chat_response(prompt):
    global conversation_history
    conversation_history.append({"role": "user", "content": prompt})
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=conversation_history,
            max_tokens=150,
            temperature=0.8
        )
        ai_response = response['choices'][0]['message']['content'].strip()
        conversation_history.append({"role": "assistant", "content": ai_response})
        return ai_response
    except Exception as e:
        print(f"Error calling OpenAI: {e}")
        return "I encountered an error. Please try again."

# -------------------------------------------------------------------
# 5. GENERATE LIP-SYNCED VIDEO (MP4) WITH AUDIO
# -------------------------------------------------------------------
def generate_lipsync_video(text):
    """
    1. Uses ElevenLabs to create TTS audio.
    2. Sends audio + 'avatar.png' to Gooey.ai to produce a lip-synced MP4.
    3. Returns the local path to that MP4.
    """
    try:
        # 5.1 Generate TTS audio with ElevenLabs
        print("Generating TTS audio...")
        audio_data = generate(
            text=text,
            voice="Eric",
            model="eleven_multilingual_v2"
        )

        # Save audio temporarily
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
            audio_path = temp_wav.name
            temp_wav.write(audio_data)

        # 5.2 Call Gooey.ai to produce lip-synced video
        print("Calling Gooey.ai Lipsync to produce MP4...")
        with open(audio_path, "rb") as audio_file, open("avatar.png", "rb") as face_file:
            files = {
                "json": (None, json.dumps({}), "application/json"),
                "input_face": ("avatar.png", face_file, "image/png"),
                "input_audio": ("audio.wav", audio_file, "audio/wav")
            }
            response = requests.post(
                "https://api.gooey.ai/v2/Lipsync/form/",
                headers={"Authorization": f"bearer {GOOEY_API_KEY}"},
                files=files
            )
            response.raise_for_status()

        # 5.3 Parse response and download the resulting MP4
        result = response.json()
        mp4_url = result["output"]["output_video"]
        print(f"Lip-sync MP4 URL: {mp4_url}")

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_mp4:
            mp4_path = temp_mp4.name
            urlretrieve(mp4_url, mp4_path)
        
        # Clean up the temporary audio
        if os.path.exists(audio_path):
            os.remove(audio_path)

        return mp4_path

    except Exception as e:
        print(f"Error generating lip-sync video: {e}")
        return None

# -------------------------------------------------------------------
# 6. PLAY THE MP4 WITH ITS OWN AUDIO
# -------------------------------------------------------------------
def play_mp4_with_default_player(mp4_path):
    """
    Opens the MP4 file in the operating system's default video player.
    """
    if not mp4_path or not os.path.exists(mp4_path):
        print("No valid MP4 file to play.")
        return
    
    print(f"Playing MP4: {mp4_path}")

    if os.name == "nt":  # Windows
        os.startfile(mp4_path)
    elif os.name == "posix":  # macOS or Linux
        # macOS
        if "Darwin" in os.uname().sysname:
            subprocess.run(["open", mp4_path])
        else:
            # Linux or other *nix
            subprocess.run(["xdg-open", mp4_path])
    else:
        print("Unsupported OS: cannot auto-play the video.")

# -------------------------------------------------------------------
# 7. MAIN LOGIC: CAPTURE SPEECH -> OPENAI -> LIPSYNC MP4 -> PLAY
# -------------------------------------------------------------------
def main():
    print("AI Lip-Sync Demo Started!")
    while True:
        user_text = transcribe_speech_to_text()
        if not user_text:
            continue

        if "end process" in user_text:
            print("Ending process. Goodbye!")
            break

        # Get AI response
        ai_response = get_openai_chat_response(user_text)
        print(f"\nAI says: {ai_response}\n")

        # Generate MP4 with embedded audio
        mp4_file = generate_lipsync_video(ai_response)
        if mp4_file:
            # Play it in the system's default player
            play_mp4_with_default_player(mp4_file)

            # OPTIONAL: Wait a few seconds if you want to auto-delete it after playback
            # time.sleep(10)
            # os.remove(mp4_file)

if __name__ == "__main__":
    main()
