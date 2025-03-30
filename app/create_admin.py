"""
Standalone script to create an admin user in the database.
"""
import os
import sys
import sqlite3
import json
from pathlib import Path
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash
import redis

def create_admin_user():
    """
    Create an admin user directly in the database if one doesn't exist.
    Uses environment variables ADMIN_EMAIL and ADMIN_PASSWORD.
    Supports both SQLite and Redis backends.
    """
    load_dotenv()
    
    admin_email = os.getenv('ADMIN_EMAIL')
    admin_password = os.getenv('ADMIN_PASSWORD')
    
    if not admin_email or not admin_password:
        print("ADMIN_EMAIL and ADMIN_PASSWORD environment variables must be set")
        return False
        
    # Check if we should use Redis instead of filesystem
    use_redis = os.environ.get('PRESIS_NO_FSDB', '').lower() == 'true'
    
    if use_redis:
        return create_admin_user_redis(admin_email, admin_password)
    else:
        return create_admin_user_sqlite(admin_email, admin_password)

def create_admin_user_redis(admin_email, admin_password):
    """Create an admin user in Redis"""
    print("Using Redis for storage")
    
    # Configure Redis connection
    redis_host = os.environ.get('REDIS_HOST', 'localhost')
    redis_port = int(os.environ.get('REDIS_PORT', 6379))
    redis_db = int(os.environ.get('REDIS_DB', 0))
    redis_password = os.environ.get('REDIS_PASSWORD', None)
    
    try:
        # Connect to Redis
        r = redis.StrictRedis(
            host=redis_host, 
            port=redis_port, 
            db=redis_db, 
            password=redis_password,
            decode_responses=True
        )
        
        # Check if Redis is running by pinging it
        if not r.ping():
            print("Failed to connect to Redis")
            return False
            
        print(f"Connected to Redis at {redis_host}:{redis_port}")
        
        # Check if any admin user exists
        admin_exists = False
        
        # Get all user keys
        user_keys = r.keys("user:*")
        for user_key in user_keys:
            if not user_key.startswith("user:") or user_key.startswith("user_email:"):
                continue
                
            user_data = r.get(user_key)
            if user_data:
                user_data = json.loads(user_data)
                if user_data.get('is_admin'):
                    admin_exists = True
                    print(f"Admin user already exists: {user_data.get('email')}")
                    break
        
        if admin_exists:
            return True
            
        # Check if user with this email already exists
        user_id = r.get(f"user_email:{admin_email}")
        
        if user_id:
            # Make existing user an admin
            user_data = r.get(f"user:{user_id}")
            if user_data:
                user_data = json.loads(user_data)
                user_data['is_admin'] = True
                user_data['has_paid_plan'] = True
                r.set(f"user:{user_id}", json.dumps(user_data))
                print(f"Existing user {admin_email} promoted to admin")
                return True
        
        # Create a new admin user
        # First, get the next available user ID
        next_id = r.get("next_user_id")
        if not next_id:
            next_id = 1
            r.set("next_user_id", next_id)
        else:
            next_id = int(next_id)
        
        # Hash the password
        hashed_password = generate_password_hash(admin_password)
        
        # Create the user data
        user_data = {
            'id': next_id,
            'email': admin_email,
            'password': hashed_password,
            'is_admin': True,
            'has_paid_plan': True,
            'subscription_id': None,
            'stripe_customer_id': None,
            'api_token': None
        }
        
        # Save the user to Redis
        r.set(f"user:{next_id}", json.dumps(user_data))
        r.set(f"user_email:{admin_email}", next_id)
        
        # Increment the next user ID
        r.set("next_user_id", next_id + 1)
        
        print(f"Created new admin user in Redis: {admin_email}")
        return True
        
    except Exception as e:
        print(f"Error creating admin user in Redis: {str(e)}")
        return False

def create_admin_user_sqlite(admin_email, admin_password):
    """Create an admin user in SQLite"""
    print("Using SQLite for storage")
    
    # Define the path to the SQLite database
    app_root = os.environ.get('APP_ROOT_DIR', os.getcwd())
    db_path = os.path.join(app_root, 'instance', 'users.db')
    
    # Ensure the instance directory exists
    Path(os.path.dirname(db_path)).mkdir(parents=True, exist_ok=True)
    
    print(f"Checking for admin user in database at {db_path}")
    
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create the user table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                is_admin BOOLEAN DEFAULT 0,
                has_paid_plan BOOLEAN DEFAULT 0,
                subscription_id TEXT,
                stripe_customer_id TEXT,
                time_data_file TEXT,
                api_token TEXT UNIQUE
            )
        ''')
        
        # Check if the is_admin column exists
        try:
            # Try to query with the is_admin column
            cursor.execute("SELECT email FROM user WHERE is_admin = 1")
        except sqlite3.OperationalError as e:
            if "no such column: is_admin" in str(e):
                print("Adding is_admin column to user table...")
                cursor.execute("ALTER TABLE user ADD COLUMN is_admin BOOLEAN DEFAULT 0")
                conn.commit()
            else:
                raise
        
        # Check if any admin user exists
        cursor.execute("SELECT email FROM user WHERE is_admin = 1")
        admin = cursor.fetchone()
        
        if admin:
            print(f"Admin user already exists: {admin[0]}")
            conn.close()
            return True
        
        # Check if a user with this email already exists
        cursor.execute("SELECT id FROM user WHERE email = ?", (admin_email,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            # Make the existing user an admin
            cursor.execute(
                "UPDATE user SET is_admin = 1 WHERE email = ?", 
                (admin_email,)
            )
            conn.commit()
            print(f"Existing user {admin_email} promoted to admin")
            conn.close()
            return True
        
        # Create a new admin user
        cursor.execute(
            "INSERT INTO user (email, password, is_admin, has_paid_plan) VALUES (?, ?, 1, 1)", 
            (admin_email, admin_password)
        )
        conn.commit()
        print(f"Created new admin user: {admin_email}")
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error creating admin user in SQLite: {str(e)}")
        return False

if __name__ == "__main__":
    try:
        success = create_admin_user()
        if success:
            print("Admin user setup completed successfully")
            sys.exit(0)
        else:
            print("Failed to set up admin user")
            sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        sys.exit(1)
