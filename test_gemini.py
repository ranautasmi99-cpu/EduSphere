"""
Standalone Gemini API test script.
Run this directly (python test_gemini.py) — completely separate from the Flask app.
This tells us if the problem is in the app's code, or in the Gemini account/API key itself.
"""

import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
print(f"API key loaded: {'Yes' if api_key else 'NO - .env not found or key missing'}")

if not api_key:
    print("STOP: Fix your .env file first, no key was found.")
    exit()

client = genai.Client(api_key=api_key)

try:
    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents="Say hello in one short sentence."
    )
    print("SUCCESS")
    print(response.text)
except Exception as e:
    print("FAILED")
    print(f"Error type: {type(e).__name__}")
    print(f"Error details: {e}")