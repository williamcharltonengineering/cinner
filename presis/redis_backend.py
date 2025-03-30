import redis
import uuid
import json
from datetime import timedelta
from werkzeug.security import generate_password_hash, check_password_hash

class RedisBackend:
    def __init__(self, host="localhost", port=6379, db=0, password=None):
        self.r = redis.StrictRedis(host=host, port=port, db=db, password=password, decode_responses=True)

    def create_user(self, username, password):
        """Create a new user with a unique ID and store a hashed password."""
        user_id = str(uuid.uuid4())
        hashed_password = generate_password_hash(password)
        self.r.hset(f"user:{username}", "user_id", user_id)
        self.r.hset(f"user:{username}", "password", hashed_password)
        return user_id

    def authenticate_user(self, username, password):
        """Check if the provided username and password match."""
        stored_password = self.r.hget(f"user:{username}", "password")
        return check_password_hash(stored_password, password)

    def get_user_id(self, username):
        """Retrieve the user ID for a given username."""
        return self.r.hget(f"user:{username}", "user_id")

    def create_scoped_token(self, username, project, scope="readonly"):
        """Generate a read-only token for sharing timesheets."""
        token = str(uuid.uuid4())
        self.r.set(f"token:{token}", json.dumps({"username": username, "project": project, "scope": scope}), ex=timedelta(days=7))
        return token

    def verify_token(self, token):
        """Verify if the token is valid and return its details."""
        data = self.r.get(f"token:{token}")
        return json.loads(data) if data else None

    def save_timesheet(self, username, project_name, data):
        """Store a timesheet in Redis."""
        key = f"timesheet:{username}:{project_name}"
        self.r.set(key, json.dumps(data))

    def load_timesheet(self, username, project_name):
        """Load a timesheet from Redis."""
        key = f"timesheet:{username}:{project_name}"
        data = self.r.get(key)
        return json.loads(data) if data else None
