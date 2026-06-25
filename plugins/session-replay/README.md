# cwp-session-replay

Generate a self-contained HTML replay viewer of a project's Claude Code sessions.

The viewer is a single, dependency-free HTML file with an animated replay player
for every Claude Code session of the project — user prompts, slash commands,
assistant text, thinking, tool calls, tool results, skill usage, and token usage,
all on a seekable timeline. Open it in any browser; no server required.

## Usage

The plugin ships a `session-replay` skill. Ask Claude to "replay" or "create a
replay of this project's Claude Code sessions", or run the bundled script
directly from the project root:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/session-replay/scripts/generate_replay.py"
```

Only the Python 3 standard library is required.

## Notes

The output file embeds session content — treat it as sensitive as the
conversation itself before sharing.
