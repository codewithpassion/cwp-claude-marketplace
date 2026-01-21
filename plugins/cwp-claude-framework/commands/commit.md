---
name: cwp:commit
model: haiku
description: Creates a commit message and executes a commit. If 'all' is passed, it tell claude to include ALL changed files.
argument-hint: [all]
---

Create a commit for the current changes. 
If `$ARGUMENTS` is 'all' then make sure you include ALL changed files.