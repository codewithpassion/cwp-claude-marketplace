---
name: session-replay
description: >-
  Generate a self-contained HTML replay viewer of this project's Claude Code
  sessions. Use when the user wants to review, replay, or share what happened
  in past Claude Code sessions (prompts, tool calls, thinking, results) as an
  animated timeline.
argument-hint: "[optional: output path or 'main <session-id>']"
---

# Claude Code Session Replay

Generates `session-replay.html` — a single, self-contained HTML file with an
animated replay player for every Claude Code session of this project. No
server or dependencies needed; open it in any browser.

The viewer is styled as an Anthropic landing page (warm ivory shell, clay
accent, editorial serif) wrapping the replay in a Claude Code terminal window
(macOS chrome, monospace, green prompt/tool lines) — the conversation reads like
a live Claude Code session.

The player shows a session list (chronological), a per-session event timeline
(user prompts, slash commands, assistant text, thinking, tool calls, tool
results, advisor notes), playback controls with speed/seek, and a browsable
list of all user prompts.

Skill usage is tracked across both invocation paths and highlighted: skills the
**user** invokes (slash commands) and skills the **model** invokes (the `Skill`
tool) are styled distinctly in the timeline, tallied per session as chips in the
sidebar, and listed in a dedicated **Skills** tab (with user/model attribution
and click-to-seek). Built-in slash commands (`/model`, `/clear`, `/config`, …)
are excluded so the count reflects actual skills, not harness controls.

Token usage is shown at three levels: each assistant turn carries a chip with
its output tokens and context size at that point, each session lists its total
output tokens and peak context (sidebar + header), and the playback controls
keep a running output-token count as events are revealed.

The timeline also surfaces the richer data in the session logs:

- **Per-turn model** — each assistant turn shows which model produced it
  (Opus / Sonnet / Haiku / Fable, colour-coded), and each session shows a
  model-mix bar in the sidebar and the full split in the header.
- **Sub-agents** — `Agent`/`Task` calls render as a clickable card; opening it
  shows a modal with the sub-agent's type, model, wall-clock duration, total
  tokens, tool-call count, a read/bash/edit/lines± breakdown, its task prompt,
  and final output. (Sub-agent internal steps aren't in the logs, so this is a
  summary, not a replay.)
- **Real tool results** — `Edit` calls show the actual unified diff
  (colour-coded add/remove/hunk) in the expandable tool body.
- **Real elapsed time** — wall-clock gaps between turns appear as “⏱ N later”
  dividers, independent of the synthetic playback pacing.
- **Skill attribution** — beyond explicit invocations, the authoritative
  `attributionSkill` is shown per turn and tallied in the Skills tab as “active
  skill context”, catching auto-triggered skills the heuristic would miss; MCP
  tool calls carry a server-provenance badge.
- **Interruptions & plan mode** — “Request interrupted by user” and plan
  enter/exit appear as inline markers.
- **Permission mode** — each session's permission mode(s) (`bypassPermissions`,
  `auto`, `plan`, …) show as sidebar chips and in the header.
- **Hooks** — hook activity (PreToolUse, etc.) attaches to its tool call,
  hidden behind a “hooks” toggle in the controls (off by default).
- **Server tools** — web-search/fetch request counts are shown per session when
  present (absent in projects that never used them).

## Usage

Run the bundled script from the project root:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/session-replay/scripts/generate_replay.py"
```

Defaults:

- **Log directory**: derived from the current working directory using Claude
  Code's project slug rule (`~/.claude/projects/<slug>/`), so running from the
  repo root picks up this project's sessions automatically.
- **Output**: `./session-replay.html`
- **Title**: basename of the current directory.

Options:

| Flag | Purpose |
| --- | --- |
| `--out FILE` | Output HTML path |
| `--title TITLE` | Project name shown in the header |
| `--main-session ID` | Session id to badge as "MAIN BUILD" and open first |
| `--project-dir DIR` | Explicit JSONL log directory (overrides slug derivation) |

Example with all options:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/session-replay/scripts/generate_replay.py" \
  --out session-replay.html \
  --title "My Project" \
  --main-session 868e14f4-bc3e-4242-86e4-b7432c2e0466
```

## Workflow

1. Run the script (add `--title` with the product name if the directory
   basename isn't presentable).
2. Check the printed summary (session count, event totals) to confirm logs
   were found. If it exits with "No session log directory", pass
   `--project-dir` explicitly.
3. Send the generated HTML file to the user.

## Notes

- The script only needs the Python 3 standard library.
- Long content blocks are truncated in the embedded data (user prompts and
  goals are kept in full); sub-agent (sidechain) chatter is excluded from the
  timeline.
- The output file embeds session content — treat it as sensitive as the
  conversation itself before sharing.
