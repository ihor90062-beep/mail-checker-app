import os
import logging
import threading
import time
import json
import socket
import smtplib
import poplib
import imaplib
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "demo_secret_key_for_development")

# In-memory storage for demonstration
users = {}
email_accounts = {}
proxy_servers = {}
check_results = {}
batch_jobs = {}

# Email provider configurations
EMAIL_PROVIDERS = {
    'gmail.com': {
        'smtp': {'host': 'smtp.gmail.com', 'port': 587, 'ssl': True},
        'imap': {'host': 'imap.gmail.com', 'port': 993, 'ssl': True},
        'pop3': {'host': 'pop.gmail.com', 'port': 995, 'ssl': True}
    },
    'yahoo.com': {
        'smtp': {'host': 'smtp.mail.yahoo.com', 'port': 587, 'ssl': True},
        'imap': {'host': 'imap.mail.yahoo.com', 'port': 993, 'ssl': True},
        'pop3': {'host': 'pop.mail.yahoo.com', 'port': 995, 'ssl': True}
    },
    'hotmail.com': {
        'smtp': {'host': 'smtp-mail.outlook.com', 'port': 587, 'ssl': True},
        'imap': {'host': 'outlook.office365.com', 'port': 993, 'ssl': True},
        'pop3': {'host': 'outlook.office365.com', 'port': 995, 'ssl': True}
    },
    'outlook.com': {
        'smtp': {'host': 'smtp-mail.outlook.com', 'port': 587, 'ssl': True},
        'imap': {'host': 'outlook.office365.com', 'port': 993, 'ssl': True},
        'pop3': {'host': 'outlook.office365.com', 'port': 995, 'ssl': True}
    }
}

def get_provider_config(email):
    """Get provider configuration based on email domain"""
    domain = email.split('@')[1].lower()
    return EMAIL_PROVIDERS.get(domain, {})

def simulate_email_check(email, password, protocol):
    """Simulate email account checking with realistic delays"""
    time.sleep(2)  # Simulate network delay
    
    # Mock validation logic
    if '@' not in email:
        return {'status': 'invalid', 'message': 'Invalid email format'}
    
    domain = email.split('@')[1].lower()
    if domain not in EMAIL_PROVIDERS:
        return {'status': 'unsupported', 'message': f'Provider {domain} not supported'}
    
    # Simulate success/failure based on simple rules
    if len(password) < 6:
        return {'status': 'failed', 'message': 'Authentication failed - password too short'}
    
    # Simulate random failures for demonstration
    import random
    if random.random() < 0.2:  # 20% failure rate
        return {'status': 'failed', 'message': 'Connection timeout or authentication failed'}
    
    return {
        'status': 'success',
        'message': f'{protocol.upper()} connection successful',
        'provider': domain,
        'protocol': protocol
    }

def simulate_proxy_check(proxy_host, proxy_port, proxy_type):
    """Simulate proxy checking with realistic delays"""
    time.sleep(1.5)  # Simulate network delay
    
    # Mock validation logic
    try:
        port = int(proxy_port)
        if port < 1 or port > 65535:
            return {'status': 'invalid', 'message': 'Invalid port number'}
    except ValueError:
        return {'status': 'invalid', 'message': 'Port must be a number'}
    
    # Simulate random results for demonstration
    import random
    if random.random() < 0.3:  # 30% failure rate
        return {'status': 'failed', 'message': 'Proxy connection failed or timeout'}
    
    response_time = round(random.uniform(100, 2000), 2)
    return {
        'status': 'success',
        'message': f'{proxy_type.upper()} proxy is working',
        'response_time': f'{response_time}ms',
        'type': proxy_type
    }

def run_batch_check(job_id, items, check_type):
    """Run batch checking in background thread"""
    logger.info(f"Starting batch job {job_id} with {len(items)} items")
    
    batch_jobs[job_id] = {
        'status': 'running',
        'progress': 0,
        'total': len(items),
        'results': [],
        'started_at': datetime.now().isoformat()
    }
    
    for i, item in enumerate(items):
        try:
            if check_type == 'email':
                result = simulate_email_check(item['email'], item['password'], item.get('protocol', 'smtp'))
                result['email'] = item['email']
            elif check_type == 'proxy':
                result = simulate_proxy_check(item['host'], item['port'], item.get('type', 'http'))
                result['proxy'] = f"{item['host']}:{item['port']}"
            
            batch_jobs[job_id]['results'].append(result)
            batch_jobs[job_id]['progress'] = i + 1
            
            logger.debug(f"Batch job {job_id}: completed {i + 1}/{len(items)}")
            
        except Exception as e:
            logger.error(f"Error in batch job {job_id}, item {i}: {e}")
            batch_jobs[job_id]['results'].append({
                'status': 'error',
                'message': f'Processing error: {str(e)}'
            })
    
    batch_jobs[job_id]['status'] = 'completed'
    batch_jobs[job_id]['completed_at'] = datetime.now().isoformat()
    logger.info(f"Batch job {job_id} completed")

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Validate input
        if not username or not email or not password:
            flash('All fields are required', 'error')
            return render_template('register.html')
        
        if username in users:
            flash('Username already exists', 'error')
            return render_template('register.html')
        
        # Create user
        user_id = len(users) + 1
        users[username] = {
            'id': user_id,
            'username': username,
            'email': email,
            'password_hash': generate_password_hash(password),
            'created_at': datetime.now().isoformat()
        }
        
        logger.info(f"New user registered: {username}")
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = users.get(username)
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = username
            logger.info(f"User logged in: {username}")
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    username = session.get('username')
    session.clear()
    logger.info(f"User logged out: {username}")
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    user_emails = [acc for acc in email_accounts.values() if acc['user_id'] == user_id]
    user_proxies = [proxy for proxy in proxy_servers.values() if proxy['user_id'] == user_id]
    user_results = [result for result in check_results.values() if result['user_id'] == user_id]
    
    stats = {
        'total_emails': len(user_emails),
        'total_proxies': len(user_proxies),
        'total_checks': len(user_results),
        'success_rate': 0
    }
    
    if user_results:
        successful = sum(1 for r in user_results if r.get('status') == 'success')
        stats['success_rate'] = round((successful / len(user_results)) * 100, 1)
    
    return render_template('dashboard.html', stats=stats)

@app.route('/email-checker')
def email_checker():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('email_checker.html', providers=EMAIL_PROVIDERS.keys())

@app.route('/proxy-checker')
def proxy_checker():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('proxy_checker.html')

@app.route('/batch-checker')
def batch_checker():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('batch_checker.html')

@app.route('/api/check-email', methods=['POST'])
def api_check_email():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    protocol = data.get('protocol', 'smtp')
    
    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400
    
    # Run check in background thread for realistic async behavior
    result = simulate_email_check(email, password, protocol)
    
    # Store result
    result_id = len(check_results) + 1
    check_results[result_id] = {
        'id': result_id,
        'user_id': session['user_id'],
        'type': 'email',
        'email': email,
        'protocol': protocol,
        'result': result,
        'checked_at': datetime.now().isoformat()
    }
    
    return jsonify(result)

@app.route('/api/check-proxy', methods=['POST'])
def api_check_proxy():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    host = data.get('host')
    port = data.get('port')
    proxy_type = data.get('type', 'http')
    
    if not host or not port:
        return jsonify({'error': 'Host and port required'}), 400
    
    result = simulate_proxy_check(host, port, proxy_type)
    
    # Store result
    result_id = len(check_results) + 1
    check_results[result_id] = {
        'id': result_id,
        'user_id': session['user_id'],
        'type': 'proxy',
        'proxy': f"{host}:{port}",
        'proxy_type': proxy_type,
        'result': result,
        'checked_at': datetime.now().isoformat()
    }
    
    return jsonify(result)

@app.route('/api/batch-check', methods=['POST'])
def api_batch_check():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    items = data.get('items', [])
    check_type = data.get('type')
    
    if not items or not check_type:
        return jsonify({'error': 'Items and type required'}), 400
    
    job_id = f"batch_{int(time.time())}_{session['user_id']}"
    
    # Start background thread
    thread = threading.Thread(target=run_batch_check, args=(job_id, items, check_type))
    thread.daemon = True
    thread.start()
    
    return jsonify({'job_id': job_id})

@app.route('/api/batch-status/<job_id>')
def api_batch_status(job_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    job = batch_jobs.get(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    
    return jsonify(job)

@app.route('/api/provider-config/<email>')
def api_provider_config(email):
    """Get provider configuration for email domain"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    config = get_provider_config(email)
    return jsonify(config)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
