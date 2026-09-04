#!/usr/bin/env python3
import sys
import json
import time

# Import the provided script as a module
import main_Version5 as m

# Read JSON config from stdin
try:
    cfg = json.load(sys.stdin)
except Exception:
    print('ERROR: no config provided', flush=True)
    sys.exit(1)

token = cfg.get('token')
guild_id = cfg.get('guild_id')
user_cfg = cfg.get('cfg') or {}

# reply callback prints to stdout
def reply(msg):
    print(msg, flush=True)

print(f"Starting NUKE runner for guild {guild_id}", flush=True)
try:
    m._sb_nuke(token, guild_id, reply, user_cfg)
    print('NUKE runner finished', flush=True)
except Exception as e:
    print('Error during nuke:', e, flush=True)

