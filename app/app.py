import os
import json
import redis
from datetime import datetime, timedelta
from flask import Flask, render_template, redirect, url_for, request, flash, session, send_from_directory, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import stripe
import uuid
import secrets
import logging
from werkzeug.security import generate_password_hash, check_password_hash
from presis.time_tracker import TimeTracker
from presis.redis_backend import RedisBackend
from presis.redis_user import RedisUser, RedisUserRepository
from presis.redis_time_tracker import RedisTimeTracker

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)

app = Flask(__name__)
app.config.from_object('config.Config')

# Check if we should use Redis instead of filesystem
USE_REDIS = os.environ.get('PRESIS_NO_FSDB', '').lower() == 'true'

# Add context processor for current year
@app.context_processor
def inject_now():
    return {'now': datetime.now()}

# Set up database and user model based on configuration
if USE_REDIS:
    # Use Redis for storage
    redis_host = os.environ.get('REDIS_HOST', 'localhost')
    redis_port = int(os.environ.get('REDIS_PORT', 6379))
    redis_db = int(os.environ.get('REDIS_DB', 0))
    redis_password = os.environ.get('REDIS_PASSWORD', None)
    
    redis_backend = RedisBackend(host=redis_host, port=redis_port, db=redis_db, password=redis_password)
    redis_user_repository = RedisUserRepository(redis_backend)
    User = RedisUser
    # Define a global variable to access the repository
    user_repository = redis_user_repository
else:
    # Use SQLAlchemy for storage
    db = SQLAlchemy(app)
    # Define the User model normally
    class User(UserMixin, db.Model):
        id = db.Column(db.Integer, primary_key=True)
        email = db.Column(db.String(120), unique=True, nullable=False)
        password = db.Column(db.String(120), nullable=False)
        is_admin = db.Column(db.Boolean, default=False)
        has_paid_plan = db.Column(db.Boolean, default=False)
        subscription_id = db.Column(db.String(120), nullable=True)
        stripe_customer_id = db.Column(db.String(120), nullable=True)
        time_data_file = db.Column(db.String(255), nullable=True)
        # Add the API token field
        api_token = db.Column(db.String(64), unique=True, nullable=True)
        
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
        
        def generate_api_token(self):
            """Generate a new API token for the user"""
            self.api_token = secrets.token_hex(32)
            db.session.commit()
            return self.api_token

    # Invitation model (only used with SQLAlchemy)
    class Invitation(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        inviter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
        email = db.Column(db.String(120), nullable=False)
        token = db.Column(db.String(120), unique=True, nullable=False)

mail = Mail(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Initialize database if using SQLAlchemy
if not USE_REDIS:
    # Create database tables within an application context
    with app.app_context():
        db.create_all()

stripe.api_key = app.config['STRIPE_API_KEY']

@login_manager.user_loader
def load_user(user_id):
    if USE_REDIS:
        return user_repository.get(int(user_id))
    else:
        return User.query.get(int(user_id))

# API token authentication
def get_user_by_token(token):
    """Get a user by their API token"""
    if not token:
        return None
    
    if USE_REDIS:
        return user_repository.filter_by(api_token=token).first()
    else:
        return User.query.filter_by(api_token=token).first()

def auth_token_required(f):
    """Decorator for routes that require API token authentication"""
    from functools import wraps
    
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if token and token.startswith('Bearer '):
            token = token[7:]  # Remove 'Bearer ' prefix
        
        user = get_user_by_token(token)
        if not user:
            abort(401)
        
        # Set the authenticated user for this request
        return f(user, *args, **kwargs)
    
    return decorated

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
    if USE_REDIS:
        users = user_repository.all()
    else:
        users = User.query.all()
    
    return render_template('admin.html', users=users)

@app.route('/admin/toggle-admin/<int:user_id>', methods=['POST'])
@login_required
def toggle_admin(user_id):
    # Only admin users can access this functionality
    if not current_user.is_admin:
        flash('You do not have permission to perform this action')
        return redirect(url_for('index'))
    
    if USE_REDIS:
        user = user_repository.get(user_id)
        if not user:
            abort(404)
        user.is_admin = not user.is_admin
        user.save()
    else:
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
    
    if USE_REDIS:
        user = user_repository.get(user_id)
        if not user:
            abort(404)
        user.has_paid_plan = not user.has_paid_plan
        
        # If removing paid plan, also remove subscription ID
        if not user.has_paid_plan:
            user.subscription_id = None
        
        user.save()
    else:
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

@app.route('/project/merge', methods=['POST'])
@login_required
def merge_projects():
    source_project = request.form.get('source_project')
    destination_project = request.form.get('destination_project')
    
    # Validate inputs
    if not source_project or not destination_project:
        flash('Both source and destination projects are required')
        return redirect(url_for('index'))
    
    if source_project == destination_project:
        flash('Cannot merge a project with itself')
        return redirect(url_for('index'))
    
    time_tracker = current_user.get_time_tracker()
    success, message = time_tracker.merge_projects(source_project, destination_project)
    
    if success:
        flash(message)
    else:
        flash(f'Error merging projects: {message}')
    
    return redirect(url_for('index'))

@app.route('/project/<project_name>/add-entry', methods=['POST'])
@login_required
def add_manual_entry(project_name):
    # Extract form data
    start_date = request.form.get('start_date')
    start_time = request.form.get('start_time')
    end_date = request.form.get('end_date')
    end_time = request.form.get('end_time')
    comment = request.form.get('comment', '')
    closing_comment = request.form.get('closing_comment', '')
    
    # Validate required fields
    if not all([start_date, start_time, end_date, end_time]):
        flash('All date and time fields are required')
        return redirect(url_for('project_report', project_name=project_name))
    
    time_tracker = current_user.get_time_tracker()
    
    # Check if project exists
    project = time_tracker.get_project(project_name)
    if not project:
        flash(f'Project "{project_name}" not found')
        return redirect(url_for('index'))
    
    # Add manual session
    time_tracker.add_manual_session(
        project_name, 
        start_date, 
        start_time, 
        end_date, 
        end_time, 
        comment, 
        closing_comment
    )
    
    flash(f'Time entry added to "{project_name}"')
    return redirect(url_for('project_report', project_name=project_name))

@app.route('/project/<project_name>/edit-entry', methods=['POST'])
@login_required
def edit_manual_entry(project_name):
    # Extract form data
    event_id = request.form.get('event_id')
    start_date = request.form.get('start_date')
    start_time = request.form.get('start_time')
    end_date = request.form.get('end_date')
    end_time = request.form.get('end_time')
    comment = request.form.get('comment', '')
    closing_comment = request.form.get('closing_comment', '')
    
    # Validate required fields
    if not all([start_date, start_time, end_date, end_time]):
        flash('All date and time fields are required')
        return redirect(url_for('project_report', project_name=project_name))
    
    # Currently, we don't have a proper way to edit existing entries
    # We would need to add that functionality to the TimeTracker class
    # For now, just show a message
    flash('Editing entries is not yet implemented')
    
    return redirect(url_for('project_report', project_name=project_name))

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
    
    # Prepare calendar events data in JSON format
    calendar_events = []
    for day in daily_report:
        for session in day['sessions']:
            event = {
                'title': session.get('comment', 'Work session'),
                'date': day['date'],
                'hours': day['hours'],
                'timeRange': f"{session['start']} - {session.get('end', 'ongoing')}",
                'comment': session.get('comment', ''),
                'closingComment': session.get('closing_comment', '')
            }
            calendar_events.append(event)
    
    import json
    calendar_events_json = json.dumps(calendar_events)
    
    return render_template(
        'project_report.html', 
        project_name=project_name, 
        daily_report=daily_report, 
        total_hours=round(total_hours, 2),
        project=project,
        calendar_events_json=calendar_events_json
    )

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        logger.info(f'login attempt for {email}')
        
        if USE_REDIS:
            user = user_repository.filter_by(email=email).first()
            # Note that Redis stores hashed passwords, so we need to check differently
            if user and check_password_hash(user.password, password):
                login_user(user)
                return redirect(url_for('index'))
        else:
            user = User.query.filter_by(email=email).first()
            if user and user.password == password:
                login_user(user)
                return redirect(url_for('index'))
                
        flash('Invalid credentials')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        subscribe = request.form.get('subscribe') == 'on'
        
        # Handle Stripe subscription if needed
        stripe_customer_id = None
        subscription_id = None
        has_paid_plan = False
        
        if subscribe and 'stripeToken' in request.form:
            stripe_token = request.form['stripeToken']
            try:
                # Create a new Stripe customer with the tokenized card information
                customer = stripe.Customer.create(
                    email=email,
                    source=stripe_token,  # Use the token from Stripe.js
                )
                
                # Store the customer ID
                stripe_customer_id = customer.id
                
                # Create a subscription for the customer
                subscription = stripe.Subscription.create(
                    customer=customer.id,
                    items=[{'price': 'price_1PPH0zBLvzmZ9ZyKpAcXdxAe'}]
                )
                
                # Update user with subscription info
                subscription_id = subscription.id
                has_paid_plan = True
                
            except stripe.error.StripeError as e:
                flash(f"Stripe error: {e.user_message}")
                return render_template('register.html', stripe_publishable_key=app.config['STRIPE_PUBLISHABLE_KEY'])
        
        # Create the user based on storage type
        if USE_REDIS:
            try:
                user = user_repository.create(
                    email=email,
                    password=password,
                    is_admin=False,
                    has_paid_plan=has_paid_plan,
                    subscription_id=subscription_id,
                    stripe_customer_id=stripe_customer_id
                )
                login_user(user)
            except ValueError as e:
                flash(str(e))
                return render_template('register.html', stripe_publishable_key=app.config['STRIPE_PUBLISHABLE_KEY'])
        else:
            # Create a new user with SQLAlchemy
            user = User(
                email=email, 
                password=password, 
                is_admin=False,
                has_paid_plan=has_paid_plan,
                subscription_id=subscription_id,
                stripe_customer_id=stripe_customer_id
            )
            
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
            success_url='http://localhost:3000/success',
            cancel_url='http://localhost:3000/cancel',
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
        
        if USE_REDIS:
            # Store invitation in Redis
            invitation_data = {
                'inviter_id': current_user.id,
                'email': email,
                'token': token
            }
            redis_backend.r.set(f"invitation:{token}", json.dumps(invitation_data))
        else:
            # Store invitation in SQLAlchemy
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
    invitation = None
    invitation_email = None
    
    if USE_REDIS:
        # Get invitation from Redis
        invitation_data = redis_backend.r.get(f"invitation:{token}")
        if invitation_data:
            invitation_data = json.loads(invitation_data)
            invitation = invitation_data
            invitation_email = invitation_data.get('email')
    else:
        # Get invitation from SQLAlchemy
        invitation = Invitation.query.filter_by(token=token).first()
        if invitation:
            invitation_email = invitation.email
    
    if not invitation:
        flash('Invalid or expired token')
        return redirect(url_for('register'))

    if request.method == 'POST':
        password = request.form['password']
        subscribe = request.form.get('subscribe') == 'on'
        
        # Handle Stripe subscription
        stripe_customer_id = None
        subscription_id = None
        has_paid_plan = False
        
        if subscribe and 'stripeToken' in request.form:
            stripe_token = request.form['stripeToken']
            try:
                # Create a new Stripe customer with the tokenized card information
                customer = stripe.Customer.create(
                    email=invitation_email,
                    source=stripe_token,  # Use the token from Stripe.js
                )
                
                # Store the customer ID
                stripe_customer_id = customer.id
                
                # Create a subscription for the customer
                subscription = stripe.Subscription.create(
                    customer=customer.id,
                    items=[{'price': 'price_1PPH0zBLvzmZ9ZyKpAcXdxAe'}]
                )
                
                # Update user with subscription info
                subscription_id = subscription.id
                has_paid_plan = True
                
            except stripe.error.StripeError as e:
                flash(f"Stripe error: {e.user_message}")
                return render_template('register.html', token=token, email=invitation_email, 
                                      stripe_publishable_key=app.config['STRIPE_PUBLISHABLE_KEY'])
        
        # Create the user based on storage type
        if USE_REDIS:
            try:
                user = user_repository.create(
                    email=invitation_email,
                    password=password,
                    is_admin=False,
                    has_paid_plan=has_paid_plan,
                    subscription_id=subscription_id,
                    stripe_customer_id=stripe_customer_id
                )
                # Delete the invitation
                redis_backend.r.delete(f"invitation:{token}")
                login_user(user)
            except ValueError as e:
                flash(str(e))
                return render_template('register.html', token=token, email=invitation_email, 
                                      stripe_publishable_key=app.config['STRIPE_PUBLISHABLE_KEY'])
        else:
            # Create a new user with SQLAlchemy
            user = User(
                email=invitation_email, 
                password=password, 
                is_admin=False,
                has_paid_plan=has_paid_plan,
                subscription_id=subscription_id,
                stripe_customer_id=stripe_customer_id
            )
            
            # Save the user and delete the invitation
            db.session.add(user)
            db.session.delete(invitation)
            db.session.commit()
            login_user(user)
        
        flash('Registration successful!')
        return redirect(url_for('index'))

    return render_template('register.html', token=token, email=invitation_email, 
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
        if USE_REDIS:
            # Find user with the given subscription_id
            # This is inefficient, but subscription events are rare
            all_user_ids = redis_backend.r.keys("user:*")
            for user_key in all_user_ids:
                if not user_key.startswith("user:") or user_key.startswith("user_email:"):
                    continue
                user_id = user_key.split(":")[1]
                user = user_repository.get(user_id)
                if user and user.subscription_id == subscription['id']:
                    user.subscription_id = None
                    user.has_paid_plan = False
                    user.save()
                    break
        else:
            user = User.query.filter_by(subscription_id=subscription['id']).first()
            if user:
                user.subscription_id = None
                user.has_paid_plan = False
                db.session.commit()

    return jsonify({'status': 'success'})

@app.route('/account/cancel-subscription', methods=['POST'])
@login_required
def cancel_subscription():
    """Cancel the user's subscription"""
    if not current_user.subscription_id:
        flash('No active subscription found')
        return redirect(url_for('profile'))
    
    try:
        # Cancel the subscription in Stripe
        subscription = stripe.Subscription.retrieve(current_user.subscription_id)
        stripe.Subscription.delete(current_user.subscription_id)
        
        # Update user in database
        current_user.subscription_id = None
        current_user.has_paid_plan = False
        
        if USE_REDIS:
            current_user.save()
        else:
            db.session.commit()
        
        flash('Your subscription has been successfully canceled')
    except stripe.error.StripeError as e:
        flash(f'Error canceling subscription: {e.user_message}')
    
    return redirect(url_for('profile'))

@app.route('/account/delete', methods=['POST'])
@login_required
def delete_account():
    """Delete the user's account"""
    user_id = current_user.id
    
    # If user has a subscription, cancel it first
    if current_user.subscription_id:
        try:
            stripe.Subscription.delete(current_user.subscription_id)
        except stripe.error.StripeError as e:
            flash(f'Error canceling subscription: {e.user_message}')
            return redirect(url_for('profile'))
    
    # Log the user out
    logout_user()
    
    # Delete the user based on storage type
    if USE_REDIS:
        # For Redis, we need to handle this deletion
        user = user_repository.get(user_id)
        if user:
            # Delete all user data from Redis
            redis_backend.r.delete(f"user:{user_id}")
            redis_backend.r.delete(f"user_email:{user.email}")
            # Also delete any timesheet data
            redis_backend.r.delete(f"timesheet:user:{user_id}")
    else:
        # For SQLAlchemy
        user = User.query.get(user_id)
        if user:
            db.session.delete(user)
            db.session.commit()
    
    flash('Your account has been permanently deleted')
    return redirect(url_for('login'))

@app.route('/profile')
@login_required
def profile():
    """User profile page with API token management"""
    return render_template('profile.html')

@app.route('/profile/generate-token', methods=['POST'])
@login_required
def generate_api_token():
    """Generate a new API token for the user"""
    current_user.generate_api_token()
    flash('New API token generated successfully')
    return redirect(url_for('profile'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# API Endpoints for CLI Integration

@app.route('/api/auth', methods=['POST'])
def api_auth():
    """Authenticate a user and return an API token"""
    data = request.get_json()
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({"error": "Email and password required"}), 400
    
    if USE_REDIS:
        user = user_repository.filter_by(email=data['email']).first()
        if not user or not check_password_hash(user.password, data['password']):
            return jsonify({"error": "Invalid credentials"}), 401
    else:
        user = User.query.filter_by(email=data['email']).first()
        if not user or user.password != data['password']:
            return jsonify({"error": "Invalid credentials"}), 401
    
    # Generate a token if the user doesn't have one
    if not user.api_token:
        user.generate_api_token()
    
    return jsonify({
        "token": user.api_token,
        "user_id": user.id,
        "email": user.email
    })

@app.route('/api/projects', methods=['GET'])
@auth_token_required
def api_get_projects(user):
    """Get all projects for the authenticated user"""
    time_tracker = user.get_time_tracker()
    return jsonify({"projects": time_tracker.projects})

@app.route('/api/projects/<project_name>', methods=['GET'])
@auth_token_required
def api_get_project(user, project_name):
    """Get a specific project for the authenticated user"""
    time_tracker = user.get_time_tracker()
    project = time_tracker.get_project(project_name)
    if not project:
        return jsonify({"error": f"Project '{project_name}' not found"}), 404
    
    return jsonify({"project": project})

@app.route('/api/projects/<project_name>/toggle', methods=['POST'])
@auth_token_required
def api_toggle_project(user, project_name):
    """Toggle time tracking for a project"""
    data = request.get_json() or {}
    comment = data.get('comment', '')
    
    time_tracker = user.get_time_tracker()
    project = time_tracker.get_project(project_name)
    
    # If project doesn't exist, create it
    if not project:
        time_tracker.add_or_update_project(project_name, comment)
        return jsonify({
            "message": f"Project '{project_name}' created and time tracking started",
            "status": "started"
        })
    
    # Toggle the project (start or stop)
    time_tracker.add_or_update_project(project_name, comment)
    
    # Determine if we started or stopped
    project = time_tracker.get_project(project_name)
    last_session = project['sessions'][-1]
    status = "started" if last_session['end'] is None else "stopped"
    
    return jsonify({
        "message": f"Time tracking for '{project_name}' {status}",
        "status": status
    })

@app.route('/api/projects/<project_name>/manual-entry', methods=['POST'])
@auth_token_required
def api_add_manual_entry(user, project_name):
    """Add a manual time entry to a project"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    # Extract data
    start_date = data.get('start_date')
    start_time = data.get('start_time')
    end_date = data.get('end_date')
    end_time = data.get('end_time')
    comment = data.get('comment', '')
    closing_comment = data.get('closing_comment', '')
    
    # Validate required fields
    if not all([start_date, start_time, end_date, end_time]):
        return jsonify({"error": "All date and time fields are required"}), 400
    
    time_tracker = user.get_time_tracker()
    
    # Check if project exists
    project = time_tracker.get_project(project_name)
    if not project:
        # Create project if it doesn't exist
        time_tracker.add_or_update_project(project_name, comment)
        project = time_tracker.get_project(project_name)
    
    # Add manual session
    time_tracker.add_manual_session(
        project_name,
        start_date,
        start_time,
        end_date,
        end_time,
        comment,
        closing_comment
    )
    
    return jsonify({
        "message": f"Time entry added to '{project_name}'",
        "project": project
    })

@app.route('/api/sync', methods=['POST'])
@auth_token_required
def api_sync_data(user):
    """Sync time data between client and server"""
    data = request.get_json()
    if not data or 'projects' not in data:
        return jsonify({"error": "Invalid sync data format"}), 400
    
    time_tracker = user.get_time_tracker()
    client_projects = data['projects']
    
    # Merge client projects with server projects
    for client_project in client_projects:
        project_name = client_project['project_name']
        server_project = time_tracker.get_project(project_name)
        
        if server_project:
            # If project exists on server, merge sessions
            existing_sessions = {
                f"{s.get('start')}_{s.get('end')}": s 
                for s in server_project['sessions']
            }
            
            # Add new sessions from client
            for client_session in client_project['sessions']:
                session_key = f"{client_session.get('start')}_{client_session.get('end')}"
                if session_key not in existing_sessions:
                    server_project['sessions'].append(client_session)
            
            # Update server project
            time_tracker.update_project_raw(project_name, server_project)
        else:
            # If project doesn't exist on server, add it
            time_tracker.add_project_raw(client_project)
    
    # After merging, get updated server data
    server_data = {"projects": time_tracker.projects}
    
    return jsonify({
        "message": "Sync successful",
        "data": server_data
    })

if __name__ == '__main__':
    app.run(debug=True)
