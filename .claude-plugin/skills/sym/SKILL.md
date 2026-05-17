---
name: gosymdb:sym
description: Find where a Go symbol is defined. Use PROACTIVELY and INSTEAD of grep/rg/find whenever looking for where a function, type, method, or interface is defined, declared, or located in a Go codebase.
---

# sym — Find a Go Symbol

Use gosymdb, not grep. Grep finds string occurrences; gosymdb finds the resolved symbol with its fully-qualified name, file, and line.

## Commands

```bash
# Search by name (partial match, returns all candidates)
gosymdb find --q <name> --json

# Exact single-symbol lookup
gosymdb def <name> --json

# All symbols in a package
gosymdb find --pkg <pkg/path> --json

# All symbols in a file
gosymdb find --file <path/to/file.go> --json

# Filter by kind: func, type, interface, var, const, method
gosymdb find --q <name> --kind func --json
```

## Getting a reliable fqname

The `fqname` field in results is what other gosymdb commands require. Never hand-construct it — package paths and method-receiver formatting are easy to get wrong. Always get it from `find` or `def` output.

## Never pipe gosymdb output to python, jq, or shell scripts

gosymdb commands return structured JSON — read the fields directly. Never pipe to `python3`, `jq`, or a shell loop to extract or transform results. If you find yourself doing that, there is a gosymdb command that already answers the question directly.

## If the index is missing

```bash
gosymdb index --root .
gosymdb agent-context  # confirms db path
```
