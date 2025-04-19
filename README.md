# SuperU Voice Agent for Meeting Scheduling

A voice-based assistant that helps users schedule meetings through natural conversation. The agent collects email addresses, meeting topics, and preferred times, then verifies calendar availability before scheduling events in Google Calendar.

## Features

- Natural voice interaction for collecting meeting details
- Email validation and cleaning
- Meeting time parsing with timezone support
- Google Calendar integration for availability checking and event creation
- Confirmation flow with retry options
- Support for scheduling multiple meetings in one session

## Prerequisites

- Python 3.8 or higher
- Google Cloud Platform account with Calendar API enabled
- Groq API key for speech-to-text functionality
- Microphone and speakers/headphones

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/superu-voice-agent.git
   cd superu-voice-agent
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up Google Calendar API credentials:
   - Visit [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project
   - Enable the Google Calendar API
   - Create OAuth2 credentials (Desktop application)
   - Download the credentials as JSON and save as `credentials.json` in the project root

4. Create a `.env` file in the project root with your Groq API key:
   ```
   GROQ_API_KEY=your_groq_api_key_here
   ```

## Usage

1. Run the voice agent:
   ```
   python superu_voice_agent.py
   ```

2. Follow the voice prompts:
   - The agent will ask for your email address
   - Provide a meeting topic
   - Specify your preferred meeting time
   - Confirm the details when prompted
   - Choose whether to schedule another meeting

3. On first run, you'll be prompted to authorize the application with your Google account.

## Troubleshooting

- If you encounter audio device issues, check your default input/output devices
- For authorization issues with Google Calendar, delete the `token.json` file and reauthorize
- Make sure your microphone is unmuted and working properly

## Development Notes

- Meeting details are stored in `meetings.txt` for backup purposes
- The application uses Groq's Whisper model for speech-to-text transcription
- Audio files are temporarily stored during conversations

## Security Considerations

- API keys are stored in the `.env` file and should not be committed to version control
- Google OAuth tokens are managed securely through the standard OAuth flow
- User data is processed locally and only shared with the necessary APIs

## Future Improvements

- Support for recurring meetings
- Multiple calendar integration
- Meeting reminders, notifications and confirmation mails
- More sophisticated conversation handling for complex scenarios

## Demo Video

Want to see it in action?  
[Watch the demo video](https://drive.google.com/file/d/1abcXYZ/view?usp=sharing)
---

## Disclaimer

This project was created as part of an assignment for the company **SuperU**.  
All company names, logos, and references used in this repository are solely for academic or demonstration purposes.  
This is not an official product of SuperU.

