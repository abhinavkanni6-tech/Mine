#!/usr/bin/env python3
import sys
import json
import time
import os
import importlib.util

# Robust import of main_Version5 by file path so runner works even if module isn't on sys.path
def load_main_module():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidate = os.path.join(script_dir, 'main_Version5.py')
    if os.path.isfile(candidate):
        spec = importlib.util.spec_from_file_location('main_Version5', candidate)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    # fallback to normal import (if package is installed or path set)
    try:
        import main_Version5 as m
        return m
    except Exception:
        raise ImportError(f"Could not find main_Version5.py at {candidate} and normal import failed")

m = load_main_module()

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
        me = m.get_me(token)
        if me and isinstance(me, dict) and me.get('id'):
            print('Token works as provided', flush=True)
            return token
    except Exception as e:
        print(f'Raw token check failed: {e}', flush=True)
    bot_token = token if token.startswith('Bot ') else f'Bot {token}'
    try:
        me = m.get_me(bot_token)
        if me and isinstance(me, dict) and me.get('id'):
            print('Token works when prefixed with "Bot "', flush=True)
            return bot_token
    except Exception as e:
        print(f'Bot-prefixed token check failed: {e}', flush=True)
    print('Warning: token normalization could not verify token; proceeding with original token', flush=True)
    return token

normalized = normalize_token(orig_token)

print(f"Starting NUKE runner for guild {guild_id}", flush=True)
try:
    m._sb_nuke(normalized, guild_id, reply, user_cfg)
    print('NUKE runner finished', flush=True)
except Exception as e:
    print('Error during nuke:', e, flush=True)
