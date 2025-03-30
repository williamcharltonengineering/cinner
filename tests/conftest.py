"""
conftest.py - Pytest configuration file
"""
import os
import sys
import pytest
import stripe
from flask import Flask, request, jsonify, render_template_string, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user
from unittest.mock import MagicMock
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Create a test Flask app without importing the real app
@pytest.fixture(scope='session')
def app():
    """Session-wide test Flask application"""
    test_app = Flask(__name__)

    # Configure the app with test settings and env vars
    test_app.config.update({
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SECRET_KEY': os.getenv('SECRET_KEY', 'test_secret_key'),
        'STRIPE_API_KEY': os.getenv('STRIPE_API_KEY', 'sk_test_dummy'),
        'STRIPE_PUBLISHABLE_KEY': os.getenv('STRIPE_PUBLISHABLE_KEY', 'pk_test_dummy'),
    })

    # Create a test database
    db = SQLAlchemy(test_app)

    # Set up login manager
    login_manager = LoginManager(test_app)

    # Create User model
    class User(db.Model, UserMixin):
        __tablename__ = 'user'
        id = db.Column(db.Integer, primary_key=True)
        email = db.Column(db.String(120), unique=True, nullable=False)
        username = db.Column(db.String(80), unique=True, nullable=True)
        password = db.Column(db.String(120), nullable=False)
        is_admin = db.Column(db.Boolean, default=False)
        has_paid_plan = db.Column(db.Boolean, default=False)
        subscription_id = db.Column(db.String(120), nullable=True)
        stripe_customer_id = db.Column(db.String(120), nullable=True)
        time_data_file = db.Column(db.String(255), nullable=True)
        api_token = db.Column(db.String(64), unique=True, nullable=True)
        
        def set_password(self, password):
            """Set the password (no hashing in test)"""
            self.password = password

    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Mock route for registration
    @test_app.route('/register', methods=['GET', 'POST'])
    def register():
        """Register route that uses the actual Stripe API calls so they can be mocked in tests"""
        if request.method == 'GET':
            return render_template_string(
                '<form method="post"><h2>Register</h2>'
                '<input type="email" name="email" placeholder="Email">'
                '<input type="password" name="password" placeholder="Password">'
                '<input type="password" name="password2" placeholder="Confirm Password">'
                '<button type="submit">Register</button></form>'
            )
            
        email = request.form.get('email')
        password = request.form.get('password')
        username = request.form.get('username', email.split('@')[0])
        subscribe = request.form.get('subscribe') == 'on'

        # Create a new user
        user = User(
            email=email,
            username=username,
            password=password,
            is_admin=False,
            has_paid_plan=subscribe
        )

        # If subscribing with a stripe token
        if subscribe and 'stripeToken' in request.form:
            # This will be mocked in tests
            stripe_token = request.form['stripeToken']

            # These actual stripe API calls will be mocked in tests
            customer = stripe.Customer.create(
                email=email,
                source=stripe_token
            )

            subscription = stripe.Subscription.create(
                customer=customer.id,
                items=[{'price': 'price_1PPH0zBLvzmZ9ZyKpAcXdxAe'}]
            )

            # Update user with subscription info
            user.stripe_customer_id = customer.id
            user.subscription_id = subscription.id
            user.has_paid_plan = True

        db.session.add(user)
        db.session.commit()
        login_user(user)

        flash_message = 'Registration successful!'
        # We need to simulate the flash messages in tests
        return render_template_string(
            '<div class="flash-message">{{ message }}</div>',
            message=flash_message
        )
        
    # Mock login route
    @test_app.route('/login', methods=['GET', 'POST'])
    def login():
        """Login route for testing"""
        if request.method == 'GET':
            return render_template_string(
                '<form method="post"><h2>Login</h2>'
                '<input type="text" name="username" placeholder="Username">'
                '<input type="password" name="password" placeholder="Password">'
                '<button type="submit">Login</button></form>'
            )
        
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            login_user(user)
            return render_template_string(
                '<div class="success">Login successful</div>'
            )
        else:
            return render_template_string(
                '<div class="error">Invalid credentials</div>'
            )

    # Mock route for payment processing
    @test_app.route('/payment', methods=['GET', 'POST'])
    def payment():
        """Payment route that processes credit card information"""
        if request.method == 'GET':
            return render_template_string(
                '<form method="post"><h2>Payment</h2>'
                '<input type="text" name="card_number" placeholder="Card Number">'
                '<input type="text" name="card_exp_month" placeholder="Expiration Month">'
                '<input type="text" name="card_exp_year" placeholder="Expiration Year">'
                '<input type="text" name="card_cvc" placeholder="CVC">'
                '<input type="text" name="name" placeholder="Name">'
                '<input type="email" name="email" placeholder="Email">'
                '<button type="submit">Pay</button></form>'
            )
        
        # In a real app, this would create a payment method and attach it to the customer
        # For testing, we'll just mock this
        return render_template_string(
            '<div class="success">Payment successful</div>'
        )

    # Mock route for subscription cancellation
    @test_app.route('/account/cancel-subscription', methods=['POST'])
    def cancel_subscription():
        """Cancel subscription route that uses actual Stripe API calls for mocking"""
        # Get current user (this is a test so no login_required)
        user = User.query.get(current_user.id)

        if not user.subscription_id:
            message = 'No active subscription found'
        else:
            # These Stripe API calls will be mocked in tests
            subscription = stripe.Subscription.retrieve(user.subscription_id)
            stripe.Subscription.delete(user.subscription_id)

            # Update user in database
            user.subscription_id = None
            user.has_paid_plan = False
            db.session.commit()
            message = 'Your subscription has been successfully canceled'

        return render_template_string(
            '<div class="flash-message">{{ message }}</div>',
            message=message
        )

    # Mock route for account deletion
    @test_app.route('/account/delete', methods=['POST'])
    def delete_account():
        """Delete account route that can use Stripe API calls for mocking"""
        # Get current user (this is a test so no login_required)
        user_id = current_user.id

        # If user has a subscription cancel it first
        user = User.query.get(user_id)
        if user.subscription_id:
            try:
                stripe.Subscription.delete(user.subscription_id)
            except stripe.error.StripeError:
                message = 'Error canceling subscription'
                return render_template_string(
                    '<div class="flash-message">{{ message }}</div>',
                    message=message
                )

        # Log the user out
        logout_user()

        # Delete the user
        db.session.delete(user)
        db.session.commit()

        return render_template_string(
            '<div class="flash-message">{{ message }}</div>',
            message='Your account has been permanently deleted'
        )

    # Add helpers to app
    test_app.db = db
    test_app.User = User

    # Establish an application context
    with test_app.app_context():
        # Create all tables
        db.create_all()

        # Configure Stripe for testing
        stripe.api_key = test_app.config['STRIPE_API_KEY']

        yield test_app

        # Clean up
        db.session.remove()
        db.drop_all()

@pytest.fixture(scope='session')
def client(app):
    """Test client for the Flask application"""
    return app.test_client()

@pytest.fixture(scope='session')
def db_session(app):
    """Session-wide test database session"""
    db = app.db
    connection = db.engine.connect()
    transaction = connection.begin()

    session = db.session

    yield session

    session.remove()
    transaction.rollback()
    connection.close()

# Stripe test fixtures
@pytest.fixture(scope='session')
def stripe_test_cards():
    """Dictionary of Stripe test card tokens"""
    return {
        # Test cards that succeed
        'visa': 'tok_visa',
        'mastercard': 'tok_mastercard',
        'amex': 'tok_amex',

        # Test cards that fail for various reasons
        'declined': 'tok_chargeDeclined',
        'insufficient_funds': 'tok_chargeDeclinedInsufficientFunds',
        'expired_card': 'tok_chargeDeclinedExpiredCard',
        'incorrect_cvc': 'tok_chargeDeclinedIncorrectCvc',
        'processing_error': 'tok_chargeDeclinedProcessingError',
    }

@pytest.fixture(scope='function')
def test_price_id():
    """Stripe test price ID - replace with your test price ID if needed"""
    return 'price_1PPH0zBLvzmZ9ZyKpAcXdxAe'  # This is just a placeholder
