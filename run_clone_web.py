#!/usr/bin/env python3
import sys
import json
import time
import os
import importlib.util

# Robust import of main_Version5 by searching multiple candidate locations.
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
    try:
        import main_Version5 as m
        print("Imported main_Version5 via normal import", flush=True)
        return m
    except Exception:
        raise ImportError(f"Could not find main_Version5.py in candidates: {find_candidate_paths()}")

m = load_main_module()

try:
    cfg = json.load(sys.stdin)
except Exception:
    print('ERROR: no config provided', flush=True)
    sys.exit(1)

token = cfg.get('token')
src_id = cfg.get('src_id')
dst_id = cfg.get('dst_id')

def reply(msg):
    print(msg, flush=True)

print(f"Starting CLONE runner {src_id} -> {dst_id}", flush=True)
try:
    m._sb_clone(token, src_id, dst_id, reply)
    print('CLONE runner finished', flush=True)
except Exception as e:
    print('Error during clone:', e, flush=True)
