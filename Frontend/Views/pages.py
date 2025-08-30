"""
Views for ClasifiCode Frontend
Handles all the page rendering and API interactions
"""

import requests
from flask import render_template, request, redirect, url_for, flash, session, jsonify
from functools import wraps
import logging

# Configure logging
logger = logging.getLogger(__name__)

# API base URL
API_BASE_URL = 'http://localhost:8000/api'

def login_required(f):
    """Decorator to require login for protected routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Por favor inicia sesión para acceder a esta página', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(required_role):
    """Decorator to require specific role for protected routes"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_role' not in session:
                flash('Acceso denegado', 'danger')
                return redirect(url_for('login'))
            
            if session['user_role'] != required_role and session['user_role'] != 'ADMIN':
                flash('No tienes permisos para acceder a esta página', 'danger')
                return redirect(url_for('dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def make_api_request(endpoint, method='GET', data=None, headers=None):
    """Helper function to make API requests"""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        
        if headers is None:
            headers = {}
        
        if 'access_token' in session:
            headers['Authorization'] = f"Bearer {session['access_token']}"
        
        if method.upper() == 'GET':
            response = requests.get(url, headers=headers, params=data)
        elif method.upper() == 'POST':
            response = requests.post(url, headers=headers, json=data)
        elif method.upper() == 'PUT':
            response = requests.put(url, headers=headers, json=data)
        elif method.upper() == 'DELETE':
            response = requests.delete(url, headers=headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in API request: {e}")
        return None

def home():
    """Home page view"""
    return render_template('home.html')

@login_required
def dashboard():
    """Dashboard view"""
    try:
        # Get user statistics
        stats = make_api_request('/admin/stats')
        
        # Get recent cases
        recent_cases = make_api_request('/cases', data={'limit': 5})
        
        # Get user profile
        user_profile = make_api_request('/auth/profile')
        
        return render_template('dashboard.html', 
                             stats=stats or {},
                             recent_cases=recent_cases or [],
                             user=user_profile or {})
    
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        flash('Error al cargar el dashboard', 'error')
        return render_template('dashboard.html', 
                             stats={}, 
                             recent_cases=[], 
                             user={})

@login_required
def classify():
    """Classification page view"""
    return render_template('classify/run.html')

@login_required
def cases_list():
    """Cases list view"""
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        status = request.args.get('status', '')
        priority = request.args.get('priority', '')
        assigned_to = request.args.get('assigned_to', '')
        search = request.args.get('search', '')
        
        # Build query parameters
        params = {
            'page': page,
            'per_page': 20
        }
        
        if status:
            params['status'] = status
        if priority:
            params['priority'] = priority
        if assigned_to:
            params['assigned_to'] = assigned_to
        if search:
            params['search'] = search
        
        # Get cases
        cases_response = make_api_request('/cases', data=params)
        
        # Get users for filter
        users_response = make_api_request('/admin/users')
        
        # Get statistics
        stats_response = make_api_request('/admin/stats')
        
        cases = cases_response or {'items': [], 'total': 0, 'pages': 0, 'page': 1}
        users = users_response or []
        stats = stats_response or {}
        
        return render_template('cases/list.html', 
                             cases=cases,
                             users=users,
                             stats=stats)
    
    except Exception as e:
        logger.error(f"Error loading cases list: {e}")
        flash('Error al cargar la lista de casos', 'error')
        return render_template('cases/list.html', 
                             cases={'items': [], 'total': 0, 'pages': 0, 'page': 1},
                             users=[],
                             stats={})

@login_required
def new_case():
    """New case creation view"""
    if request.method == 'POST':
        try:
            # Prepare case data
            case_data = {
                'title': request.form.get('title'),
                'description': request.form.get('description'),
                'product_name': request.form.get('product_name'),
                'product_description': request.form.get('product_description'),
                'brand': request.form.get('brand'),
                'model': request.form.get('model'),
                'origin_country': request.form.get('origin_country'),
                'destination_country': request.form.get('destination_country'),
                'proposed_hs_code': request.form.get('proposed_hs_code'),
                'priority': request.form.get('priority', 'MEDIUM'),
                'assigned_to': request.form.get('assigned_to'),
                'confidence_score': request.form.get('confidence_score')
            }
            
            # Remove empty values
            case_data = {k: v for k, v in case_data.items() if v}
            
            # Create case
            response = make_api_request('/cases', method='POST', data=case_data)
            
            if response and response.get('success'):
                flash('Caso creado exitosamente', 'success')
                return redirect(url_for('case_detail', case_id=response['case']['id']))
            else:
                flash('Error al crear el caso', 'error')
        
        except Exception as e:
            logger.error(f"Error creating case: {e}")
            flash('Error al crear el caso', 'error')
    
    try:
        # Get users for assignment
        users = make_api_request('/admin/users') or []
        return render_template('cases/new.html', users=users)
    
    except Exception as e:
        logger.error(f"Error loading new case form: {e}")
        flash('Error al cargar el formulario', 'error')
        return render_template('cases/new.html', users=[])

@login_required
def case_detail(case_id):
    """Case detail view"""
    try:
        # Get case details
        case = make_api_request(f'/cases/{case_id}')
        
        if not case:
            flash('Caso no encontrado', 'error')
            return redirect(url_for('cases_list'))
        
        return render_template('cases/detail.html', case=case)
    
    except Exception as e:
        logger.error(f"Error loading case detail: {e}")
        flash('Error al cargar los detalles del caso', 'error')
        return redirect(url_for('cases_list'))

@login_required
def edit_case(case_id):
    """Edit case view"""
    try:
        if request.method == 'POST':
            # Prepare case data
            case_data = {
                'title': request.form.get('title'),
                'description': request.form.get('description'),
                'product_name': request.form.get('product_name'),
                'product_description': request.form.get('product_description'),
                'brand': request.form.get('brand'),
                'model': request.form.get('model'),
                'origin_country': request.form.get('origin_country'),
                'destination_country': request.form.get('destination_country'),
                'proposed_hs_code': request.form.get('proposed_hs_code'),
                'priority': request.form.get('priority'),
                'assigned_to': request.form.get('assigned_to'),
                'confidence_score': request.form.get('confidence_score')
            }
            
            # Remove empty values
            case_data = {k: v for k, v in case_data.items() if v}
            
            # Update case
            response = make_api_request(f'/cases/{case_id}', method='PUT', data=case_data)
            
            if response and response.get('success'):
                flash('Caso actualizado exitosamente', 'success')
                return redirect(url_for('case_detail', case_id=case_id))
            else:
                flash('Error al actualizar el caso', 'error')
        
        # Get case details
        case = make_api_request(f'/cases/{case_id}')
        
        if not case:
            flash('Caso no encontrado', 'error')
            return redirect(url_for('cases_list'))
        
        # Get users for assignment
        users = make_api_request('/admin/users') or []
        
        return render_template('cases/edit.html', case=case, users=users)
    
    except Exception as e:
        logger.error(f"Error editing case: {e}")
        flash('Error al editar el caso', 'error')
        return redirect(url_for('cases_list'))

@login_required
def profile():
    """User profile view"""
    try:
        if request.method == 'POST':
            # Prepare profile data
            profile_data = {
                'first_name': request.form.get('first_name'),
                'last_name': request.form.get('last_name'),
                'email': request.form.get('email')
            }
            
            # Update profile
            response = make_api_request('/auth/profile', method='PUT', data=profile_data)
            
            if response and response.get('success'):
                flash('Perfil actualizado exitosamente', 'success')
                # Update session data
                session['user_name'] = f"{profile_data['first_name']} {profile_data['last_name']}"
            else:
                flash('Error al actualizar el perfil', 'error')
        
        # Get user profile
        user = make_api_request('/auth/profile') or {}
        
        return render_template('profile.html', user=user)
    
    except Exception as e:
        logger.error(f"Error loading profile: {e}")
        flash('Error al cargar el perfil', 'error')
        return render_template('profile.html', user={})

@login_required
@role_required('ADMIN')
def admin_dashboard():
    """Admin dashboard view"""
    try:
        # Get admin statistics
        stats = make_api_request('/admin/stats')
        
        # Get system health
        health = make_api_request('/health')
        
        # Get recent activity
        activity = make_api_request('/admin/activity')
        
        return render_template('admin/dashboard.html', 
                             stats=stats or {},
                             health=health or {},
                             activity=activity or [])
    
    except Exception as e:
        logger.error(f"Error loading admin dashboard: {e}")
        flash('Error al cargar el dashboard de administración', 'error')
        return render_template('admin/dashboard.html', 
                             stats={}, 
                             health={}, 
                             activity=[])

def login():
    """Login view"""
    if request.method == 'POST':
        try:
            login_data = {
                'username': request.form.get('username'),
                'password': request.form.get('password')
            }
            
            response = make_api_request('/auth/login', method='POST', data=login_data)
            
            if response and response.get('success'):
                # Store user data in session
                session['user_id'] = response['user']['id']
                session['username'] = response['user']['username']
                session['user_name'] = response['user']['full_name']
                session['user_role'] = response['user']['role']
                session['access_token'] = response['access_token']
                session['refresh_token'] = response['refresh_token']
                
                flash('Inicio de sesión exitoso', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Credenciales inválidas', 'error')
        
        except Exception as e:
            logger.error(f"Login error: {e}")
            flash('Error en el inicio de sesión', 'error')
    
    return render_template('auth/login.html')

def register():
    """Register view"""
    if request.method == 'POST':
        try:
            register_data = {
                'username': request.form.get('username'),
                'email': request.form.get('email'),
                'password': request.form.get('password'),
                'first_name': request.form.get('first_name'),
                'last_name': request.form.get('last_name')
            }
            
            response = make_api_request('/auth/register', method='POST', data=register_data)
            
            if response and response.get('success'):
                flash('Registro exitoso. Por favor inicia sesión.', 'success')
                return redirect(url_for('login'))
            else:
                flash('Error en el registro', 'error')
        
        except Exception as e:
            logger.error(f"Registration error: {e}")
            flash('Error en el registro', 'error')
    
    return render_template('auth/register.html')

def logout():
    """Logout view"""
    try:
        # Revoke token on backend
        if 'access_token' in session:
            make_api_request('/auth/logout', method='POST')
    except Exception as e:
        logger.error(f"Logout error: {e}")
    
    # Clear session
    session.clear()
    flash('Sesión cerrada exitosamente', 'success')
    return redirect(url_for('home'))

# API proxy functions for AJAX requests
def api_proxy():
    """Proxy for API requests from frontend"""
    try:
        # Get the endpoint from the request
        endpoint = request.path.replace('/api/', '')
        
        # Forward the request to the backend API
        response = make_api_request(f'/{endpoint}', 
                                  method=request.method,
                                  data=request.get_json() if request.is_json else request.form.to_dict(),
                                  headers=dict(request.headers))
        
        return jsonify(response or {})
    
    except Exception as e:
        logger.error(f"API proxy error: {e}")
        return jsonify({'error': 'Internal server error'}), 500
