import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
print("API Key present:", bool(api_key and api_key != "your_gemini_api_key_here"))

client = genai.Client(api_key=api_key)

print("\n--- Listing Available Models ---")
try:
    for m in client.models.list():
        if "generateContent" in (m.supported_actions or []):
            print(f"- {m.name}")
except Exception as e:
    print(f"Error listing models: {e}")
