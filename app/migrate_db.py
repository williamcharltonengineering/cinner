import os
import sys
import sqlite3
import stat
from app import app, db, User

def ensure_directory_permissions(directory):
    """Ensure the directory has the correct permissions"""
    try:
        # Make sure the directory exists
        os.makedirs(directory, exist_ok=True)
        
        # Set permissions to 755 (rwxr-xr-x)
        os.chmod(directory, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
        print(f"Set permissions for directory: {directory}")
    except Exception as e:
        print(f"Warning: Could not set permissions for directory {directory}: {e}")

def create_fresh_database():
    """Create a fresh database with the new schema"""
    try:
        with app.app_context():
            db.drop_all()  # Drop all tables if they exist
            db.create_all()  # Create tables with the new schema
            print("Created fresh database with new schema!")
            return True
    except Exception as e:
        print(f"Error creating fresh database: {e}")
        return False

def migrate_database():
    """
    Migrate the database to add new columns to the User model.
    This is a simple migration script for development purposes.
    """
    # Path to the database file
    db_path = os.path.join(app.instance_path, 'users.db')
    
    if os.path.exists(db_path):
        print(f"Backing up existing database to {db_path}.bak")
        # Create a backup of the existing database
        if os.path.exists(f"{db_path}.bak"):
            os.remove(f"{db_path}.bak")
        os.rename(db_path, f"{db_path}.bak")
        
        # Connect to the backup database
        conn_old = sqlite3.connect(f"{db_path}.bak")
        cursor_old = conn_old.cursor()
        
        # Check the schema of the existing database
        cursor_old.execute("PRAGMA table_info(user)")
        columns = {column[1]: column[0] for column in cursor_old.fetchall()}
        print(f"Found columns in existing database: {', '.join(columns.keys())}")
        
        # Build a query based on available columns
        select_columns = ["id", "email", "password"]
        if "is_owner" in columns:
            select_columns.append("is_owner")
        else:
            print("Warning: is_owner column not found, defaulting to 0")
        
        if "subscription_id" in columns:
            select_columns.append("subscription_id")
        else:
            print("Warning: subscription_id column not found, defaulting to NULL")
            
        if "time_data_file" in columns:
            select_columns.append("time_data_file")
        else:
            print("Warning: time_data_file column not found, defaulting to NULL")
        
        # Get existing users
        query = f"SELECT {', '.join(select_columns)} FROM user"
        print(f"Executing query: {query}")
        cursor_old.execute(query)
        users_data = cursor_old.fetchall()
        
        # Create new database with updated schema
        with app.app_context():
            db.create_all()
        
        # Connect to the new database
        conn_new = sqlite3.connect(db_path)
        cursor_new = conn_new.cursor()
        
        # Migrate users to the new schema
        for user_data in users_data:
            # Create a dictionary with default values
            user_dict = {
                "id": user_data[0],
                "email": user_data[1],
                "password": user_data[2],
                "is_owner": 0,
                "subscription_id": None,
                "time_data_file": None
            }
            
            # Update with actual values from the database
            col_index = 3
            if "is_owner" in columns and col_index < len(user_data):
                user_dict["is_owner"] = user_data[col_index]
                col_index += 1
                
            if "subscription_id" in columns and col_index < len(user_data):
                user_dict["subscription_id"] = user_data[col_index]
                col_index += 1
                
            if "time_data_file" in columns and col_index < len(user_data):
                user_dict["time_data_file"] = user_data[col_index]
            
            # Convert is_owner to is_admin (they're conceptually similar)
            is_admin = 1 if user_dict["is_owner"] == 1 else 0
            has_paid_plan = 1 if user_dict["subscription_id"] is not None else 0
            
            # Insert into new database
            cursor_new.execute(
                "INSERT INTO user (id, email, password, is_admin, has_paid_plan, subscription_id, time_data_file, api_token) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (user_dict["id"], user_dict["email"], user_dict["password"], is_admin, has_paid_plan, 
                 user_dict["subscription_id"], user_dict["time_data_file"], None)
            )
        
        # Commit changes and close connections
        conn_new.commit()
        conn_old.close()
        conn_new.close()
        
        print("Database migration completed successfully!")
    else:
        # Database doesn't exist yet, just create it
        with app.app_context():
            db.create_all()
            print("Database created with new schema!")

def create_admin_user():
    """Create an admin user if no users exist"""
    with app.app_context():
        if User.query.count() == 0:
            admin = User(
                email='admin@example.com',
                password='adminpassword',
                is_admin=True,
                has_paid_plan=True
            )
            db.session.add(admin)
            db.session.commit()
            print("Admin user created successfully!")
        else:
            print("Users already exist, skipping admin creation")

if __name__ == "__main__":
    # Ensure the instance directory has the correct permissions
    ensure_directory_permissions(app.instance_path)
    
    # Ensure the time_data directory has the correct permissions
    time_data_dir = os.path.join(app.instance_path, 'time_data')
    ensure_directory_permissions(time_data_dir)
    
    try:
        # Try to migrate the database
        migrate_database()
        create_admin_user()
    except Exception as e:
        print(f"Error during migration: {e}")
        print("Attempting to create a fresh database instead...")
        
        # If migration fails, try to create a fresh database
        if create_fresh_database():
            try:
                create_admin_user()
                print("Successfully created a fresh database with an admin user.")
                print("Note: Any existing data has been lost.")
            except Exception as e:
                print(f"Error creating admin user: {e}")
                print("You may need to manually create an admin user.")
        else:
            print("Failed to create a fresh database.")
            print("Please check file permissions and try again.")
            sys.exit(1)
