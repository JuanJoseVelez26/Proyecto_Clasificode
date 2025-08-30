from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import requests
import os
from datetime import datetime
import logging

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key')

# Configuration
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8000')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def make_api_request(endpoint, method='GET', data=None, headers=None):
    """Make API request to backend"""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        
        if headers is None:
            headers = {}
        
        # Add authentication token if available
        if 'access_token' in session:
            headers['Authorization'] = f"Bearer {session['access_token']}"
        
        if method == 'GET':
            response = requests.get(url, headers=headers)
        elif method == 'POST':
            response = requests.post(url, json=data, headers=headers)
        elif method == 'PUT':
            response = requests.put(url, json=data, headers=headers)
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        return response
        
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        return None

def is_authenticated():
    """Check if user is authenticated"""
    return 'access_token' in session and 'user' in session

def require_auth(f):
    """Decorator to require authentication"""
    def decorated_function(*args, **kwargs):
        if not is_authenticated():
            flash('Please log in to access this page', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/')
def home():
    """Home page"""
    if is_authenticated():
        return redirect(url_for('dashboard'))
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Username and password are required', 'error')
            return render_template('auth/login.html')
        
        # Make API request to login
        response = make_api_request('/api/auth/login', method='POST', data={
            'username': username,
            'password': password
        })
        
        if response and response.status_code == 200:
            data = response.json()
            session['access_token'] = data['access_token']
            session['refresh_token'] = data['refresh_token']
            session['user'] = data['user']
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            error_msg = 'Invalid credentials'
            if response and response.status_code == 401:
                error_data = response.json()
                error_msg = error_data.get('error', 'Invalid credentials')
            flash(error_msg, 'error')
    
    return render_template('auth/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Register page"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        
        # Validate form data
        if not all([username, email, password, confirm_password, first_name, last_name]):
            flash('All fields are required', 'error')
            return render_template('auth/register.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('auth/register.html')
        
        # Make API request to register
        response = make_api_request('/api/auth/register', method='POST', data={
            'username': username,
            'email': email,
            'password': password,
            'first_name': first_name,
            'last_name': last_name
        })
        
        if response and response.status_code == 201:
            data = response.json()
            session['access_token'] = data['access_token']
            session['refresh_token'] = data['refresh_token']
            session['user'] = data['user']
            flash('Registration successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            error_msg = 'Registration failed'
            if response and response.status_code in [400, 409]:
                error_data = response.json()
                error_msg = error_data.get('error', 'Registration failed')
            flash(error_msg, 'error')
    
    return render_template('auth/register.html')

@app.route('/logout')
def logout():
    """Logout user"""
    # Make API request to logout
    make_api_request('/api/auth/logout', method='POST')
    
    # Clear session
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('home'))

@app.route('/dashboard')
@require_auth
def dashboard():
    """Dashboard page"""
    user = session.get('user', {})
    
    # Get user statistics
    stats_response = make_api_request('/api/classify/stats')
    stats = {}
    if stats_response and stats_response.status_code == 200:
        stats = stats_response.json()
    
    return render_template('dashboard.html', user=user, stats=stats)

@app.route('/classify', methods=['GET', 'POST'])
@require_auth
def classify():
    """Classification page"""
    if request.method == 'POST':
        product_name = request.form.get('product_name')
        product_description = request.form.get('product_description')
        brand = request.form.get('brand')
        model = request.form.get('model')
        origin_country = request.form.get('origin_country')
        destination_country = request.form.get('destination_country')
        
        if not product_name or not product_description:
            flash('Product name and description are required', 'error')
            return render_template('classify/run.html')
        
        # Make API request to classify
        response = make_api_request('/api/classify', method='POST', data={
            'product_name': product_name,
            'product_description': product_description,
            'brand': brand,
            'model': model,
            'origin_country': origin_country,
            'destination_country': destination_country
        })
        
        if response and response.status_code == 200:
            data = response.json()
            flash('Classification completed successfully!', 'success')
            return render_template('classify/run.html', 
                                 classification_result=data,
                                 show_results=True)
        else:
            error_msg = 'Classification failed'
            if response and response.status_code == 400:
                error_data = response.json()
                error_msg = error_data.get('error', 'Classification failed')
            flash(error_msg, 'error')
    
    return render_template('classify/run.html')

@app.route('/cases')
@require_auth
def cases():
    """Cases list page"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status')
    search = request.args.get('search')
    
    # Build query parameters
    params = {'page': page}
    if status:
        params['status'] = status
    if search:
        params['search'] = search
    
    # Make API request to get cases
    response = make_api_request(f'/api/cases?page={page}')
    
    cases_data = {'cases': [], 'pagination': {}}
    if response and response.status_code == 200:
        cases_data = response.json()
    
    return render_template('cases/list.html', 
                         cases=cases_data['cases'],
                         pagination=cases_data['pagination'],
                         current_status=status,
                         current_search=search)

@app.route('/cases/new', methods=['GET', 'POST'])
@require_auth
def new_case():
    """Create new case page"""
    if request.method == 'POST':
        product_name = request.form.get('product_name')
        product_description = request.form.get('product_description')
        brand = request.form.get('brand')
        model = request.form.get('model')
        origin_country = request.form.get('origin_country')
        destination_country = request.form.get('destination_country')
        priority = request.form.get('priority', 'medium')
        notes = request.form.get('notes')
        
        if not product_name or not product_description:
            flash('Product name and description are required', 'error')
            return render_template('cases/new.html')
        
        # Make API request to create case
        response = make_api_request('/api/cases', method='POST', data={
            'product_name': product_name,
            'product_description': product_description,
            'brand': brand,
            'model': model,
            'origin_country': origin_country,
            'destination_country': destination_country,
            'priority': priority,
            'notes': notes
        })
        
        if response and response.status_code == 201:
            data = response.json()
            flash('Case created successfully!', 'success')
            return redirect(url_for('cases'))
        else:
            error_msg = 'Failed to create case'
            if response and response.status_code == 400:
                error_data = response.json()
                error_msg = error_data.get('error', 'Failed to create case')
            flash(error_msg, 'error')
    
    return render_template('cases/new.html')

@app.route('/cases/<int:case_id>')
@require_auth
def case_detail(case_id):
    """Case detail page"""
    # Make API request to get case
    response = make_api_request(f'/api/cases/{case_id}')
    
    if response and response.status_code == 200:
        case_data = response.json()
        return render_template('cases/detail.html', case=case_data['case'])
    else:
        flash('Case not found', 'error')
        return redirect(url_for('cases'))

@app.route('/profile')
@require_auth
def profile():
    """User profile page"""
    user = session.get('user', {})
    return render_template('profile.html', user=user)

@app.route('/admin')
@require_auth
def admin():
    """Admin page"""
    user = session.get('user', {})
    if user.get('role') != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    # Get system statistics
    stats_response = make_api_request('/api/admin/stats')
    stats = {}
    if stats_response and stats_response.status_code == 200:
        stats = stats_response.json()
    
    return render_template('admin.html', user=user, stats=stats)

@app.errorhandler(404)
def not_found(error):
    """404 error handler"""
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """500 error handler"""
    return render_template('errors/500.html'), 500

if __name__ == '__main__':
    host = os.getenv('FRONTEND_HOST', '0.0.0.0')
    port = int(os.getenv('FRONTEND_PORT', 8080))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    print(f"Starting ClasifiCode Frontend on {host}:{port}")
    print(f"API Base URL: {API_BASE_URL}")
    print(f"Debug mode: {debug}")
    
    app.run(host=host, port=port, debug=debug)
