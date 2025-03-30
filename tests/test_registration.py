"""
Test the user registration flow including payment processing with Stripe test cards.
"""
import os
import pytest
import time
from flask import current_app, url_for
from unittest.mock import patch, MagicMock

# Import the app and required modules
import sys
import os

# Add the project root to the Python path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.app import app, db 
from app.config import TestConfig

@pytest.fixture
def client():
    """Set up a test client"""
    app.config.from_object(TestConfig)
    with app.test_client() as client:
        with app.app_context():
            db.create_all()  # Create tables for testing
            yield client
            db.drop_all()  # Clean up after test

def test_register_view(client):
    """Test that the registration page loads properly"""
    response = client.get('/register')
    assert response.status_code == 200
    assert b'Register' in response.data
    assert b'Email' in response.data
    assert b'Password' in response.data

def test_register_user_basic(client):
    """Test basic user registration without payment"""
    response = client.post('/register', data={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'password123',
        'password2': 'password123'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    # Check for successful registration indicators
    assert b'Login' in response.data or b'Profile' in response.data
    
    # Verify user was added to database
    with app.app_context():
        from app.models import User
        user = User.query.filter_by(username='testuser').first()
        assert user is not None
        assert user.email == 'test@example.com'

@pytest.mark.skipif(os.environ.get('STRIPE_API_KEY') is None, reason="Stripe API key not configured")
@patch('stripe.PaymentMethod.create')
@patch('stripe.PaymentIntent.create')
@patch('stripe.PaymentIntent.confirm')
@patch('stripe.Customer.create')
def test_register_with_payment(mock_customer_create, mock_intent_confirm, 
                              mock_intent_create, mock_pm_create, client):
    """Test complete registration flow with payment processing"""
    # Mock Stripe responses
    mock_customer = MagicMock()
    mock_customer.id = 'cus_test123'
    mock_customer_create.return_value = mock_customer
    
    mock_payment_method = MagicMock()
    mock_payment_method.id = 'pm_test123'
    mock_pm_create.return_value = mock_payment_method
    
    mock_intent = MagicMock()
    mock_intent.id = 'pi_test123'
    mock_intent.status = 'succeeded'
    mock_intent.next_action = None
    mock_intent_create.return_value = mock_intent
    mock_intent_confirm.return_value = mock_intent
    
    # Step 1: Register the user
    response = client.post('/register', data={
        'username': 'paiduser',
        'email': 'paid@example.com',
        'password': 'password123',
        'password2': 'password123'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    
    # Step 2: Submit payment information (using test card from Stripe)
    # This assumes your payment endpoint format
    response = client.post('/payment', data={
        'card_number': '4242424242424242',  # Stripe test card number
        'card_exp_month': '12',
        'card_exp_year': '2025',
        'card_cvc': '123',
        'name': 'Test User',
        'email': 'paid@example.com'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    
    # Verify the calls to Stripe were made correctly
    mock_pm_create.assert_called_once()
    mock_customer_create.assert_called_once()
    mock_intent_create.assert_called_once()
    
    # Verify user was properly updated with payment info
    with app.app_context():
        from app.models import User
        user = User.query.filter_by(username='paiduser').first()
        assert user is not None
        assert user.stripe_customer_id == 'cus_test123'
        assert user.has_paid_plan == True  # Check if the user has a paid plan
        assert user.subscription_id is not None  # Should have a subscription ID

@pytest.mark.skipif(os.environ.get('STRIPE_API_KEY') is None, reason="Stripe API key not configured")
def test_registration_cancel_account(client):
    """Test cancelling an account after registration"""
    # First register and set up mock data
    with app.app_context():
        from app.models import User
        # Create a test user directly in the database with mock Stripe data
        user = User(
            username='canceluser',
            email='cancel@example.com',
            stripe_customer_id='cus_mock123',
            subscription_id='sub_mock123',
            has_paid_plan=True
        )
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        user_id = user.id
    
    # Log in as the test user
    response = client.post('/login', data={
        'username': 'canceluser',
        'password': 'password123'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    
    # Mock the Stripe subscription cancellation
    with patch('stripe.Subscription.delete') as mock_subscription_delete:
        mock_subscription_delete.return_value = {'status': 'canceled'}
        
        # Cancel the account
        response = client.post('/account/cancel-subscription', follow_redirects=True)
        assert response.status_code == 200
        
        # Verify the user's subscription was canceled
        with app.app_context():
            user = User.query.get(user_id)
            assert user.has_paid_plan == False
            assert user.subscription_id is None

if __name__ == "__main__":
    pytest.main(["-v", "test_registration.py"])
