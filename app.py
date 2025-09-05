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

def check_email_account(email, password, protocol):
    """Real email account checking with actual server connections"""
    if '@' not in email:
        return {'status': 'invalid', 'message': 'Invalid email format'}
    
    domain = email.split('@')[1].lower()
    config = EMAIL_PROVIDERS.get(domain)
    
    if not config:
        return {'status': 'unsupported', 'message': f'Provider {domain} not supported'}
    
    protocol_config = config.get(protocol)
    if not protocol_config:
        return {'status': 'invalid', 'message': f'{protocol.upper()} not supported for {domain}'}
    
    try:
        if protocol == 'smtp':
            return check_smtp_connection(email, password, protocol_config)
        elif protocol == 'imap':
            return check_imap_connection(email, password, protocol_config)
        elif protocol == 'pop3':
            return check_pop3_connection(email, password, protocol_config)
        else:
            return {'status': 'invalid', 'message': f'Unknown protocol: {protocol}'}
            
    except Exception as e:
        logger.error(f"Email check error for {email}: {str(e)}")
        return {'status': 'error', 'message': f'Connection error: {str(e)}'}

def check_smtp_connection(email, password, config):
    """Check SMTP connection"""
    try:
        if config['ssl']:
            server = smtplib.SMTP_SSL(config['host'], config['port'], timeout=10)
        else:
            server = smtplib.SMTP(config['host'], config['port'], timeout=10)
            if config['port'] == 587:  # TLS
                server.starttls()
        
        server.login(email, password)
        server.quit()
        
        return {
            'status': 'success',
            'message': 'SMTP authentication successful',
            'provider': email.split('@')[1],
            'protocol': 'smtp',
            'server': f"{config['host']}:{config['port']}"
        }
        
    except smtplib.SMTPAuthenticationError:
        return {'status': 'failed', 'message': 'Authentication failed - invalid credentials'}
    except smtplib.SMTPConnectError:
        return {'status': 'failed', 'message': 'Connection failed - server unreachable'}
    except smtplib.SMTPServerDisconnected:
        return {'status': 'failed', 'message': 'Server disconnected unexpectedly'}
    except Exception as e:
        return {'status': 'error', 'message': f'SMTP error: {str(e)}'}

def check_imap_connection(email, password, config):
    """Check IMAP connection"""
    try:
        if config['ssl']:
            server = imaplib.IMAP4_SSL(config['host'], config['port'])
        else:
            server = imaplib.IMAP4(config['host'], config['port'])
        
        server.login(email, password)
        server.select('INBOX')
        server.close()
        server.logout()
        
        return {
            'status': 'success',
            'message': 'IMAP authentication successful',
            'provider': email.split('@')[1],
            'protocol': 'imap',
            'server': f"{config['host']}:{config['port']}"
        }
        
    except imaplib.IMAP4.error as e:
        if 'authentication failed' in str(e).lower():
            return {'status': 'failed', 'message': 'Authentication failed - invalid credentials'}
        return {'status': 'failed', 'message': f'IMAP error: {str(e)}'}
    except Exception as e:
        return {'status': 'error', 'message': f'IMAP connection error: {str(e)}'}

def check_pop3_connection(email, password, config):
    """Check POP3 connection"""
    try:
        if config['ssl']:
            server = poplib.POP3_SSL(config['host'], config['port'], timeout=10)
        else:
            server = poplib.POP3(config['host'], config['port'], timeout=10)
        
        server.user(email)
        server.pass_(password)
        server.stat()  # Test connection
        server.quit()
        
        return {
            'status': 'success',
            'message': 'POP3 authentication successful',
            'provider': email.split('@')[1],
            'protocol': 'pop3',
            'server': f"{config['host']}:{config['port']}"
        }
        
    except poplib.error_proto as e:
        if 'authentication failed' in str(e).lower() or 'invalid' in str(e).lower():
            return {'status': 'failed', 'message': 'Authentication failed - invalid credentials'}
        return {'status': 'failed', 'message': f'POP3 error: {str(e)}'}
    except Exception as e:
        return {'status': 'error', 'message': f'POP3 connection error: {str(e)}'}

def check_proxy_server(proxy_host, proxy_port, proxy_type, username=None, password=None):
    """Real proxy server checking with actual connections"""
    try:
        port = int(proxy_port)
        if port < 1 or port > 65535:
            return {'status': 'invalid', 'message': 'Invalid port number'}
    except ValueError:
        return {'status': 'invalid', 'message': 'Port must be a number'}
    
    try:
        if proxy_type.lower() in ['http', 'https']:
            return check_http_proxy(proxy_host, port, proxy_type, username, password)
        elif proxy_type.lower() in ['socks4', 'socks5']:
            return check_socks_proxy(proxy_host, port, proxy_type, username, password)
        else:
            return {'status': 'invalid', 'message': f'Unsupported proxy type: {proxy_type}'}
            
    except Exception as e:
        logger.error(f"Proxy check error for {proxy_host}:{port}: {str(e)}")
        return {'status': 'error', 'message': f'Connection error: {str(e)}'}

def check_http_proxy(host, port, proxy_type, username=None, password=None):
    """Check HTTP/HTTPS proxy"""
    import requests
    
    try:
        # Build proxy URL
        if username and password:
            proxy_url = f"http://{username}:{password}@{host}:{port}"
        else:
            proxy_url = f"http://{host}:{port}"
        
        proxies = {
            'http': proxy_url,
            'https': proxy_url
        }
        
        # Test proxy with a request to httpbin.org
        test_url = 'http://httpbin.org/ip' if proxy_type.lower() == 'http' else 'https://httpbin.org/ip'
        
        start_time = time.time()
        response = requests.get(test_url, proxies=proxies, timeout=10)
        response_time = round((time.time() - start_time) * 1000, 2)
        
        if response.status_code == 200:
            try:
                data = response.json()
                proxy_ip = data.get('origin', 'Unknown')
                
                return {
                    'status': 'success',
                    'message': f'{proxy_type.upper()} proxy is working',
                    'response_time': f'{response_time}ms',
                    'type': proxy_type,
                    'proxy_ip': proxy_ip,
                    'server': f"{host}:{port}"
                }
            except:
                return {
                    'status': 'success',
                    'message': f'{proxy_type.upper()} proxy is working',
                    'response_time': f'{response_time}ms',
                    'type': proxy_type,
                    'server': f"{host}:{port}"
                }
        else:
            return {'status': 'failed', 'message': f'Proxy returned status code: {response.status_code}'}
            
    except requests.exceptions.ProxyError:
        return {'status': 'failed', 'message': 'Proxy connection failed - authentication or connectivity issue'}
    except requests.exceptions.ConnectTimeout:
        return {'status': 'failed', 'message': 'Connection timeout - proxy server unreachable'}
    except requests.exceptions.ReadTimeout:
        return {'status': 'failed', 'message': 'Read timeout - proxy server too slow'}
    except Exception as e:
        return {'status': 'error', 'message': f'HTTP proxy error: {str(e)}'}

def check_socks_proxy(host, port, proxy_type, username=None, password=None):
    """Check SOCKS4/SOCKS5 proxy"""
    try:
        # Test basic TCP connection to proxy
        start_time = time.time()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        
        result = sock.connect_ex((host, port))
        response_time = round((time.time() - start_time) * 1000, 2)
        
        if result == 0:
            sock.close()
            
            # For SOCKS5, try to test with requests library if available
            if proxy_type.lower() == 'socks5':
                try:
                    import requests
                    
                    if username and password:
                        proxy_url = f"socks5://{username}:{password}@{host}:{port}"
                    else:
                        proxy_url = f"socks5://{host}:{port}"
                    
                    proxies = {
                        'http': proxy_url,
                        'https': proxy_url
                    }
                    
                    test_response = requests.get('http://httpbin.org/ip', proxies=proxies, timeout=10)
                    if test_response.status_code == 200:
                        try:
                            data = test_response.json()
                            proxy_ip = data.get('origin', 'Unknown')
                            return {
                                'status': 'success',
                                'message': f'{proxy_type.upper()} proxy is working',
                                'response_time': f'{response_time}ms',
                                'type': proxy_type,
                                'proxy_ip': proxy_ip,
                                'server': f"{host}:{port}"
                            }
                        except:
                            pass
                except:
                    pass
            
            return {
                'status': 'success',
                'message': f'{proxy_type.upper()} proxy connection successful',
                'response_time': f'{response_time}ms',
                'type': proxy_type,
                'server': f"{host}:{port}"
            }
        else:
            sock.close()
            return {'status': 'failed', 'message': f'Connection failed to {host}:{port}'}
            
    except socket.timeout:
        return {'status': 'failed', 'message': 'Connection timeout'}
    except socket.gaierror:
        return {'status': 'failed', 'message': 'DNS resolution failed'}
    except Exception as e:
        return {'status': 'error', 'message': f'SOCKS proxy error: {str(e)}'}

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
            result = None
            if check_type == 'email':
                result = check_email_account(item['email'], item['password'], item.get('protocol', 'smtp'))
                result['email'] = item['email']
            elif check_type == 'proxy':
                result = check_proxy_server(item['host'], item['port'], item.get('type', 'http'), item.get('username'), item.get('password'))
                result['proxy'] = f"{item['host']}:{item['port']}"
            
            if result:
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
        successful = sum(1 for r in user_results if r.get('result', {}).get('status') == 'success')
        stats['success_rate'] = round((successful / len(user_results)) * 100.0, 1)
    
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
    result = check_email_account(email, password, protocol)
    
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
    
    result = check_proxy_server(host, port, proxy_type, data.get('username'), data.get('password'))
    
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
