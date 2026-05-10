---
name: gosymdb:trace
description: Full profile of a Go symbol — definition, callers, callees, and blast radius in one sequence. Use BEFORE reading source files when investigating how a symbol fits into the codebase.
---

# trace — Full Symbol Profile

Run this sequence to fully understand a symbol before reading source. Faster and more complete than browsing files.

## Sequence

```bash
# 1. Get the fqname (never guess it)
gosymdb find --q <name> --json

# 2. Confirm definition — file, line, signature
gosymdb def <name> --json

# 3. Who calls it?
gosymdb callers --symbol <fqname> --json

# 4. What does it call?
gosymdb callees --symbol <fqname> --json

# 5. If it's an interface — what implements it?
gosymdb implementors --iface <name> --json
```

Use the `fqname` from step 1 in all subsequent commands.

## Interface dispatch gap

`callers` only records direct calls — calls through an interface variable are not captured. If `callers` returns 0 for an interface method, the `hint` field will flag it. Recovery: `implementors --iface <name>` to find concrete types, then `callers` on the concrete method.

## Stale index

Every response includes `env.stale_packages`. If non-empty, results may be incomplete. Pass `--auto-reindex` to any query to fix before it runs:

```bash
gosymdb callers --symbol <fqname> --auto-reindex --json
```
