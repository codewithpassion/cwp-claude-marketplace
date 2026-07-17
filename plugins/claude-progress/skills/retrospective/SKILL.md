---
name: retrospective
description: >-
  Consolidate accumulated project knowledge into durable docs. Reviews
  PROGRESS.md and .claude/memory/, then promotes lasting lessons into
  CLAUDE.md/docs, prunes what's now obsolete, and commits. Use periodically
  or after a milestone to distill scattered notes into lasting guidance.
argument-hint: "[--force]"
---

# Retrospective

There's a lot of assembled knowledge in @PROGRESS.md and @.claude/memory/.
The goal of this session is to **distill it into durable form** — not just reflect.

## Steps

1. **Read** @PROGRESS.md and everything under @.claude/memory/. Cross-reference
   with existing @docs/ and the CLAUDE.md files.

2. **Sort each recurring lesson / decision** into one of:
   - **Promote** → a general, lasting rule or pattern that isn't written down yet
     → propose an edit to the right CLAUDE.md or a @docs/ page.
   - **Keep** → still relevant but project-episodic → leave in PROGRESS.md/memory.
   - **Prune** → already encoded in code/config, resolved, or superseded
     → remove/collapse it so the memory tree stays signal-dense.

3. **Dedup** overlapping notes that say the same thing in different words.

4. **Show the user the proposed changes** (promotions + prunes) before writing.
   Use the AskUserQuestion tool to confirm, unless '--force' is passed: "$ARGUMENTS".

5. **Apply** the approved edits and commit (e.g. `docs: retrospective — distill lessons`).

## Guardrails
- Prefer editing existing sections over adding new ones — no CLAUDE.md bloat.
- A promoted lesson must be general enough to apply beyond the one incident.
- When unsure whether something is durable, keep it — don't prune aggressively.
