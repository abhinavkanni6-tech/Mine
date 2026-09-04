"""Stub main_Version5.py for safe local testing.

This file provides lightweight, non-destructive implementations of the
functions the web UI expects so you can test the dashboard and runner
without needing the real destructive Discord code.

- get_me(token) -> dict
- _sb_nuke(token, guild_id, reply, cfg) -> prints simulated steps via reply()
- _sb_clone(token, src_id, dst_id, reply) -> prints simulated steps via reply()

Replace this file with your real main_Version5.py when you're ready to
run actual Discord operations.
"""

import json
import time
import sys
from typing import Dict, Any


def get_me(token: str) -> Dict[str, Any]:
    """Return a minimal 'me' object for a token. This is a harmless stub.
    If token is falsy return None to signal failure."""
    if not token:
        raise Exception("No token provided")
    # Accept both "Bot <token>" and raw token for testing.
    t = token
    if t.startswith("Bot "):
        t = t[4:]
    return {"id": "100000000000000000", "username": "testbot", "token_preview": t[:8]}


def _sb_nuke(token: str, guild_id: str, reply, cfg: Dict[str, Any]):
    """Simulate a nuke run. This does NOT contact Discord.
    It prints progress messages through the reply callback so the UI can
    display output. Use this for testing the UI and runner plumbing.
    """
    reply(f"[stub] Starting simulated nuke on guild {guild_id}")
    time.sleep(0.2)

    # Show token check
    try:
        me = get_me(token)
        reply(f"[stub] Authenticated as {me['username']} (id={me['id']})")
    except Exception as e:
        reply(f"[stub][ERROR] Token check failed: {e}")
        return

    # Simulate deleting channels/roles
    if cfg.get('delete'):
        reply("[stub] Deleting channels and roles...")
        for i in range(min(5, cfg.get('ch_count', 5))):
            reply(f"[stub] Deleted channel #{i+1}")
            time.sleep(0.05)

    # Simulate creating channels
    if cfg.get('create'):
        reply(f"[stub] Creating {cfg.get('ch_count', 5)} channels named {cfg.get('ch_name','nuked')}")
        for i in range(cfg.get('ch_count', 5)):
            reply(f"[stub] Created channel: {cfg.get('ch_name','nuked')}-{i+1}")
            time.sleep(0.02)

    # Simulate spamming
    if cfg.get('spam'):
        spam_msg = cfg.get('spam_msg', '@everyone')
        count = cfg.get('spam_count', 3)
        reply(f"[stub] Spamming message {count} times: {spam_msg}")
        for i in range(count):
            reply(f"[stub] Spam #{i+1}: {spam_msg}")
            time.sleep(0.02)

    # Simulate bans
    if cfg.get('ban'):
        reply("[stub] Banning members (simulated)...")
        # pretend to ban 3 members
        for i in range(3):
            reply(f"[stub] Banned user id: 2000000000{i}")
            time.sleep(0.03)

    reply("[stub] Simulated nuke finished")


def _sb_clone(token: str, src_id: str, dst_id: str, reply):
    reply(f"[stub] Starting simulated clone from {src_id} to {dst_id}")
    try:
        me = get_me(token)
        reply(f"[stub] Authenticated as {me['username']} (id={me['id']})")
    except Exception as e:
        reply(f"[stub][ERROR] Token check failed: {e}")
        return
    time.sleep(0.2)
    reply("[stub] Copying roles...")
    time.sleep(0.05)
    reply("[stub] Copying channels...")
    time.sleep(0.05)
    reply("[stub] Copying settings...")
    time.sleep(0.05)
    reply("[stub] Simulated clone finished")


# If this file is executed directly, allow quick manual testing
if __name__ == '__main__':
    try:
        cfg = json.load(sys.stdin)
    except Exception:
        print("ERROR: supply JSON on stdin (token/guild_id/cfg) for a quick test")
        sys.exit(1)
    token = cfg.get('token')
    guild_id = cfg.get('guild_id')
    def _r(m):
        print(m)
    _sb_nuke(token, guild_id, _r, cfg.get('cfg', {}))
