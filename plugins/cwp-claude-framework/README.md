# cwp-claude-framework

Personal toolkit of reusable Claude Code commands and utilities.

## Installation

```bash
# Option 1: Use directly with Claude Code
claude --plugin-dir /path/to/cwp-claude-framework

# Option 2: Add to a marketplace
# Add entry to marketplace.json pointing to this plugin
```

## Commands

| Command | Description |
|---------|-------------|
| `/cwp:commit [all]` | Creates a commit message and executes a commit. Pass `all` to include all changed files. |
| `/cwp:prime [files]` | Primes context by reading README, CLAUDE.md, package.json, and optionally specified files. |
| `/cwp:implement [prompt] [--parallel] [--background]` | Implementation coordinator that spawns coder subagents. Use `--parallel` for multiple agents, `--background` for async execution. |

## Command Details

### /cwp:commit
Quick commit helper that generates a commit message based on staged changes.
- Uses Haiku model for speed
- Pass `all` to include all changed files in the commit

### /cwp:prime
Loads project context into the conversation by reading key files:
- README files
- CLAUDE.md
- package.json
- ai_docs/rules.md (if exists)
- Any additional files you specify

### /cwp:implement
Full-featured implementation coordinator for complex tasks:
- Reads CLAUDE.md/README to discover project-specific check commands
- Spawns subagents to implement tasks
- `--parallel`: Use 2-5 parallel coder agents for independent tasks
- `--background`: Run agents asynchronously (non-blocking)
- Enforces quality gates (type checks, linting, tests)
- Updates task files with completion checkboxes

## Structure

```
cwp-claude-framework/
├── .claude-plugin/
│   └── plugin.json          # Plugin manifest
├── commands/                 # User-invocable commands
│   ├── commit.md
│   ├── prime.md
│   └── implement.md
└── README.md
```

## Adding More Components

- **Commands**: Create new `.md` files in `commands/`
- **Skills**: Create `skills/<skill-name>/SKILL.md` for knowledge/guidance
- **Agents**: Create `agents/<agent>.md` for autonomous tasks
- **Hooks**: Create `hooks/hooks.json` for event-driven automation
