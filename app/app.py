import os
import json
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, request, flash, session, send_from_directory, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import stripe
import uuid
import logging
from presis.time_tracker import TimeTracker

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)

app = Flask(__name__)
app.config.from_object('config.Config')

db = SQLAlchemy(app)
mail = Mail(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

stripe.api_key = app.config['STRIPE_API_KEY']

# Add context processor for current year
@app.context_processor
def inject_now():
    return {'now': datetime.now()}

# User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    has_paid_plan = db.Column(db.Boolean, default=False)
    subscription_id = db.Column(db.String(120), nullable=True)
    time_data_file = db.Column(db.String(255), nullable=True)
    
    def get_time_tracker(self):
        """Get or create a TimeTracker instance for this user"""
        if not self.time_data_file:
            # Create a data file for the user
            data_dir = os.path.join(app.instance_path, 'time_data')
            if not os.path.exists(data_dir):
                os.makedirs(data_dir)
            
            self.time_data_file = os.path.join(data_dir, f'user_{self.id}_time_data.json')
            
            # Initialize the file if it doesn't exist
            if not os.path.exists(self.time_data_file):
                with open(self.time_data_file, 'w') as f:
                    json.dump({"projects": []}, f)
            
            db.session.commit()
            
        return TimeTracker(self.time_data_file)

# Invitation model
class Invitation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    inviter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    token = db.Column(db.String(120), unique=True, nullable=False)

# Create database tables within an application context
with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, 'static/images'),
        'favicon.ico',
        mimetype='image/vnd.microsoft.icon'
    )

@app.route('/')
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    
    # Get the user's time tracker and projects
    time_tracker = current_user.get_time_tracker()
    projects = time_tracker.projects
    
    # Get active project (if any)
    active_project = None
    for project in projects:
        if project['sessions'] and project['sessions'][-1]['end'] is None:
            active_project = project['project_name']
            break
    
    return render_template('index.html', projects=projects, active_project=active_project)

@app.route('/admin')
@login_required
def admin():
    # Only admin users can access this page
    if not current_user.is_admin:
        flash('You do not have permission to access the admin panel')
        return redirect(url_for('index'))
    
    # Get all users
    users = User.query.all()
    
    return render_template('admin.html', users=users)

@app.route('/admin/toggle-admin/<int:user_id>', methods=['POST'])
@login_required
def toggle_admin(user_id):
    # Only admin users can access this functionality
    if not current_user.is_admin:
        flash('You do not have permission to perform this action')
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(user_id)
    user.is_admin = not user.is_admin
    db.session.commit()
    
    flash(f'Admin status for {user.email} has been {"granted" if user.is_admin else "revoked"}')
    return redirect(url_for('admin'))

@app.route('/admin/toggle-paid-plan/<int:user_id>', methods=['POST'])
@login_required
def toggle_paid_plan(user_id):
    # Only admin users can access this functionality
    if not current_user.is_admin:
        flash('You do not have permission to perform this action')
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(user_id)
    user.has_paid_plan = not user.has_paid_plan
    
    # If removing paid plan, also remove subscription ID
    if not user.has_paid_plan:
        user.subscription_id = None
    
    db.session.commit()
    
    flash(f'Paid plan for {user.email} has been {"activated" if user.has_paid_plan else "deactivated"}')
    return redirect(url_for('admin'))

@app.route('/project/create', methods=['POST'])
@login_required
def create_project():
    project_name = request.form.get('project_name')
    if not project_name:
        flash('Project name is required')
        return redirect(url_for('index'))
    
    time_tracker = current_user.get_time_tracker()
    
    # Check if project already exists
    if time_tracker.get_project(project_name):
        flash('Project already exists')
        return redirect(url_for('index'))
    
    # Create new project with a session
    comment = request.form.get('comment', '')
    time_tracker.add_or_update_project(project_name, comment)
    
    flash(f'Project "{project_name}" created and time tracking started')
    return redirect(url_for('index'))

@app.route('/project/<project_name>/toggle', methods=['POST'])
@login_required
def toggle_project(project_name):
    comment = request.form.get('comment', '')
    time_tracker = current_user.get_time_tracker()
    
    # Check if project exists
    project = time_tracker.get_project(project_name)
    if not project:
        flash(f'Project "{project_name}" not found')
        return redirect(url_for('index'))
    
    # Toggle the project (start or stop)
    time_tracker.add_or_update_project(project_name, comment)
    
    # Determine if we started or stopped
    project = time_tracker.get_project(project_name)
    last_session = project['sessions'][-1]
    if last_session['end'] is None:
        flash(f'Started time tracking for "{project_name}"')
    else:
        flash(f'Stopped time tracking for "{project_name}"')
    
    return redirect(url_for('index'))

@app.route('/project/<project_name>/report')
@login_required
def project_report(project_name):
    time_tracker = current_user.get_time_tracker()
    
    # Check if project exists
    project = time_tracker.get_project(project_name)
    if not project:
        flash(f'Project "{project_name}" not found')
        return redirect(url_for('index'))
    
    # Get daily hours
    daily_hours = time_tracker.assemble_total_hours_per_day(project_name)
    
    # Get all sessions for the project
    sessions = project['sessions']
    
    # Group sessions by date
    sessions_by_date = {}
    for session in sessions:
        start_date = datetime.strptime(session['start'], "%d/%m/%y - %H:%M:%S").date()
        
        # Handle sessions that span multiple days
        if session['end'] is not None:
            end_date = datetime.strptime(session['end'], "%d/%m/%y - %H:%M:%S").date()
            current_date = start_date
            while current_date <= end_date:
                date_str = current_date.strftime('%Y-%m-%d')
                if date_str not in sessions_by_date:
                    sessions_by_date[date_str] = []
                
                # Add session to this date
                sessions_by_date[date_str].append(session)
                current_date += timedelta(days=1)
        else:
            # For active sessions
            date_str = start_date.strftime('%Y-%m-%d')
            if date_str not in sessions_by_date:
                sessions_by_date[date_str] = []
            sessions_by_date[date_str].append(session)
    
    # Format for display
    daily_report = []
    for date, hours in daily_hours:
        date_str = date.strftime('%Y-%m-%d')
        hours_decimal = hours.total_seconds() / 3600
        
        # Get sessions for this date
        date_sessions = sessions_by_date.get(date_str, [])
        
        daily_report.append({
            'date': date_str,
            'hours': round(hours_decimal, 2),
            'sessions': date_sessions
        })
    
    # Calculate total hours
    total_hours = time_tracker.calculate_total_hours(project_name).total_seconds() / 3600
    
    return render_template(
        'project_report.html', 
        project_name=project_name, 
        daily_report=daily_report, 
        total_hours=round(total_hours, 2),
        project=project
    )

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        logger.info(f'loggin in {email}')
        user = User.query.filter_by(email=email).first()
        logger.info(f'logged in {user}')
        if user and user.password == password:
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        subscribe = request.form.get('subscribe') == 'on'
        
        # Create a new user
        user = User(
            email=email, 
            password=password, 
            is_admin=False,
            has_paid_plan=False
        )
        
        if subscribe and 'stripeToken' in request.form:
            stripe_token = request.form['stripeToken']
            try:
                # Create a new Stripe customer with the tokenized card information
                customer = stripe.Customer.create(
                    email=email,
                    source=stripe_token,  # Use the token from Stripe.js
                )
                
                # Create a subscription for the customer
                subscription = stripe.Subscription.create(
                    customer=customer.id,
                    items=[{'price': 'price_1PPH0zBLvzmZ9ZyKpAcXdxAe'}]
                )
                
                # Update user with subscription info
                user.subscription_id = subscription.id
                user.has_paid_plan = True
                
            except stripe.error.StripeError as e:
                flash(f"Stripe error: {e.user_message}")
                return render_template('register.html', stripe_publishable_key=app.config['STRIPE_PUBLISHABLE_KEY'])
        
        # Save the user
        db.session.add(user)
        db.session.commit()
        login_user(user)
        
        flash('Registration successful!')
        return redirect(url_for('index'))
    
    return render_template('register.html', stripe_publishable_key=app.config['STRIPE_PUBLISHABLE_KEY'])

@app.route('/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': 'price_1PPIOhBLvzmZ9ZyKNZLzyP17',
                'quantity': 1,
            }],
            mode='subscription',
            success_url='http://localhost:5000/success',
            cancel_url='http://localhost:5000/cancel',
            customer=current_user.stripe_customer_id
        )
        return redirect(session.url, code=303)
    except Exception as e:
        return str(e)

@app.route('/attach-payment-method', methods=['POST'])
@login_required
def attach_payment_method():
    data = request.get_json()
    payment_method_id = data['paymentMethodId']

    try:
        stripe.PaymentMethod.attach(
            payment_method_id,
            customer=current_user.stripe_customer_id,
        )
        # Set the attached payment method as the default
        stripe.Customer.modify(
            current_user.stripe_customer_id,
            invoice_settings={
                'default_payment_method': payment_method_id,
            },
        )
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/payment')
@login_required
def payment():
    return render_template('payment.html', stripe_publishable_key=os.getenv('STRIPE_PUBLISHABLE_KEY'))

@app.route('/create-subscription', methods=['POST'])
@login_required
def create_subscription():
    try:
        subscription = stripe.Subscription.create(
            customer=current_user.stripe_customer_id,
            items=[{
                'price': 'price_id_from_stripe_dashboard',
                'quantity': 1,
            }],
            default_payment_method=current_user.default_payment_method_id,
        )
        return jsonify(subscription)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/invite', methods=['GET', 'POST'])
@login_required
def invite():
    # Any user can invite others
    if request.method == 'POST':
        email = request.form['email']
        token = uuid.uuid4().hex
        invitation = Invitation(inviter_id=current_user.id, email=email, token=token)
        db.session.add(invitation)
        db.session.commit()

        # Send invitation email
        msg = Message('Invitation to join Presis', sender='noreply@example.com', recipients=[email])
        msg.body = f'You have been invited to join Presis by {current_user.email}. Please register using the following link: {request.host_url}register/{token}'
        mail.send(msg)

        flash('Invitation sent')
    return render_template('invite.html')

@app.route('/register/<token>', methods=['GET', 'POST'])
def register_token(token):
    invitation = Invitation.query.filter_by(token=token).first()
    
    if not invitation:
        flash('Invalid or expired token')
        return redirect(url_for('register'))

    if request.method == 'POST':
        password = request.form['password']
        subscribe = request.form.get('subscribe') == 'on'
        
        # Create a new user
        user = User(
            email=invitation.email, 
            password=password, 
            is_admin=False,
            has_paid_plan=False
        )
        
        if subscribe and 'stripeToken' in request.form:
            stripe_token = request.form['stripeToken']
            try:
                # Create a new Stripe customer with the tokenized card information
                customer = stripe.Customer.create(
                    email=invitation.email,
                    source=stripe_token,  # Use the token from Stripe.js
                )
                
                # Create a subscription for the customer
                subscription = stripe.Subscription.create(
                    customer=customer.id,
                    items=[{'price': 'price_1PPH0zBLvzmZ9ZyKpAcXdxAe'}]
                )
                
                # Update user with subscription info
                user.subscription_id = subscription.id
                user.has_paid_plan = True
                
            except stripe.error.StripeError as e:
                flash(f"Stripe error: {e.user_message}")
                return render_template('register.html', token=token, email=invitation.email, 
                                      stripe_publishable_key=app.config['STRIPE_PUBLISHABLE_KEY'])
        
        # Save the user and delete the invitation
        db.session.add(user)
        db.session.delete(invitation)
        db.session.commit()
        login_user(user)
        
        flash('Registration successful!')
        return redirect(url_for('index'))

    return render_template('register.html', token=token, email=invitation.email, 
                          stripe_publishable_key=app.config['STRIPE_PUBLISHABLE_KEY'])

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

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
