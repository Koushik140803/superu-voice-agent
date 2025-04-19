# superu_voice_agent.py

import os
import time
import pyttsx3
import pyaudio
import wave
from dotenv import load_dotenv
from dateutil import parser, tz, relativedelta
from vocode_custom_agent import GroqVoiceAgent
from agent_config import GroqAgentConfig
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import datetime
import logging
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()

# Text to Speech
tts = pyttsx3.init()

def speak(text):
    tts.say(text)
    tts.runAndWait()

def record_audio(filename, duration=5):
    chunk = 1024
    format = pyaudio.paInt16
    channels = 1
    rate = 16000

    p = pyaudio.PyAudio()
    stream = p.open(format=format, channels=channels, rate=rate, input=True, frames_per_buffer=chunk)
    frames = []

    print("🎙️ Listening...")
    for _ in range(0, int(rate / chunk * duration)):
        data = stream.read(chunk)
        frames.append(data)

    stream.stop_stream()
    stream.close()
    p.terminate()

    wf = wave.open(filename, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(p.get_sample_size(format))
    wf.setframerate(rate)
    wf.writeframes(b''.join(frames))
    wf.close()
    print("✅ Recorded.")

def transcribe(filename):
    import requests
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    url = "https://api.groq.com/openai/v1/audio/transcriptions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    files = {"file": (filename, open(filename, "rb")), "model": (None, "whisper-large-v3-turbo")}
    try:
        res = requests.post(url, headers=headers, files=files)
        return res.json().get("text", "") if res.status_code == 200 else ""
    except Exception as e:
        logging.error(f"Transcription failed: {e}")
        return ""

def ask_and_transcribe(question, filename, duration=8, required=True):
    for _ in range(3):
        speak(question)
        record_audio(filename, duration)
        response = transcribe(filename)
        if response.strip():
            return response
        if not required:
            return ""
        speak("Sorry, I didn't catch that. Could you please repeat?")
    raise ValueError("Failed to get a valid response after multiple attempts.")

def clean_email(email_text):
    email_text = email_text.lower().replace(" at ", "@").replace(" dot ", ".").replace(" ", "")
    return email_text if re.match(r"[^@]+@[^@]+\.[^@]+", email_text) else None

def save_meeting(email, topic, time_pref):
    try:
        with open("meetings.txt", "a") as f:
            f.write(f"Email: {email}\nTopic: {topic}\nTime: {time_pref}\n---\n")
        logging.info("Meeting saved.")
    except Exception as e:
        logging.error(f"Failed to save meeting: {e}")

SCOPES = ['https://www.googleapis.com/auth/calendar.events']
UTC_TZ = tz.tzutc()

def parse_time(time_str):
    try:
        lower_str = time_str.lower().strip()
        now = datetime.datetime.now(tz=tz.tzlocal())

        # Map ambiguous times to specific default hours
        if "afternoon" in lower_str and "at" not in lower_str:
            time_str += " at 12:00 PM"
        elif "morning" in lower_str and "at" not in lower_str:
            time_str += " at 9:00 AM"
        elif "evening" in lower_str and "at" not in lower_str:
            time_str += " at 6:00 PM"
        elif "night" in lower_str and "at" not in lower_str:
            time_str += " at 8:00 PM"
        elif "noon" in lower_str and "at" not in lower_str:
            time_str += " at 12:00 PM"
        elif "midnight" in lower_str and "at" not in lower_str:
            time_str += " at 12:00 AM"

        # Special handling for "tomorrow" phrases
        if "tomorrow" in lower_str:
            tomorrow = now + datetime.timedelta(days=1)
            if "at" in lower_str:
                time_part = lower_str.split("at")[1].strip()
                parsed_time = parser.parse(time_part, fuzzy=True)
                tomorrow = tomorrow.replace(hour=parsed_time.hour, minute=parsed_time.minute, second=0)
            return tomorrow.astimezone(UTC_TZ)

        # Generic parser fallback
        dt = parser.parse(time_str, fuzzy=True)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=tz.tzlocal())
        return dt.astimezone(UTC_TZ)
    except Exception as e:
        logging.error(f"Time parsing failed for input '{time_str}': {e}")
        return None


def create_google_event(email, topic, meeting_time):
    from google_auth_oauthlib.flow import InstalledAppFlow

    credentials_path = os.path.join(os.path.dirname(__file__), 'credentials.json')
    creds = None

    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    else:
        flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
        creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('calendar', 'v3', credentials=creds)

    try:
        end_time = meeting_time + datetime.timedelta(hours=1)
        event = {
            'summary': topic,
            'description': f'Scheduled via Voice Bot by {email}',
            'start': {'dateTime': meeting_time.isoformat(), 'timeZone': 'UTC'},
            'end': {'dateTime': end_time.isoformat(), 'timeZone': 'UTC'},
            'attendees': [{'email': email}],
        }
        event = service.events().insert(calendarId='primary', body=event).execute()
        logging.info(f"Event created: {event.get('htmlLink')}")
        speak("Your meeting has been added to your calendar.")
    except Exception as e:
        logging.error(f"Failed to create event: {e}")
        speak("I couldn't add the event to your calendar.")

def check_calendar_availability(email, time_pref, topic):
    from google_auth_oauthlib.flow import InstalledAppFlow

    credentials_path = os.path.join(os.path.dirname(__file__), 'credentials.json')
    creds = None

    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    else:
        flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
        creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('calendar', 'v3', credentials=creds)

    meeting_time = parse_time(time_pref)
    if not meeting_time:
        return None, "Sorry, I couldn't understand the time you provided."

    start = meeting_time - datetime.timedelta(hours=1)
    end = meeting_time + datetime.timedelta(hours=2)

    events_result = service.events().list(
        calendarId='primary',
        timeMin=start.isoformat(),
        timeMax=end.isoformat(),
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])
    conflicts = [(parser.parse(e['start'].get('dateTime')), parser.parse(e['end'].get('dateTime')))
                 for e in events if 'dateTime' in e['start']]

    for s, e in conflicts:
        if start < e and end > s:
            return None, "That time is already booked. Please suggest a different time."

    return meeting_time, "The time is available."

class DialogueState:
    def __init__(self):
        self.email = None
        self.topic = None
        self.time_pref = None

    def reset(self):
        self.email = self.topic = self.time_pref = None

    def is_complete(self):
        return all([self.email, self.topic, self.time_pref])

def run_agent():
    speak("Hello! I'm your SuperU voice assistant to help you schedule meetings.")
    agent = GroqVoiceAgent(GroqAgentConfig(type="custom"))
    dialogue_state = DialogueState()

    while True:
        try:
            if not dialogue_state.email:
                email_raw = ask_and_transcribe("Please tell me your email address.", "email.wav")
                dialogue_state.email = clean_email(email_raw)
                if not dialogue_state.email:
                    speak("That doesn't seem valid. Let's try again.")
                    continue

            if not dialogue_state.topic:
                dialogue_state.topic = ask_and_transcribe("What is the topic of the meeting?", "topic.wav")

            if not dialogue_state.time_pref:
                dialogue_state.time_pref = ask_and_transcribe("When would you like to schedule the meeting?", "time.wav")

            if dialogue_state.is_complete():
                meeting_time = parse_time(dialogue_state.time_pref)
                if not meeting_time:
                    speak("I couldn't understand the time. Please try again.")
                    dialogue_state.time_pref = None
                    continue
                    # Prevent scheduling past or too-close times
                now_utc = datetime.datetime.now(tz=UTC_TZ)
                print(f"Current time (UTC): {now_utc}")
                print(f"Time + 10 min: {now_utc + datetime.timedelta(minutes=10)}")
                print(f"Meeting time (UTC): {meeting_time}")
                print(f"Is meeting too soon? {meeting_time <= now_utc + datetime.timedelta(minutes=10)}")

                if meeting_time <= now_utc + datetime.timedelta(minutes=10):
                    speak("The time you gave is already past or too soon. Please choose a future time.")
                    dialogue_state.time_pref = None
                    continue
                meeting_time, availability_msg = check_calendar_availability(dialogue_state.email, dialogue_state.time_pref, dialogue_state.topic)
                speak(availability_msg)
                if meeting_time:
                    # Summarize and confirm details
                    speak(f"To confirm, your email is {dialogue_state.email}, topic is {dialogue_state.topic}, and time is {dialogue_state.time_pref}.")
                    confirm = ask_and_transcribe("Is everything correct? Say yes or no.", "confirm.wav", duration=4)

                    if "yes" in confirm.lower():
                        create_google_event(dialogue_state.email, dialogue_state.topic, meeting_time)
                        save_meeting(dialogue_state.email, dialogue_state.topic, dialogue_state.time_pref)
                        speak("Your meeting is scheduled. Thank you!")
                        dialogue_state.reset()
                    else:
                        speak("Okay, let's try again.")
                        dialogue_state.reset()
                else:
                    dialogue_state.time_pref = None

            again = ask_and_transcribe("Would you like to schedule another meeting? Say yes or no.", "again.wav", duration=3, required=False)
            if any(word in again.lower() for word in ["no", "nope", "nah", "not now", "i'm done"]):
                speak("Goodbye!")
                break

        except ValueError as e:
            logging.error(e)
            speak(str(e))
            dialogue_state.reset()
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            speak("An unexpected error occurred. Let's start over.")
            dialogue_state.reset()

if __name__ == "__main__":
    run_agent()
