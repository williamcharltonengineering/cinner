# add_stripe_customer_id.py
import os
import sqlite3

def migrate():
    """Add the stripe_customer_id column to the user table if it doesn't exist."""
    
    print("Running migration: add_stripe_customer_id")
    
    try:
        # Directly use the database path
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                             'instance', 'users.db')
        print(f"Using database at: {db_path}")
        
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the column already exists
        cursor.execute("PRAGMA table_info(user)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'stripe_customer_id' not in columns:
            # Add the stripe_customer_id column
            cursor.execute("ALTER TABLE user ADD COLUMN stripe_customer_id VARCHAR(120)")
            conn.commit()
            print("Added stripe_customer_id column to user table")
        else:
            print("stripe_customer_id column already exists")
        
        conn.close()
    except Exception as e:
        print(f"Error in migration: {e}")
        raise

if __name__ == "__main__":
    migrate()
