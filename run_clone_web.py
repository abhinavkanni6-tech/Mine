#!/usr/bin/env python3
import sys
import json
import time
import os
import importlib.util

# Robust import of main_Version5 by file path
def load_main_module():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidate = os.path.join(script_dir, 'main_Version5.py')
    if os.path.isfile(candidate):
        spec = importlib.util.spec_from_file_location('main_Version5', candidate)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    try:
        import main_Version5 as m
        return m
    except Exception:
        raise ImportError(f"Could not find main_Version5.py at {candidate} and normal import failed")

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
