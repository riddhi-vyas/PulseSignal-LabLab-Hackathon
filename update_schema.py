import sqlite3

def update_schema():
    print("Updating database schema...")
    conn = sqlite3.connect("pulsesignal.db")
    cursor = conn.cursor()
    
    try:
        # Add company_size column
        cursor.execute("ALTER TABLE structured_signals ADD COLUMN company_size TEXT")
        print("Added company_size column.")
    except sqlite3.OperationalError:
        print("company_size column already exists.")

    try:
        # Add growth_stage column
        cursor.execute("ALTER TABLE structured_signals ADD COLUMN growth_stage TEXT")
        print("Added growth_stage column.")
    except sqlite3.OperationalError:
        print("growth_stage column already exists.")
    
    conn.commit()
    conn.close()
    print("Schema update complete.")

if __name__ == "__main__":
    update_schema()
