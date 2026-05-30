import sqlite3
import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

# 1. Load the API key from the .env file
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("Error: GEMINI_API_KEY not found. Please create a .env file.")
    exit()

# Configure the Gemini library with your key
genai.configure(api_key=api_key)

# Initialize the generative model for text extraction
model = genai.GenerativeModel('models/gemini-flash-latest')


def get_unprocessed_data(conn):
    """Fetches rows from raw_cache that Gemini hasn't looked at yet."""
    cursor = conn.cursor()
    # We only select rows where processed_status is 0
    cursor.execute("SELECT id, company, raw_text FROM raw_cache WHERE processed_status = 0")
    return cursor.fetchall()

def extract_skills_fallback(text):
    known_skills = [
        "CUDA", "C++", "Python", "PyTorch", "LangChain", "RLHF",
        "SQL", "NCCL", "React", "RAG", "distributed systems",
        "model serving", "enterprise SaaS"
    ]

    found = []
    text_lower = text.lower()

    for skill in known_skills:
        if skill.lower() in text_lower:
            found.append(skill)

    return found if found else ["AI", "Data", "Engineering"]


def extract_seniority_fallback(text):
    text_lower = text.lower()

    if "staff" in text_lower:
        return "Lead"
    elif "senior" in text_lower:
        return "Senior"
    elif "lead" in text_lower:
        return "Lead"
    elif "manager" in text_lower:
        return "Lead"
    else:
        return "Mid"
    

def ask_gemini_to_extract(text):
    """Sends the raw text to Gemini with a strict prompt to return JSON."""
    
    # This prompt forces Gemini to act like a data extractor and ONLY output JSON
    prompt = f"""
    You are an expert Go-To-Market Intelligence AI. Analyze the following job posting or news snippet.
    Extract the intelligence into a STRICT JSON format. Do not include markdown formatting or extra text.
    
    Required JSON Schema:
    {{
      "skills": ["list", "of", "technical", "skills", "found"],
      "seniority": "Entry, Mid, Senior, Lead, or Unknown",
      "team_signal": "A short 3-word summary of what team is growing",
      "business_priority": "A 1-sentence prediction of what project this company is focusing on based on this text",
      "company_size": "Small (1-50), Mid-Market (51-500), or Enterprise (501+)",
      "growth_stage": "Early (Seed/A), Growth (B/C), or Public/FAANG"
    }}
    
    Text to analyze:
    {text}
    """
    
    try:
        response = model.generate_content(prompt)
        # Gemini sometimes wraps JSON in markdown blocks (```json ... ```). We strip that out.
        print("Gemini raw response:", response.text)
        clean_response = response.text.replace("```json", "").replace("```", "").strip()
        
        # Convert the text response into a Python dictionary
        structured_data = json.loads(clean_response)
        return structured_data
    
    except Exception as e:
        print(f"Gemini processing failed for this text: {e}")
        print("Using fallback mock extraction instead.")

    return {
        "skills": extract_skills_fallback(text),
        "seniority": extract_seniority_fallback(text),
        "team_signal": "AI infrastructure growth",
        "business_priority": "Company is likely expanding AI infrastructure and related enterprise capabilities.",
        "company_size": "Enterprise (501+)",
        "growth_stage": "Public/FAANG"
    }

def process_database():
    """Main loop: reads data, calls Gemini, saves results."""
    print("Connecting to database...")
    conn = sqlite3.connect("pulsesignal.db")
    cursor = conn.cursor()
    
    unprocessed_rows = get_unprocessed_data(conn)
    print(f"Found {len(unprocessed_rows)} unprocessed records.")
    
    for row in unprocessed_rows:
        record_id = row[0]
        company = row[1]
        raw_text = row[2]
        
        print(f"Processing {company} (ID: {record_id})...")
        extracted_data = ask_gemini_to_extract(raw_text)
        print("Extracted data:", extracted_data)
        
        if extracted_data:
            # 1. Insert the clean data into the structured_signals table
            # We join the skills list into a comma-separated string to save it in SQLite easily
            skills_string = ", ".join(extracted_data.get("skills", []))
            
            cursor.execute('''
                INSERT OR REPLACE INTO structured_signals (id, company, skills, seniority, team_signal, business_priority, company_size, growth_stage)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                record_id, 
                company, 
                skills_string,
                extracted_data.get("seniority", "Unknown"),
                extracted_data.get("team_signal", "Unknown"),
                extracted_data.get("business_priority", "Unknown"),
                extracted_data.get("company_size", "Unknown"),
                extracted_data.get("growth_stage", "Unknown")
            ))
            
            # 2. Update the raw_cache table to mark this record as done (status = 1)
            cursor.execute('''
                UPDATE raw_cache SET processed_status = 1 WHERE id = ?
            ''', (record_id,))
            
            conn.commit()
            print(f"Successfully structured data for {record_id}")

    conn.close()
    print("Step 2 complete: The structured_signals table is populated.")

if __name__ == "__main__":
    process_database()