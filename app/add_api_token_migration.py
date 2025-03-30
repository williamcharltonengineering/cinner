import os
import sqlite3
from app import app

def add_api_token_column():
    """Add the api_token column to the user table if it doesn't exist"""
    # Path to the database file
    db_path = os.path.join(app.instance_path, 'users.db')
    
    if os.path.exists(db_path):
        print(f"Updating database schema at {db_path}")
        
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if api_token column already exists
        cursor.execute("PRAGMA table_info(user)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'api_token' not in columns:
            print("Adding api_token column to user table...")
            # SQLite doesn't support adding UNIQUE constraint in ALTER TABLE
            cursor.execute("ALTER TABLE user ADD COLUMN api_token VARCHAR(64)")
            conn.commit()
            print("api_token column added successfully!")
        else:
            print("api_token column already exists, no changes needed.")
        
        conn.close()
    else:
        print(f"Database file {db_path} does not exist!")

if __name__ == "__main__":
    try:
        add_api_token_column()
        print("Migration completed successfully!")
    except Exception as e:
        print(f"Error during migration: {e}")
