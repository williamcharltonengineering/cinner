import json
import secrets
from werkzeug.security import generate_password_hash, check_password_hash
from presis.redis_backend import RedisBackend
from presis.redis_time_tracker import RedisTimeTracker

class RedisUser:
    """
    Redis-based implementation of the User model
    This class mimics the SQLAlchemy User model interface but stores data in Redis
    """
    
    def __init__(self, redis_backend, user_data=None):
        self.redis = redis_backend
        # Default values
        self.id = None
        self.email = None
        self.password = None
        self.is_admin = False
        self.has_paid_plan = False
        self.subscription_id = None
        self.stripe_customer_id = None
        self.api_token = None
        
        # If user_data is provided, populate the attributes
        if user_data:
            self.id = user_data.get('id')
            self.email = user_data.get('email')
            self.password = user_data.get('password')
            self.is_admin = user_data.get('is_admin', False)
            self.has_paid_plan = user_data.get('has_paid_plan', False)
            self.subscription_id = user_data.get('subscription_id')
            self.stripe_customer_id = user_data.get('stripe_customer_id')
            self.api_token = user_data.get('api_token')
    
    def is_authenticated(self):
        """Required by Flask-Login"""
        return True
        
    def is_active(self):
        """Required by Flask-Login"""
        return True
        
    def is_anonymous(self):
        """Required by Flask-Login"""
        return False
        
    def get_id(self):
        """Required by Flask-Login"""
        return str(self.id)
    
    def save(self):
        """Save the user data to Redis"""
        user_data = {
            'id': self.id,
            'email': self.email,
            'password': self.password,
            'is_admin': self.is_admin,
            'has_paid_plan': self.has_paid_plan,
            'subscription_id': self.subscription_id,
            'stripe_customer_id': self.stripe_customer_id,
            'api_token': self.api_token
        }
        self.redis.r.set(f"user:{self.id}", json.dumps(user_data))
        self.redis.r.set(f"user_email:{self.email}", self.id)
        
    def generate_api_token(self):
        """Generate a new API token for the user"""
        self.api_token = secrets.token_hex(32)
        self.save()
        return self.api_token
    
    def get_time_tracker(self):
        """Get a RedisTimeTracker instance for this user"""
        return RedisTimeTracker(self.id, self.redis)

class RedisUserRepository:
    """
    Repository for managing Redis-based User objects
    This class mimics the SQLAlchemy query interface for User model
    """
    
    def __init__(self, redis_backend):
        self.redis = redis_backend
        self.next_id = self._get_next_id()
    
    def _get_next_id(self):
        """Get the next available user ID"""
        next_id = self.redis.r.get("next_user_id")
        if not next_id:
            next_id = 1
            self.redis.r.set("next_user_id", next_id)
        return int(next_id)
    
    def _increment_next_id(self):
        """Increment the next available user ID"""
        next_id = self._get_next_id()
        self.redis.r.set("next_user_id", next_id + 1)
        return next_id
    
    def create(self, email, password, is_admin=False, has_paid_plan=False,
              subscription_id=None, stripe_customer_id=None, api_token=None):
        """Create a new user and save to Redis"""
        # Check if email is already used
        if self.redis.r.get(f"user_email:{email}"):
            raise ValueError(f"Email {email} is already in use")
            
        # Create user with next available ID
        user_id = self._increment_next_id()
        
        # Hash the password
        hashed_password = generate_password_hash(password)
        
        user = RedisUser(self.redis, {
            'id': user_id,
            'email': email,
            'password': hashed_password,
            'is_admin': is_admin,
            'has_paid_plan': has_paid_plan,
            'subscription_id': subscription_id,
            'stripe_customer_id': stripe_customer_id,
            'api_token': api_token
        })
        
        # Save the user to Redis
        user.save()
        return user
    
    def get(self, user_id):
        """Get a user by ID"""
        if user_id is None:
            return None
            
        user_data = self.redis.r.get(f"user:{user_id}")
        if not user_data:
            return None
            
        return RedisUser(self.redis, json.loads(user_data))
    
    def filter_by(self, **kwargs):
        """Filter users by criteria (simplified implementation)"""
        # Only support filtering by email or api_token
        if 'email' in kwargs:
            user_id = self.redis.r.get(f"user_email:{kwargs['email']}")
            if not user_id:
                return EmptyResult()
            return SingleResult(self.get(user_id))
        elif 'api_token' in kwargs:
            # Find the user with the given API token
            # This is inefficient, but API tokens are used less frequently
            all_user_ids = self.redis.r.keys("user:*")
            for user_key in all_user_ids:
                if not user_key.startswith("user:") or user_key == "user_email:":
                    continue
                user_id = user_key.split(":")[1]
                user = self.get(user_id)
                if user and user.api_token == kwargs['api_token']:
                    return SingleResult(user)
            return EmptyResult()
        return EmptyResult()
    
    def all(self):
        """Get all users"""
        all_user_ids = self.redis.r.keys("user:*")
        users = []
        for user_key in all_user_ids:
            if not user_key.startswith("user:") or user_key.startswith("user_email:"):
                continue
            user_id = user_key.split(":")[1]
            user = self.get(user_id)
            if user:
                users.append(user)
        return users

class EmptyResult:
    """Empty result from a query"""
    def first(self):
        return None
        
    def all(self):
        return []

class SingleResult:
    """Single result from a query"""
    def __init__(self, user):
        self.user = user
        
    def first(self):
        return self.user
        
    def all(self):
        return [self.user] if self.user else []
