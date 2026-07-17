---
name: progress
description: >-
  Update PROGRESS.md with a new entry for the current implementation cycle.
  Use at the end of a work session to log what was done, lessons learned, and pitfalls to avoid.
argument-hint: "[optional: cycle title]"
context: fork
---

# Update Progress Log

You are updating `PROGRESS.md` at the project root. 

## Purpose

`PROGRESS.md` is a reverse-chronological log of implementation cycles in the project. It serves as a shared memory between the developer and AI assistant across sessions — capturing what was done, what went wrong, and what to avoid next time.

## Why

- Git history tells you **what** changed. Progress entries tell you **why**, what the intent was, what tripped us up, and what we'd do differently.
- Lessons learned prevent the same mistakes across sessions (especially with AI assistants that don't retain memory of debugging loops).
- Reverse-chronological order keeps the most relevant context at the top.

## Entry Format

Each entry follows this structure:

```markdown
## Cycle N — Short Title (YYYY-MM-DD)

**Goal:** One sentence describing the objective.

**What we did:**
- Bullet list of concrete outcomes (commits, files created, decisions made)

**Lessons learned:**
- Things that caused errors, cost time, or surprised us

**Avoid next time:**
- Specific anti-patterns or pitfalls to watch for
```

## Rules

1. **One entry per implementation cycle** — a cycle is a focused session with a clear goal (e.g., "set up testing", "build auth layer", "add design system").
2. **Reverse chronological** — newest entry at the top, just below the header.
3. **Be specific** — "Biome formatting broke because we used spaces" is useful. "Had some formatting issues" is not.
4. **No filler** — skip entries where nothing interesting happened. Not every commit needs an entry.
5. **Keep it honest** — include mistakes and dead ends. That's the whole point.


## Steps

1. **Read the current first 20 lines of `PROGRESS.md`** (or more if needed) to determine the next cycle number and avoid duplicating content.

2. **Review what happened this session.** Use these sources:
   - `git log --oneline` — commits since the last progress entry
   - `git diff` of changed files for context
   - Your conversation history — decisions made, errors hit, things that worked

3. **Draft a new entry** using the above format.

4. **Insert the new entry** immediately below the `---` separator after the header block in `PROGRESS.md` (before existing entries — newest first).

5. **Show the user the draft** before writing. Use the 'AskUserQuestion' tool to let the user approve or adjust unless the user specifies '--force' in the arguments: "$ARGUMENTS".

6. **Write the approved entry** to `PROGRESS.md` and commit with a message like `docs: update progress log for cycle N`.

## Guidelines

- Use today's date. The current date is available in conversation context.
- If no cycle title was provided via `$ARGUMENTS`, infer one from the work done.
- Be specific and honest — vague entries are useless. Name files, error messages, and tools.
- Only log cycles where something meaningful happened. Don't log trivial one-off changes.
- Keep each entry concise: 3-8 bullets per section. Not a commit log — synthesize.
- Include errors and dead ends. That's the most valuable part for future sessions.
