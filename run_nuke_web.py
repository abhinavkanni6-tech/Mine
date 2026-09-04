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

orig_token = cfg.get('token')
guild_id = cfg.get('guild_id')
user_cfg = cfg.get('cfg') or {}

# reply callback prints to stdout
def reply(msg):
    print(msg, flush=True)

# Normalize token: try raw token, then try with "Bot " prefix if raw fails
def normalize_token(token):
    if not token:
        return token
    try:
        # Try raw token
        me = m.get_me(token)
        if me and isinstance(me, dict) and me.get('id'):
            print('Token works as provided', flush=True)
            return token
    except Exception as e:
        print(f'Raw token check failed: {e}', flush=True)
    # Try with Bot prefix
    bot_token = token if token.startswith('Bot ') else f'Bot {token}'
    try:
        me = m.get_me(bot_token)
        if me and isinstance(me, dict) and me.get('id'):
            print('Token works when prefixed with "Bot "', flush=True)
            return bot_token
    except Exception as e:
        print(f'Bot-prefixed token check failed: {e}', flush=True)
    # As a last attempt, return original token and proceed; calls may fail but we log it
    print('Warning: token normalization could not verify token; proceeding with original token', flush=True)
    return token

normalized = normalize_token(orig_token)

print(f"Starting NUKE runner for guild {guild_id}", flush=True)
try:
    m._sb_nuke(normalized, guild_id, reply, user_cfg)
    print('NUKE runner finished', flush=True)
except Exception as e:
    print('Error during nuke:', e, flush=True)
