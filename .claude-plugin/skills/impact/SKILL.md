---
name: gosymdb:impact
description: Check what breaks before changing a Go symbol. Use BEFORE any refactor, rename, signature change, or deletion to understand the full transitive impact.
---

# impact — Pre-Change Impact Analysis

Always run this before modifying a symbol. Changing a signature without knowing its blast radius causes broken callers.

## Commands

```bash
# Full transitive impact — everything that breaks if this symbol changes
gosymdb blast-radius --symbol <fqname> --depth 5 --json

# Direct callers only (depth 1)
gosymdb callers --symbol <fqname> --json

# Where is this type used (assertions, switches, literals, conversions)?
gosymdb references --symbol <fqname> --json

# Dead code — safe to delete (no callers recorded)
gosymdb dead --pkg <pkg/path/prefix> --json
```

## Getting the fqname

Never hand-construct it. Get it from:

```bash
gosymdb find --q <name> --json   # candidates with fqname
gosymdb def <name> --json        # exact lookup
```

## Dead code caveats

`dead` reports symbols with no recorded call edges. Before deleting, verify with `callers` — a symbol may still be reached via interface dispatch, `reflect`, goroutine/defer indirection, or `go:linkname`. The `note` field in the `dead` response explains when this applies.

## Never manually replicate what built-ins answer

Do not loop `find` + `callers` to find dead code — use `dead`. Do not walk `callers` recursively for impact — use `blast-radius`. The built-in commands exist to avoid that work.
