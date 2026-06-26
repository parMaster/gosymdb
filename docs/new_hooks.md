# Proposed Claude Code Hooks for gosymdb

## Background

This document captures the Claude Code enforcement hooks that emerged from a real incident and are bundled with the gosymdb plugin so every user gets them out of the box.

### The problem

Claude Code has a built-in session-level instruction to use the `Explore` subagent for broad codebase searches ("for broad codebase exploration that'll take more than 3 queries, spawn Agent with subagent_type=Explore"). The gosymdb plugin's own `CLAUDE.md` and skill descriptions explicitly override this with "NEVER use grep/rg/find — ALWAYS use gosymdb skills", but in practice Claude kept reaching for the Explore agent first. Memory and instructions alone are not reliable enough to override a built-in default: Claude can mis-prioritize competing instructions turn by turn.

A second pattern also appeared: Claude would run `gosymdb find ... --json | python3 -c "import sys,json; ..."` to parse results, even though the gosymdb skill documentation explicitly says *"never pipe gosymdb output to python, jq, or shell scripts — gosymdb commands return structured JSON, read it directly"*. Again, the rule existed but was not structurally enforced.

The fix for both: **hooks in `settings.json` that deny the tool call before it executes**, with a clear message pointing back to the correct approach. Hooks are enforced by the Claude Code harness, not by the model's attention, so they can't be overridden by competing instructions.

---

## Hook 1 — Block the Explore agent in Go projects

**File:** `~/.claude/hooks/block-explore-in-go.py`

```python
import json, sys, os, re

data = json.load(sys.stdin)
ti = data.get('tool_input', {})

# Only relevant for the Explore agent inside a Go module.
if ti.get('subagent_type') == 'Explore' and os.path.exists('go.mod'):
    text = '{} {}'.format(ti.get('description', ''), ti.get('prompt', '')).lower()

    # Signals that the exploration is hunting for Go symbols — the case
    # gosymdb handles. Word matches keep "interface" from firing on
    # unrelated prose while still catching the declaration keywords.
    symbol_intent = re.search(
        r'\b(func|funcs|type|types|interface|interfaces|struct|structs|'
        r'method|methods|receiver|symbol|symbols|caller|callers|callee|'
        r'callees|implementation|implementations|implements|signature|'
        r'definition|defined|declared)\b',
        text,
    ) is not None or '.go' in text

    if symbol_intent:
        print(json.dumps({
            'hookSpecificOutput': {
                'hookEventName': 'PreToolUse',
                'permissionDecision': 'deny',
                'permissionDecisionReason': (
                    'Go symbol lookup detected: use the gosymdb skills '
                    '(gosymdb:sym / gosymdb:trace / gosymdb:impact --auto-reindex) '
                    'instead of the Explore agent. See CLAUDE.md. '
                    '(General, non-symbol exploration of this repo is fine — '
                    'reword without Go-symbol terms.)'
                )
            }
        }))
```

**What it does:** Fires on every `Agent` tool call. If the requested subagent is `Explore`, a `go.mod` exists in the current working directory, **and** the prompt/description signals Go-symbol intent (declaration keywords, `method`/`caller`/`implementation`/`symbol`/`definition`, or a `.go` mention), the call is denied with a message redirecting to gosymdb skills. General, non-symbol exploration of a Go repo — docs, YAML/CI config, Dockerfiles, frontend — passes through. Non-Go projects and non-Explore agents are unaffected.

---

## Hook 2 — Block grep/rg for Go symbols

**File:** `~/.claude/hooks/block-go-symbol-grep.py`

```python
import json, sys, os, re

data = json.load(sys.stdin)
cmd = data.get('tool_input', {}).get('command', '')

# A content-search tool is being invoked (covers `git grep` too).
uses_search = re.search(r'\b(grep|egrep|fgrep|rg|ripgrep|ag)\b', cmd) is not None

# gosymdb output never needs grep; let those commands through.
if uses_search and 'gosymdb' not in cmd:
    targets_go = re.search(r'\.go\b', cmd) is not None or '*.go' in cmd
    decl = re.search(r'\b(func|type|interface|struct)\b', cmd) is not None
    in_go_project = os.path.exists('go.mod')

    # Block when grepping .go files directly, or searching for a Go
    # declaration keyword while inside a Go module. The go.mod gate keeps
    # this from firing on `grep type styles.css` in non-Go projects.
    if targets_go or (in_go_project and decl):
        print(json.dumps({
            'hookSpecificOutput': {
                'hookEventName': 'PreToolUse',
                'permissionDecision': 'deny',
                'permissionDecisionReason': (
                    'Do not use grep/rg/find to locate Go symbols. '
                    'Use the gosymdb skills instead (always with --auto-reindex):\n'
                    '  - gosymdb:sym    — find where a symbol is defined\n'
                    '  - gosymdb:trace  — definition + callers + callees\n'
                    '  - gosymdb:impact — blast radius before a refactor/deletion\n'
                    'See CLAUDE.md. If this is a plain text/comment/string search '
                    '(not a symbol lookup), narrow the pattern so it does not look '
                    'like a Go declaration.'
                )
            }
        }))
```

**What it does:** Fires on every `Bash` tool call. If the command invokes a content-search tool (`grep`/`egrep`/`fgrep`/`rg`/`git grep`/`ag`) and either targets `.go` files or searches for a Go declaration keyword (`func`/`type`/`interface`/`struct`) inside a Go module, the call is denied and redirected to gosymdb. The `go.mod` gate prevents false positives in non-Go projects (e.g. `grep type styles.css`). `gosymdb` commands are skipped so their output can still be filtered.

---

## Hook 3 — Block piping gosymdb output to python/jq

**File:** `~/.claude/hooks/block-gosymdb-pipe.py`

```python
import json, sys

data = json.load(sys.stdin)
cmd = data.get('tool_input', {}).get('command', '')

if 'gosymdb' in cmd and any(p in cmd for p in ['| python', '|python', '| jq', '|jq']):
    print(json.dumps({
        'hookSpecificOutput': {
            'hookEventName': 'PreToolUse',
            'permissionDecision': 'deny',
            'permissionDecisionReason': (
                'Do not pipe gosymdb output to python/jq. '
                'gosymdb returns structured JSON - read it directly. '
                'Use a different gosymdb subcommand that already answers the question.'
            )
        }
    }))
```

**What it does:** Fires on every `Bash` tool call. If the command string contains `gosymdb` and a pipe to `python`, `python3`, or `jq`, the call is denied. Plain `gosymdb` commands and unrelated bash pipelines are unaffected.

**Note on detection scope:** The check operates on the full raw command string, including any heredoc content embedded in the command. This is intentional — it catches all variants of the antipattern — but means that a Bash command whose source code contains both `gosymdb` and `| python` as string literals will also be blocked. This edge case is unlikely in real use.

---

## settings.json wiring

All three are `PreToolUse` hooks. They should be added to `~/.claude/settings.json` (global, so they apply to all Go projects):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/block-gosymdb-pipe.py",
            "statusMessage": "Checking gosymdb usage..."
          },
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/block-go-symbol-grep.py",
            "statusMessage": "Checking for Go symbol grep..."
          }
        ]
      },
      {
        "matcher": "Agent",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/block-explore-in-go.py",
            "statusMessage": "Checking agent type..."
          }
        ]
      }
    ]
  }
}
```

Merge these into any existing `hooks.PreToolUse` array — do not replace the whole object. `make install-hooks` (or `python3 install-hooks.py`) does this merge idempotently.

---

## Where this should live in the gosymdb plugin

The goal is for users who install the gosymdb plugin to get these hooks automatically, without manual `settings.json` editing. The two natural places in the plugin layout:

1. **Hook scripts** — ship `block-explore-in-go.py` and `block-gosymdb-pipe.py` as part of the plugin, installed to a known path (e.g. alongside the plugin's other assets).
2. **Plugin-provided hooks** — wire them via the plugin's settings contribution so they appear in the user's effective `PreToolUse` list on install.

The exact mechanism depends on how the gosymdb plugin currently contributes settings (check the plugin manifest / `.claude-plugin/` directory for the contribution point). The hook scripts themselves are plain Python 3, no dependencies beyond the stdlib.

---

## Why hooks and not CLAUDE.md rules

CLAUDE.md rules work when there is no competing built-in instruction. When a built-in default conflicts with a CLAUDE.md rule (as is the case here: built-in says "use Explore", CLAUDE.md says "use gosymdb"), the model can flip between them turn by turn. Hooks are enforced at the harness level and cannot be overridden by model attention, making them the right tool for mandatory, non-negotiable constraints.
