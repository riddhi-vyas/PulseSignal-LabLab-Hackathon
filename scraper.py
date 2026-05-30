import os
import sqlite3
import requests
import uuid
import time
from dotenv import load_dotenv
from urllib.parse import urlencode

load_dotenv()

API_KEY = os.getenv("BRIGHTDATA_API_KEY")
ZONE = os.getenv("BRIGHTDATA_ZONE", "pulsesignal_serp")

TARGET_COMPANIES = [
    "NVIDIA", "Meta", "Google", "Microsoft", "Amazon", # AI Giants
    "OpenAI", "Anthropic", "Databricks", "Snowflake", "Mistral AI", "Cohere", "Perplexity", # AI Disruptors
    "Wafer", "Manufact", "Ineffable Intelligence" # Early Stage (Seed/A)
]

def fetch_live_signals(company):
    query = f"{company} careers AI machine learning infrastructure jobs"
    params = urlencode({"q": query})
    url = f"https://www.google.com/search?{params}"

    payload = {
        "zone": ZONE,
        "url": url,
        "format": "json"
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    response = requests.post(
        "https://api.brightdata.com/request",
        headers=headers,
        json=payload,
        timeout=30
    )
    print("Status:", response.status_code)
    print("Response:", response.text[:1000])

    response.raise_for_status()
    return response.text

def save_to_cache(company, raw_text, source_url):
    conn = sqlite3.connect("pulsesignal.db")
    cursor = conn.cursor()

    record_id = f"live_{uuid.uuid4().hex[:8]}"

    cursor.execute("""
        INSERT INTO raw_cache (id, company, source_url, raw_text, processed_status)
        VALUES (?, ?, ?, ?, 0)
    """, (record_id, company, source_url, raw_text))

    conn.commit()
    conn.close()

def main():
    print("Starting Bright Data live ingestion...")

    for company in TARGET_COMPANIES:
        print(f"Fetching {company}...")
        raw_result = fetch_live_signals(company)

        save_to_cache(
            company,
            raw_result[:3000],
            f"https://www.google.com/search?q={company}+careers+AI+jobs"
        )

        print(f"Saved {company} result to raw_cache.")
        time.sleep(2)

    print("Step 3 complete. Now run: python extract_signals.py")

print("Bright Data key loaded:", bool(API_KEY))
print("Zone:", ZONE)

if __name__ == "__main__":
    main()