Flask web server (Python) for the Abhinav Discord Tool

This replaces the previous Node.js server and serves the UI in /public, handles admin/user auth,
starts Python runner scripts (run_nuke_web.py, run_clone_web.py), and streams process output via SSE.

Usage (example):

1. Install dependencies (create virtualenv recommended):
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt

2. Set environment variables (or copy .env.example -> .env and export):
   export ADMIN_USER=admin
   export ADMIN_PASS=admin
   export SESSION_SECRET='a-long-random-secret'
   export PORT=3000
   export PYTHON_CMD=python3   # optional

3. Ensure main_Version5.py, run_nuke_web.py, run_clone_web.py exist in the repo root.

4. Start the server:
   python index.py

5. Open http://HOST:PORT/login.html and login with ADMIN_USER/ADMIN_PASS

Security: Use only in a controlled environment. The tool will execute destructive Discord actions if supplied with real tokens.
