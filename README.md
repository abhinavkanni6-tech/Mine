Simple web UI and Python runners for running main_Version5.py nuke/clone commands.

Files added:
- index.js (Express server startup)
- package.json
- run_nuke_web.py (reads JSON from stdin and calls _sb_nuke)
- run_clone_web.py (reads JSON and calls _sb_clone)
- public/* (frontend dark-themed UI)
- users.json (user store, default admin created)

Usage:
1. Install Node dependencies: npm install
2. Make sure you have python3 available and main_Version5.py is present in the same directory.
3. Start: npm start
4. Visit http://localhost:3000, login as admin/admin, create users, and run jobs.

Security: This is a minimal example for local use only. Do NOT expose a running server with tokens to the public.
