# stripe_webhook.py
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import stripe
import os
from app import User, db
load_dotenv()

app = Flask(__name__)
# stripe.api_key = os.getenv('STRIPE_API_KEY')

@app.route('/webhook', methods=['POST'])
def webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, os.getenv('STRIPE_WEBHOOK_SECRET')
        )
    except ValueError as e:
        # Invalid payload
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return 'Invalid signature', 400

    # Handle the event
    if event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        # Find user and deactivate their subscription in the database
        user = User.query.filter_by(subscription_id=subscription['id']).first()
        if user:
            user.subscription_id = None
            db.session.commit()

    return jsonify({'status': 'success'})

if __name__ == '__main__':
    app.run(port=5001, debug=True)
