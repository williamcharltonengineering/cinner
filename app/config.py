# config.py
from dotenv import load_dotenv
import os

load_dotenv()

def str_to_bool(value):
    if isinstance(value, str):
        return value.lower() in ('true', '1', 't', 'y', 'yes')
    return bool(value)

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_SERVER = os.getenv('MAIL_SERVER')
    MAIL_PORT = int(os.getenv('MAIL_PORT', '587'))
    MAIL_USE_TLS = str_to_bool(os.getenv('MAIL_USE_TLS', 'True'))
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')
    STRIPE_API_KEY = os.getenv('STRIPE_API_KEY')
    STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')

class TestConfig(Config):
    """Configuration for test environment"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///instance/test/test.db'
    WTF_CSRF_ENABLED = False
    SECRET_KEY = 'test_secret_key'
    STRIPE_API_KEY = "sk_test_51PPG9tBLvzmZ9ZyKG6q9dK9WQ7LG3fEF44OXckIWdlUg8O4oHMjFGJQ42WbXbTBIVlKoIUBciBP5xTZy09AJXON9001hnkOWO6"
    STRIPE_PUBLISHABLE_KEY = "pk_test_51PPG9tBLvzmZ9ZyKFQz9JAngfqAuXQdAWYmufL2yeKu3oV239qbhUzYDbwBOBcUiWsh3qXMsl2mshJ3PwFfKSjtr00DBatgbdO"
    SERVER_NAME = 'localhost'
