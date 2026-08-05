"""
One-time migration: adds the 'videos' column to the complaints table.
Run this ONCE from the same folder as your complaints.db:
    python migrate_add_videos.py
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "complaints.db")

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check if column already exists (safe to run multiple times)
    cursor.execute("PRAGMA table_info(complaints)")
    columns = [row[1] for row in cursor.fetchall()]

    if "videos" in columns:
        print("✅ 'videos' column already exists — nothing to do.")
    else:
        cursor.execute("ALTER TABLE complaints ADD COLUMN videos TEXT DEFAULT '[]'")
        conn.commit()
        print("✅ 'videos' column added successfully.")

    conn.close()

if __name__ == "__main__":
    migrate()
