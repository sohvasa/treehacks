import openai
import speech_recognition as sr
from elevenlabs import generate, play
from elevenlabs import set_api_key
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Get API Keys from environment variables
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')

if not OPENAI_API_KEY or not ELEVENLABS_API_KEY:
    raise ValueError("Missing API keys in .env file")

openai.api_key = OPENAI_API_KEY
set_api_key(ELEVENLABS_API_KEY)

# Context window to keep track of conversation
conversation_history = [
    {"role": "system", "content": "You are a friendly and natural-sounding AI assistant. Keep responses simple and engaging, like a human conversation."}
]


def transcribe_speech_to_text():
    """
    Listens to microphone input and returns recognized text using Google's Speech Recognition.
    """
    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        print("\nListening... (Say 'end process' to stop)")
        recognizer.adjust_for_ambient_noise(source)  # Reduces background noise
        audio_data = recognizer.listen(source)

    try:
        text = recognizer.recognize_google(audio_data).lower()
        print(f"You said: {text}")
        return text
    except sr.UnknownValueError:
        print("Didn't catch that. Can you say it again?")
        return None
    except sr.RequestError as e:
        print(f"Speech Recognition error: {e}")
        return None


def get_openai_chat_response(prompt):
    """
    Sends a prompt to OpenAI Chat API and returns a human-like response.
    """
    global conversation_history

    # Add the new user message to conversation history
    conversation_history.append({"role": "user", "content": prompt})

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=conversation_history,
            max_tokens=100,
            temperature=0.8,  # Increases randomness to sound more human
            n=1
        )

        ai_response = response['choices'][0]['message']['content'].strip()

        # Add AI response to conversation history
        conversation_history.append({"role": "assistant", "content": ai_response})

        return ai_response
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return "Hmm... I ran into a problem. Can you try again?"


def speak_text(text):
    """
    Uses ElevenLabs API (Eric - Eleven Multilingual v2) to generate a more human-like voice response.
    """
    try:
        audio = generate(
            text=text,
            voice="Eric",
            model="eleven_multilingual_v2"
        )
        play(audio)
    except Exception as e:
        print(f"Error using ElevenLabs API: {e}")


def main():
    """
    Runs a continuous conversation loop until the user says "end process".
    """
    print("Chat started! Say 'end process' anytime to stop.")

    while True:
        # Listen to user input
        user_input = transcribe_speech_to_text()

        # Check if user wants to exit
        if user_input is None:
            continue  # Skip to next iteration if no valid input

        if "end process" in user_input:
            print("\nEnding conversation. Take care!")
            speak_text("Goodbye! Have a great day!")
            break

        # Get AI response with context
        ai_response = get_openai_chat_response(user_input)

        if ai_response:
            print("\n--- AI Response ---")
            print(ai_response)

            # Speak out the response using Eric's voice
            speak_text(ai_response)
        else:
            print("No response from AI.")


if __name__ == "__main__":
    main()