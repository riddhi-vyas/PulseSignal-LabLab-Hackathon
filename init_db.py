import sqlite3
import json
import os

# 1. Define the database file name. This will be created in your folder.
DB_NAME = "pulsesignal.db"

def initialize_database():
    """This function creates the database file and sets up our two tables."""
    print("Connecting to database...")
    
    # Connect to the file. If it doesn't exist, Python creates it.
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Create the table for our messy, raw data (from JSON or Scraper)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS raw_cache (
            id TEXT PRIMARY KEY,
            company TEXT,
            source_url TEXT,
            raw_text TEXT,
            processed_status INTEGER DEFAULT 0  -- 0 means Gemini hasn't looked at it yet, 1 means done
        )
    ''')

    # Create the table for our clean, AI-extracted data (Streamlit will read from here)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS structured_signals (
            id TEXT PRIMARY KEY,
            company TEXT,
            skills TEXT,               
            seniority TEXT,
            team_signal TEXT,
            business_priority TEXT,
            FOREIGN KEY(id) REFERENCES raw_cache(id)
        )
    ''')

    # Save the changes to the file
    conn.commit()
    print("Tables created successfully.")
    return conn

def load_fake_data(conn):
    """This function reads the JSON file and puts it into the raw_cache table."""
    print("Loading data from sample_data.json...")
    
    # Safety check: make sure the JSON file exists
    if not os.path.exists("sample_data.json"):
        print("Error: Cannot find sample_data.json. Please ensure it is in the same directory.")
        return

    # Open and read the JSON file
    with open("sample_data.json", "r") as f:
        data = json.load(f)

    cursor = conn.cursor()
    inserted_count = 0

    # Loop through each job in the JSON and add it to the table
    for item in data:
        try:
            # INSERT OR IGNORE means if we run this script twice, it won't crash from duplicates
            cursor.execute('''
                INSERT OR IGNORE INTO raw_cache (id, company, source_url, raw_text)
                VALUES (?, ?, ?, ?)
            ''', (item["id"], item["company"], item["source_url"], item["raw_text"]))
            
            # Count how many new items were actually added
            if cursor.rowcount > 0:
                inserted_count += 1
        except Exception as e:
            print(f"Error inserting {item['id']}: {e}")

    # Save the new rows
    conn.commit()
    print(f"Successfully loaded {inserted_count} new records into the database.")

# This is the starting block of the script
if __name__ == "__main__":
    # 1. Create the DB and tables
    db_connection = initialize_database()
    # 2. Fill the raw_cache table
    load_fake_data(db_connection)
    # 3. Close the connection
    db_connection.close()
    
    print("Step 1 complete: Database initialized.")