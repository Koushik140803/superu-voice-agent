#   vocode_custom_agent.py

from vocode.streaming.agent.base_agent import RespondAgent
from agent_config import GroqAgentConfig
import requests
import os
from dotenv import load_dotenv
import json
import logging

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

class GroqVoiceAgent(RespondAgent[GroqAgentConfig]):
    async def respond(self, human_input: str, conversation_id: str, is_interrupt: bool = False):
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "llama3-8b-8192",
            "messages": [
                {"role": "system", "content": "You are a polite assistant that helps schedule meetings. Ask for the user's email, topic, and preferred time.  If the user provides incomplete information, ask clarifying questions. Check for calendar availability before confirming. Be conversational and helpful."},
                {"role": "user", "content": human_input}
            ]
        }

        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()  # Raise an exception for bad status codes

            if response.status_code == 200:
                reply = response.json()["choices"][0]["message"]["content"]
                return reply, False
            else:
                logging.error(f"Groq API error: {response.status_code}, {response.text}")
                return "I'm sorry, I had trouble processing that. Please try again.", False

        except requests.exceptions.RequestException as e:
            logging.error(f"Error communicating with Groq API: {e}")
            return "I'm sorry, I encountered a network error. Please try again.", False
        except json.JSONDecodeError as e:
            logging.error(f"Error decoding Groq API response: {e}, Response text: {response.text if 'response' in locals() else 'No response'}")
            return "I'm sorry, I received an invalid response from the server.", False
        except KeyError as e:
            logging.error(f"Error extracting content from Groq API response: {e}, Response: {response.text if 'response' in locals() else 'No response'}")
            return "I'm sorry, I received an unexpected response format.", False