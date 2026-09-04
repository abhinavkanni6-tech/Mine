# Notes added: systemd template and testing stub

I added a safe stub version of main_Version5.py to allow you to test the UI and
runner plumbing without connecting to Discord or performing destructive actions.

Files added:
- main_Version5.py (safe test stub)
- systemd/abhinav-tool.service.template (copy and edit paths/user before installing)

When you're ready to run against real Discord APIs, replace main_Version5.py with
your actual implementation and restart the server.
