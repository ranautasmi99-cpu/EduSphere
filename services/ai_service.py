import os
import json
import re
import time
from google import genai
from google.genai import types

def get_gemini_client():
    """
    Initializes and returns the Google GenAI client using GEMINI_API_KEY from environment.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        raise ValueError("GEMINI_API_KEY environment variable is not set. Please set it in your .env file.")
    
    return genai.Client(api_key=api_key)

def clean_json_response(raw_text):
    """
    Strips markdown code fences (```json ... ```) from raw text output
    so json.loads() can parse it cleanly.
    """
    if not raw_text:
        return ""
    
    cleaned = re.sub(r'^```(?:json)?\s*', '', raw_text.strip(), flags=re.MULTILINE)
    cleaned = re.sub(r'\s*```$', '', cleaned, flags=re.MULTILINE)
    return cleaned.strip()

def generate_study_materials(pdf_text, subject="General"):
    """
    Calls Gemini API with structured instructions to generate revision notes,
    a 5-question MCQ quiz, and a markdown mindmap outline in a single JSON response.
    
    :param pdf_text: Extracted plain text from the uploaded PDF
    :return: Parsed dictionary matching expected schema
    """
    client = get_gemini_client()

    # Preferred model: gemini-3.5-flash-lite (or gemini-flash-latest)
    model_name = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

    system_prompt = """You are an expert AI academic tutor. Analyze the provided lecture material and return ONLY a valid JSON object matching the exact schema below. Do not include markdown code block formatting or preambles.

Exact Required JSON Schema:
{
  "notes": [
    "Bullet point 1 summarizing key concept",
    "Bullet point 2 summarizing key concept"
  ],
  "quiz": [
    {
      "question": "Clear question testing key understanding?",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct_answer": "Option A"
    }
  ],
  "mindmap_markdown": "# Main Topic Title\\n## Key Theme 1\\n- Important Detail A\\n- Important Detail B\\n## Key Theme 2\\n- Important Detail C"
}

Rules:
1. Provide 5 to 8 concise, exam-revision style bullet points in 'notes'.
2. Provide EXACTLY 5 multiple-choice questions in 'quiz'. Each question must have 4 distinct options and 'correct_answer' must exactly match one of the items in 'options'.
3. Provide valid hierarchical Markdown for 'mindmap_markdown' suitable for markmap rendering.
4. Output MUST be strictly valid raw JSON.
5. This material is for a SUBJECT_PLACEHOLDER student. Tailor terminology, examples, and emphasis appropriately for that subject where relevant.
"""
    # NOTE: using .replace() here instead of .format() because the JSON schema
    # example above contains literal { } characters that .format() would
    # misinterpret as format fields.
    system_prompt = system_prompt.replace("SUBJECT_PLACEHOLDER", subject)

    user_content = f"Lecture Material Content:\n\n{pdf_text[:30000]}"

    try:
        # Automatic retry logic for Gemini API 503 (UNAVAILABLE) errors.
        # This handles temporary Google server overloads, which is not a bug in our code.
        max_attempts = 3
        delay = 2
        response = None
        
        for attempt in range(1, max_attempts + 1):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=[system_prompt, user_content],
                    config=types.GenerateContentConfig(
                        temperature=0.2,
                        response_mime_type="application/json"
                    )
                )
                if attempt > 1:
                    print(f"[AI SERVICE LOG] Gemini API call succeeded on attempt {attempt}.")
                break
            except Exception as api_err:
                error_str = str(api_err)
                if "503" in error_str or "UNAVAILABLE" in error_str or "high demand" in error_str.lower():
                    if attempt < max_attempts:
                        print(f"[AI SERVICE WARN] Attempt {attempt} failed with 503 UNAVAILABLE. Retrying in {delay} seconds...")
                        time.sleep(delay)
                        delay *= 2  # Exponential backoff (2s, then 4s)
                        continue
                    else:
                        print(f"[AI SERVICE ERROR] All {max_attempts} attempts failed due to high demand.")
                        raise
                else:
                    # Do not retry on other errors (like invalid API key, bad request)
                    raise api_err

        
        raw_text = response.text
        cleaned_text = clean_json_response(raw_text)

        try:
            parsed_data = json.loads(cleaned_text)
        except json.JSONDecodeError as json_err:
            print(f"[AI SERVICE ERROR] JSON parsing failed: {json_err}. Raw text was:\n{raw_text}")
            raise ValueError(f"Gemini returned invalid JSON structure. Details: {str(json_err)}")

        if "notes" not in parsed_data or "quiz" not in parsed_data or "mindmap_markdown" not in parsed_data:
            raise ValueError("Gemini response missing one or more required keys ('notes', 'quiz', 'mindmap_markdown').")

        return parsed_data

    except Exception as e:
        print(f"[AI SERVICE WARN] Model {model_name} error: {e}. Retrying with 'gemini-flash-latest'...")
        try:
            response = client.models.generate_content(
                model="gemini-flash-latest",
                contents=[system_prompt, user_content],
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    response_mime_type="application/json"
                )
            )
            cleaned_text = clean_json_response(response.text)
            return json.loads(cleaned_text)
        except Exception as fallback_err:
            raise RuntimeError(f"AI Service Error: {str(fallback_err)}")

def answer_student_question(pdf_text, question):
    """
    Answers a specific student question grounded in the uploaded PDF text.
    
    :param pdf_text: Extracted text from PDF
    :param question: User's question string
    :return: Direct, concise text answer string
    """
    client = get_gemini_client()
    model_name = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

    prompt = f"""You are a helpful AI academic assistant. Answer the student's question based strictly on the provided lecture material. Be direct, clear, and concise.

Lecture Material:
{pdf_text[:30000]}

Student Question:
{question}
"""

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3
            )
        )
        return response.text.strip()
    except Exception as e:
        try:
            response = client.models.generate_content(
                model="gemini-flash-latest",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3
                )
            )
            return response.text.strip()
        except Exception:
            raise RuntimeError(f"Failed to generate answer: {str(e)}")