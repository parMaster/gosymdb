#!/usr/bin/env python3
"""
Install gosymdb Claude Code hooks.

Copies hook scripts to ~/.claude/hooks/ and wires them into
~/.claude/settings.json as PreToolUse hooks.

Safe to run multiple times — skips steps that are already done.
"""

import json
import shutil
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
HOOKS_SRC  = SCRIPT_DIR / ".claude-plugin" / "hooks"
HOOKS_DST  = Path.home() / ".claude" / "hooks"
SETTINGS   = Path.home() / ".claude" / "settings.json"

HOOK_ENTRIES = [
    {
        "matcher":       "Bash",
        "script":        "block-gosymdb-pipe.py",
        "command":       "python3 ~/.claude/hooks/block-gosymdb-pipe.py",
        "statusMessage": "Checking gosymdb usage...",
    },
    {
        "matcher":       "Bash",
        "script":        "block-go-symbol-grep.py",
        "command":       "python3 ~/.claude/hooks/block-go-symbol-grep.py",
        "statusMessage": "Checking for Go symbol grep...",
    },
    {
        "matcher":       "Agent",
        "script":        "block-explore-in-go.py",
        "command":       "python3 ~/.claude/hooks/block-explore-in-go.py",
        "statusMessage": "Checking agent type...",
    },
]


def copy_scripts():
    HOOKS_DST.mkdir(parents=True, exist_ok=True)
    for entry in HOOK_ENTRIES:
        src = HOOKS_SRC / entry["script"]
        dst = HOOKS_DST / entry["script"]
        if dst.exists() and dst.read_bytes() == src.read_bytes():
            print(f"  skip  {dst}  (unchanged)")
        else:
            shutil.copy2(src, dst)
            print(f"  copy  {dst}")


def merge_settings():
    settings = json.loads(SETTINGS.read_text()) if SETTINGS.exists() else {}

    hooks = settings.setdefault("hooks", {})
    pre   = hooks.setdefault("PreToolUse", [])

    changed = False
    for entry in HOOK_ENTRIES:
        block = next((b for b in pre if b.get("matcher") == entry["matcher"]), None)
        if block is None:
            block = {"matcher": entry["matcher"], "hooks": []}
            pre.append(block)
            changed = True

        cmd = entry["command"]
        if cmd not in [h.get("command") for h in block.get("hooks", [])]:
            block.setdefault("hooks", []).append({
                "type":          "command",
                "command":       cmd,
                "statusMessage": entry["statusMessage"],
            })
            changed = True
            print(f"  wire  {entry['matcher']} -> {cmd}")
        else:
            print(f"  skip  {entry['matcher']} hook  (already wired)")

    if changed:
        SETTINGS.write_text(json.dumps(settings, indent=2) + "\n")
        print(f"  save  {SETTINGS}")
    else:
        print(f"  skip  {SETTINGS}  (no changes)")


def main():
    print("gosymdb: installing Claude Code hooks\n")
    print("Hook scripts:")
    copy_scripts()
    print("\nsettings.json:")
    merge_settings()
    print("\nDone. Restart Claude Code to activate the hooks.")


if __name__ == "__main__":
    main()
