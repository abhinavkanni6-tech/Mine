from flask import Flask, request, jsonify, session, redirect, send_from_directory, Response
import os
import json
import bcrypt
import uuid
import subprocess
import threading
import queue
import sys
from functools import wraps

# Configuration from env
ADMIN_USER = os.getenv('ADMIN_USER', 'admin')
ADMIN_PASS = os.getenv('ADMIN_PASS', 'admin')
SESSION_SECRET = os.getenv('SESSION_SECRET', 'change-this-secret')
PORT = int(os.getenv('PORT', '3000'))
PYTHON_CMD = os.getenv('PYTHON_CMD', sys.executable)

APP_DIR = os.path.dirname(os.path.abspath(__file__))
USERS_FILE = os.path.join(APP_DIR, 'users.json')
PUBLIC_DIR = os.path.join(APP_DIR, 'public')

# Create Flask app with explicit root_path/instance_path to avoid pkgutil issues in some hosts
app = Flask(__name__, static_folder='public', static_url_path='', root_path=APP_DIR, instance_path=APP_DIR)
app.secret_key = SESSION_SECRET

jobs = {}  # jobId -> { 'proc': Popen, 'queue': Queue }

# --- user store helpers ---
def load_users():
    try:
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {'users': []}


def save_users(db):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(db, f, indent=2)


# Ensure default admin from env
db = load_users()
if 'users' not in db:
    db = {'users': []}
if not any(u.get('username') == ADMIN_USER for u in db['users']):
    pw = ADMIN_PASS.encode('utf-8')
    hashed = bcrypt.hashpw(pw, bcrypt.gensalt()).decode('utf-8')
    db['users'].append({'username': ADMIN_USER, 'password': hashed, 'role': 'admin'})
    save_users(db)
    print(f"Created default admin user: {ADMIN_USER}")
else:
    print(f"Admin user {ADMIN_USER} already exists")


# --- auth decorators ---

def login_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not session.get('user'):
            return jsonify({'error': 'unauthenticated'}), 401
        return f(*args, **kwargs)
    return wrapped


def admin_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        u = session.get('user')
        if not u or u.get('role') != 'admin':
            return jsonify({'error': 'forbidden'}), 403
        return f(*args, **kwargs)
    return wrapped


# --- static routes ---
@app.route('/')
def index():
    return redirect('/login.html')

# static files served by Flask automatically from /public

# --- API routes ---
@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json or request.form
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'error': 'missing'}), 400
    db = load_users()
    user = next((u for u in db.get('users', []) if u.get('username') == username), None)
    if not user:
        return jsonify({'error': 'invalid'}), 400
    stored = user.get('password').encode('utf-8')
    if not bcrypt.checkpw(password.encode('utf-8'), stored):
        return jsonify({'error': 'invalid'}), 400
    session['user'] = {'username': user['username'], 'role': user.get('role', 'user')}
    return jsonify({'ok': True, 'user': session['user']})


@app.route('/api/logout', methods=['POST'])
@login_required
def api_logout():
    session.clear()
    return jsonify({'ok': True})


@app.route('/api/admin/create-user', methods=['POST'])
@admin_required
def api_create_user():
    data = request.json or request.form
    username = data.get('username')
    password = data.get('password')
    role = data.get('role') or 'user'
    if not username or not password:
        return jsonify({'error': 'missing'}), 400
    db = load_users()
    if any(u.get('username') == username for u in db.get('users', [])):
        return jsonify({'error': 'exists'}), 400
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    db['users'].append({'username': username, 'password': hashed, 'role': role})
    save_users(db)
    return jsonify({'ok': True})


@app.route('/api/whoami')
def api_whoami():
    return jsonify({'user': session.get('user')})


# --- Job runners and SSE ---

def start_python_job(script, payload):
    job_id = uuid.uuid4().hex
    q = queue.Queue()
    python_cmd = os.getenv('PYTHON_CMD', PYTHON_CMD)
    # Start subprocess
    proc = subprocess.Popen([python_cmd, script], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)

    # reader thread
    def _reader():
        try:
            for line in proc.stdout:
                q.put(line.rstrip('\n'))
        except Exception as e:
            q.put(f"ERROR reading process output: {e}")
        finally:
            proc.wait()
            q.put(None)  # sentinel

    t = threading.Thread(target=_reader, daemon=True)
    t.start()
    jobs[job_id] = {'proc': proc, 'queue': q}
    return job_id


@app.route('/api/run-nuke', methods=['POST'])
@login_required
def api_run_nuke():
    data = request.json or request.form
    token = data.get('token')
    guild_id = data.get('guild_id')
    cfg = data.get('cfg') or {}
    if not token or not guild_id:
        return jsonify({'error': 'missing token or guild_id'}), 400
    # payload is JSON sent to wrapper script via stdin
    payload = {'token': token, 'guild_id': guild_id, 'cfg': cfg}
    try:
        job_id = start_python_job(os.path.join(APP_DIR, 'run_nuke_web.py'), payload)
        return jsonify({'jobId': job_id})
    except Exception as e:
        return jsonify({'error': 'failed_to_start', 'detail': str(e)}), 500


@app.route('/api/run-clone', methods=['POST'])
@login_required
def api_run_clone():
    data = request.json or request.form
    token = data.get('token')
    src_id = data.get('src_id')
    dst_id = data.get('dst_id')
    if not token or not src_id or not dst_id:
        return jsonify({'error': 'missing'}), 400
    payload = {'token': token, 'src_id': src_id, 'dst_id': dst_id}
    try:
        job_id = start_python_job(os.path.join(APP_DIR, 'run_clone_web.py'), payload)
        return jsonify({'jobId': job_id})
    except Exception as e:
        return jsonify({'error': 'failed_to_start', 'detail': str(e)}), 500


@app.route('/api/stream/<job_id>')
@login_required
def api_stream(job_id):
    job = jobs.get(job_id)
    if not job:
        return "Not found", 404
    q = job['queue']

    def event_stream():
        while True:
            line = q.get()
            if line is None:
                yield f"event: end\ndata: done\n\n"
                break
            # Escape newlines handled per-line
            # Send as data: <line>\n\n
            # Replace any solitary CR/LF in line
            safe = line.replace('\r','')
            yield f"data: {safe}\n\n"

    return Response(event_stream(), mimetype='text/event-stream')


@app.route('/api/admin/users')
@admin_required
def api_list_users():
    db = load_users()
    users = [{'username': u['username'], 'role': u.get('role','user')} for u in db.get('users', [])]
    return jsonify({'users': users})


if __name__ == '__main__':
    print(f"Starting Flask server on 0.0.0.0:{PORT} (admin: {ADMIN_USER}, python: {PYTHON_CMD})")
    app.run(host='0.0.0.0', port=PORT)
