# cwp-claude-progress

Keeps a `PROGRESS.md` work log up to date automatically, plus skills for capturing and distilling what you learn across sessions.

> **Prerequisite:** A `PROGRESS.md` file must exist in the project root. Without it the Stop hook does nothing — create an empty `PROGRESS.md` to opt in.

## Installation

```bash
# Option 1: Use directly with Claude Code
claude --plugin-dir /path/to/claude-progress

# Option 2: Add via the marketplace
# The cwp-claude-marketplace already lists this plugin
```

## What it does

### Automatic progress log (Stop hook)
At the end of each session, if a `PROGRESS.md` exists and you made meaningful code changes, the plugin appends a brief timestamped entry (date, what changed, suggested next steps). Q&A-only or exploration sessions are skipped, and existing entries are never rewritten.

### Skills

| Skill | Description |
|-------|-------------|
| `/progress [cycle title]` | Add a structured entry for the current implementation cycle — goal, what we did, lessons learned, pitfalls to avoid. Reverse-chronological, proposes the draft before writing. |
| `/remember` | Capture important decisions and findings from the session into private memory, and persist them to `./.claude/memory/` for future work on the project. |
| `/retrospective [--force]` | Consolidate accumulated knowledge in `PROGRESS.md` and `.claude/memory/` — promote lasting lessons into `CLAUDE.md`/`docs/`, prune what's obsolete, then commit. |

## Structure

```
claude-progress/
├── .claude-plugin/
│   └── plugin.json              # Manifest + Stop hook
├── skills/
│   ├── progress/SKILL.md
│   ├── remember/SKILL.md
│   └── retrospective/SKILL.md
└── README.md
```
