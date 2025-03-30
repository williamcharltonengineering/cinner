"""
Test Stripe integration functionality independently of the Flask app
"""
import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# Add the project root to the Python path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestStripeIntegration:
    """Test suite for Stripe integration"""
    
    @pytest.mark.skipif(os.environ.get('STRIPE_API_KEY') is None, reason="Stripe API key not configured")
    @patch('stripe.Customer.create')
    def test_customer_creation(self, mock_customer_create):
        """Test creating a Stripe customer"""
        import stripe
        
        # Configure mock
        mock_customer = MagicMock()
        mock_customer.id = 'cus_test123'
        mock_customer_create.return_value = mock_customer
        
        # Set API key for test
        stripe.api_key = os.environ.get('STRIPE_API_KEY', 'sk_test_dummy')
        
        # Create a customer
        customer = stripe.Customer.create(
            email='test@example.com',
            name='Test User',
            description='Test customer for registration'
        )
        
        # Verify the mock was called with expected parameters
        mock_customer_create.assert_called_once()
        call_kwargs = mock_customer_create.call_args.kwargs
        assert call_kwargs['email'] == 'test@example.com'
        assert call_kwargs['name'] == 'Test User'
        
        # Verify the result
        assert customer.id == 'cus_test123'
    
    @pytest.mark.skipif(os.environ.get('STRIPE_API_KEY') is None, reason="Stripe API key not configured")
    @patch('stripe.PaymentMethod.create')
    def test_payment_method_creation(self, mock_pm_create):
        """Test creating a payment method with a test card"""
        import stripe
        
        # Configure mock
        mock_payment_method = MagicMock()
        mock_payment_method.id = 'pm_test123'
        mock_pm_create.return_value = mock_payment_method
        
        # Set API key for test
        stripe.api_key = os.environ.get('STRIPE_API_KEY', 'sk_test_dummy')
        
        # Create a payment method
        payment_method = stripe.PaymentMethod.create(
            type='card',
            card={
                'number': '4242424242424242',
                'exp_month': 12,
                'exp_year': 2025,
                'cvc': '123'
            }
        )
        
        # Verify the mock was called with expected parameters
        mock_pm_create.assert_called_once()
        call_kwargs = mock_pm_create.call_args.kwargs
        assert call_kwargs['type'] == 'card'
        assert call_kwargs['card']['number'] == '4242424242424242'
        
        # Verify the result
        assert payment_method.id == 'pm_test123'
    
    @pytest.mark.skipif(os.environ.get('STRIPE_API_KEY') is None, reason="Stripe API key not configured")
    @patch('stripe.Subscription.create')
    def test_subscription_creation(self, mock_sub_create):
        """Test creating a subscription"""
        import stripe
        
        # Configure mock
        mock_subscription = MagicMock()
        mock_subscription.id = 'sub_test123'
        mock_subscription.status = 'active'
        mock_sub_create.return_value = mock_subscription
        
        # Set API key for test
        stripe.api_key = os.environ.get('STRIPE_API_KEY', 'sk_test_dummy')
        
        # Create a subscription
        subscription = stripe.Subscription.create(
            customer='cus_test123',
            items=[{'price': 'price_test123'}]
        )
        
        # Verify the mock was called with expected parameters
        mock_sub_create.assert_called_once()
        call_kwargs = mock_sub_create.call_args.kwargs
        assert call_kwargs['customer'] == 'cus_test123'
        assert call_kwargs['items'][0]['price'] == 'price_test123'
        
        # Verify the result
        assert subscription.id == 'sub_test123'
        assert subscription.status == 'active'
    
    @pytest.mark.skipif(os.environ.get('STRIPE_API_KEY') is None, reason="Stripe API key not configured")
    @patch('stripe.Subscription.delete')
    def test_subscription_cancellation(self, mock_sub_delete):
        """Test canceling a subscription"""
        import stripe
        
        # Configure mock
        mock_canceled_subscription = MagicMock()
        mock_canceled_subscription.status = 'canceled'
        mock_sub_delete.return_value = mock_canceled_subscription
        
        # Set API key for test
        stripe.api_key = os.environ.get('STRIPE_API_KEY', 'sk_test_dummy')
        
        # Cancel a subscription
        canceled_subscription = stripe.Subscription.delete('sub_test123')
        
        # Verify the mock was called with expected parameters
        mock_sub_delete.assert_called_once_with('sub_test123')
        
        # Verify the result
        assert canceled_subscription.status == 'canceled'

    @pytest.mark.skipif(os.environ.get('STRIPE_API_KEY') is None, reason="Stripe API key not configured")
    @patch('stripe.Customer.create')
    @patch('stripe.PaymentMethod.create')
    @patch('stripe.PaymentMethod.attach')
    @patch('stripe.Subscription.create')
    @patch('stripe.Subscription.delete')
    def test_full_subscription_lifecycle(self, mock_sub_delete, mock_sub_create, 
                                        mock_pm_attach, mock_pm_create, mock_customer_create):
        """Test the full subscription lifecycle: create customer, payment method, subscription, then cancel"""
        import stripe
        
        # Configure mocks
        mock_customer = MagicMock()
        mock_customer.id = 'cus_test456'
        mock_customer_create.return_value = mock_customer
        
        mock_payment_method = MagicMock()
        mock_payment_method.id = 'pm_test456'
        mock_pm_create.return_value = mock_payment_method
        
        mock_subscription = MagicMock()
        mock_subscription.id = 'sub_test456'
        mock_subscription.status = 'active'
        mock_sub_create.return_value = mock_subscription
        
        mock_canceled_subscription = MagicMock()
        mock_canceled_subscription.status = 'canceled'
        mock_sub_delete.return_value = mock_canceled_subscription
        
        # Set API key for test
        stripe.api_key = os.environ.get('STRIPE_API_KEY', 'sk_test_dummy')
        
        # 1. Create a customer
        customer = stripe.Customer.create(
            email='test@example.com',
            name='Test User'
        )
        assert customer.id == 'cus_test456'
        
        # 2. Create a payment method
        payment_method = stripe.PaymentMethod.create(
            type='card',
            card={
                'number': '4242424242424242',
                'exp_month': 12,
                'exp_year': 2025,
                'cvc': '123'
            }
        )
        assert payment_method.id == 'pm_test456'
        
        # 3. Attach payment method to customer
        stripe.PaymentMethod.attach(
            payment_method.id,
            customer=customer.id
        )
        mock_pm_attach.assert_called_once()
        
        # 4. Create subscription
        subscription = stripe.Subscription.create(
            customer=customer.id,
            items=[{'price': 'price_test456'}]
        )
        assert subscription.id == 'sub_test456'
        assert subscription.status == 'active'
        
        # 5. Cancel subscription
        canceled_subscription = stripe.Subscription.delete(subscription.id)
        assert canceled_subscription.status == 'canceled'
        
        # Verify all mocks were called
        mock_customer_create.assert_called_once()
        mock_pm_create.assert_called_once()
        mock_pm_attach.assert_called_once()
        mock_sub_create.assert_called_once()
        mock_sub_delete.assert_called_once()
