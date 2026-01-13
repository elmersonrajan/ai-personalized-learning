import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load .env file
load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    raise ValueError("❌ GOOGLE_API_KEY not found. Check your .env file.")

genai.configure(api_key=API_KEY)

model = genai.GenerativeModel("gemini-2.5-flash")

def ask_tutor(question, topic="fractions"):
    prompt = f"""
You are a friendly AI tutor helping a student learn {topic}.
Explain concepts simply, step-by-step, with examples.
Guide the student instead of directly giving final answers.

Student question: {question}
"""
    response = model.generate_content(prompt)
    return response.text
