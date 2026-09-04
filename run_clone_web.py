#!/usr/bin/env python3
import sys
import json
import time
import main_Version5 as m

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
