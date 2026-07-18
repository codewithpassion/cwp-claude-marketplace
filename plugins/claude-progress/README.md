# cwp-claude-progress

Keeps a `PROGRESS.md` work log up to date via the `/progress` skill, plus skills for capturing and distilling what you learn across sessions.

> **Prerequisite:** A `PROGRESS.md` file must exist in the project root. Create an empty `PROGRESS.md` to start a work log.

## Installation

```bash
# Option 1: Use directly with Claude Code
claude --plugin-dir /path/to/claude-progress

# Option 2: Add via the marketplace
# The cwp-claude-marketplace already lists this plugin
```

## What it does

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
│   └── plugin.json              # Manifest
├── skills/
│   ├── progress/SKILL.md
│   ├── remember/SKILL.md
│   └── retrospective/SKILL.md
└── README.md
```
