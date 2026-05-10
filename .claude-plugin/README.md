# gosymdb Claude Code Plugin

Three focused skills that replace grep for Go code navigation in Claude Code.

## Skills

| Skill | Trigger | What it does |
|-------|---------|--------------|
| `gosymdb:sym` | Finding where a symbol is defined | Looks up functions, types, methods, interfaces by name |
| `gosymdb:trace` | Investigating how a symbol fits in the codebase | Definition + callers + callees + implementors in one sequence |
| `gosymdb:impact` | Before any refactor, rename, or deletion | Blast radius, dead code detection, type references |

## Requirements

- [gosymdb](https://github.com/walkindude/gosymdb) installed and on `PATH`
- A built index in your Go project: `gosymdb index --root .`

## Installation

**1. Add this repo as a marketplace:**

```
/plugin marketplace add parMaster/gosymdb
```

**2. Install the plugin:**

```
/plugin install gosymdb@gosymdb
```

**3. Allow gosymdb commands without approval prompts** (recommended):

Add to `~/.claude/settings.json`:

```json
{
  "permissions": {
    "allow": ["Bash(gosymdb *)"]
  }
}
```

**4. Reload:**

```
/reload-plugins
```

The three skills (`gosymdb:sym`, `gosymdb:trace`, `gosymdb:impact`) are now active globally across all projects.

## Usage

The skills trigger automatically when Claude Code navigates Go code. You can also invoke them explicitly:

```
/gosymdb:sym
/gosymdb:trace
/gosymdb:impact
```

## Building the index

In any Go project:

```bash
gosymdb index --root .
```

The index is stored as `gosymdb.sqlite` in the project root and auto-discovered by all commands. Re-index after significant changes, or pass `--auto-reindex` to any query to refresh stale packages on the fly.
