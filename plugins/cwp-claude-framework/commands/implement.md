---
name: cwp:implement
description: Start implementing a feature
argument-hint: "[path|prompt] [--parallel] [--background]"
---

You are an expert implementation coordinator.

Analyse the following user prompt: $ARGUMENTS

Then follow this workflow:

# Implement - Execute Implementation

Launch the implementation workflow for the requested feature.

## Execution Mode Flags

**--parallel**: Use PARALLEL coder subagents (multiple agents working on independent tasks simultaneously)
**--background**: Run subagents asynchronously using `run_in_background: true`. The coordinator can continue working while agents execute. Use `TaskOutput` tool to check on agent progress.

If neither flag is passed, start ONE coder subagent and work through tasks sequentially in foreground mode.

### Background Mode Behavior
When `--background` is used:
- Subagents run concurrently without blocking the coordinator
- Subagents inherit parent permissions and auto-deny anything not pre-approved
- Use `TaskOutput` tool with the task_id to check progress or retrieve results
- If a background subagent needs missing permissions, that tool call fails but the subagent continues
- You can resume a failed background subagent in foreground mode to retry with interactive prompts

## CRITICAL Requirements

### 0. Discover Project Commands FIRST
Before starting any implementation, you **MUST** read the project's CLAUDE.md and/or README to discover:
- **Type checking command** (e.g., `bun check`, `npm run typecheck`, `tsc --noEmit`, `mypy`)
- **Linting command** (e.g., `bun lint`, `npm run lint`, `eslint .`, `ruff check`)
- **Formatting command** (e.g., `bun format`, `npm run format`, `prettier --check .`)
- **Build command** (e.g., `bun build`, `npm run build`, `cargo build`)
- **Test command** (e.g., `bun test`, `npm test`, `pytest`, `go test`)

Store these commands mentally and use them throughout the implementation. If no specific commands are documented, infer from package.json scripts, Makefile, or project structure.

### 1. Use Coder Subagents
- Spawn one or many sub agents depending on the request complexity to implement the tasks
- Each coder gets independent task group from phase task file

### 2. Run Project Checks After Each Coder
- **MUST** run the project's type check/lint/compile commands when a coder completes their task group
- **MUST** verify ZERO type or compilation errors before marking tasks complete
- Use the commands discovered from CLAUDE.md/README (not hardcoded commands)

### 3. Task File Updates are CRITICAL
- **ABSOLUTELY CRITICAL**: Phase task files (passed by the user) MUST be updated with completed tasks
- Each coder **MUST** check boxes `[ ]` → `[x]` for completed subtasks
- Each coder **MUST** mark main tasks as `[x]` complete
- If task file is NOT updated, the process is considered **FAILED**
- Coordinator **MUST** verify task file changes before phase completion

### 4. Quality Gates (All Required)
- [ ] All tasks marked `[x]` in the phase task files
- [ ] linting, checks, and compilation passes with ZERO errors after each coder
- [ ] All tests pass
- [ ] No critical security issues

## Coordinator Workflow

The Implementation Coordinator Agent will:

### 1. Prepare Phase
- **Read CLAUDE.md and/or README** to discover project-specific commands (check, lint, build, test)
- Verify the requirements passed in the prompt can be read
- Break down the requirements into tasks
- Analyze task dependencies (identify critical path vs parallel work)
- Determine optimal coder count if '--parallel' development is requested (2-5 based on task complexity and dependencies)
- Create task groups for parallel execution (independent tasks per group)

### 2. Spawn Parallel Subagents if requested
- Use **Task tool** for each subagent for implementation 
- If '--parallel' is passed in the primpt: Create 2-5 coder agents as parallel subagents
- Assign independent task groups to each coder (no overlapping files/features)
- Minimize context overlap between coders
- Provide clear instructions to each coder (see below)

**Instructions to Each Coder Subagent:**
```
Implement tasks [X.X-Y.Y]

FIRST: Read CLAUDE.md and/or README to discover the project's check/lint/build/test commands.

CRITICAL REQUIREMENTS (All mandatory):
1. Read the task file to understand your assigned tasks
2. Implement each task following CLAUDE.md guidelines
3. **Check subtask boxes [ ] → [x] as you complete them in the task file**
4. **Mark main task boxes [ ] → [x] when task is complete**
5. **Run ALL project checks when you finish - MUST pass with ZERO errors**
   (type checking, linting, formatting - whatever the project specifies)
6. Write tests for your code (if requirements includes testing tasks)

FAILURE CONDITIONS:
- If task file NOT updated with checkboxes → Work is FAILED
- If any project checks fail → Work is FAILED
- If any `any` types used (TypeScript projects) → Work is FAILED

Report back with:
- Which tasks you completed
- Confirmation that checkboxes are updated in task file
- Results of ALL project checks (must show ZERO errors)
- Any blockers encountered
```

### 3. Monitor Coder Progress
- Wait for all coders to complete (parallel execution)
- Track task completion by monitoring task file changes
- Handle dependencies if one coder blocks another
- Escalate blockers if any coder gets stuck

### 4. Verify Each Coder's Work (CRITICAL STEP)
After each coder completes, coordinator **MUST** verify:

- [ ] **Read task file** - Confirm checkboxes updated for assigned tasks
- [ ] **Verify all checks passed** - Coder must report ZERO errors
- [ ] **Spot check code** - Verify tasks actually implemented
- [ ] **Check code follows patterns** - Matches CLAUDE.md guidelines

**If ANY verification step fails:**
- Work is incomplete and must be redone
- Reassign to same or different coder
- Do NOT proceed until fixed

### 5. Run Final Quality Gates
After all coders complete and verified:

- [ ] All tasks marked `[x]` in the tasks files
- [ ] Run ALL project checks globally (from CLAUDE.md/README) - must pass with ZERO errors
- [ ] Run project build command - must succeed
- [ ] Run all tests (if phase includes tests)
- [ ] Verify no critical security issues
- [ ] Check all quality standards met (see Quality Gates section)

### 6. Complete Phase
- Verify all quality gates passed
- Mark phase as complete
- Prepare for next phase (if applicable)

**Output Files:**
- Updated the tasks file with `[x]` checkboxes
- Implementation artifacts (code, tests, documentation)

## How to Invoke Coder Subagents

The coordinator uses the **Task tool** to spawn parallel coder subagents. Each invocation creates an independent coder working on their assigned task group.

### Example: Spawning 3 Parallel Coder Agents (Foreground)

```typescript
// Coder 1: Database & Backend Foundation
Task({
  subagent_type: 'general-purpose',
  description: 'Phase 1 Database & Backend',
  prompt: `Implement tasks 1.1-1.5 and 2.1-2.2 from project-docs/tasks/phase-1-tasks.md

FIRST: Read CLAUDE.md/README to discover project check commands.

CRITICAL REQUIREMENTS:
1. Check subtask boxes [ ] → [x] as you complete them in the task file
2. Mark main task boxes [ ] → [x] when complete
3. Run ALL project checks when finished - MUST pass with ZERO errors
4. Follow project type conventions (no 'any' types in TypeScript)

Report back:
- Tasks completed
- Task file checkboxes updated (confirm)
- All project check results (must be passing)
- Any blockers`
})

// Coder 2: Backend Features & Seed Data
Task({
  subagent_type: 'general-purpose',
  description: 'Phase 1 Backend Features',
  prompt: `Implement tasks 2.3-2.4 and 3.1-3.2 from project-docs/tasks/phase-1-tasks.md

FIRST: Read CLAUDE.md/README to discover project check commands.

CRITICAL REQUIREMENTS:
1. Check subtask boxes [ ] → [x] as you complete them in the task file
2. Mark main task boxes [ ] → [x] when complete
3. Run ALL project checks when finished - MUST pass with ZERO errors
4. Follow project type conventions (no 'any' types in TypeScript)

Report back:
- Tasks completed
- Task file checkboxes updated (confirm)
- All project check results (must be passing)
- Any blockers`
})

// Coder 3: Frontend Structure & Integration
Task({
  subagent_type: 'general-purpose',
  description: 'Phase 1 Frontend',
  prompt: `Implement tasks 4.1-4.4 and 6.1-6.3 from project-docs/tasks/phase-1-tasks.md

FIRST: Read CLAUDE.md/README to discover project check commands.

CRITICAL REQUIREMENTS:
1. Check subtask boxes [ ] → [x] as you complete them in the task file
2. Mark main task boxes [ ] → [x] when complete
3. Run ALL project checks when finished - MUST pass with ZERO errors
4. Follow project type conventions (no 'any' types in TypeScript)

Report back:
- Tasks completed
- Task file checkboxes updated (confirm)
- All project check results (must be passing)
- Any blockers`
})
```

### Example: Spawning 3 Background Coder Agents (Async)

When `--background` flag is passed, use `run_in_background: true`:

```typescript
// Coder 1: Database & Backend Foundation (Background)
Task({
  subagent_type: 'general-purpose',
  description: 'Phase 1 Database & Backend',
  run_in_background: true,
  prompt: `Implement tasks 1.1-1.5 and 2.1-2.2 from project-docs/tasks/phase-1-tasks.md
...`
})
// Returns immediately with task_id and output_file path

// Coder 2: Backend Features & Seed Data (Background)
Task({
  subagent_type: 'general-purpose',
  description: 'Phase 1 Backend Features',
  run_in_background: true,
  prompt: `Implement tasks 2.3-2.4 and 3.1-3.2 from project-docs/tasks/phase-1-tasks.md
...`
})

// Coder 3: Frontend Structure & Integration (Background)
Task({
  subagent_type: 'general-purpose',
  description: 'Phase 1 Frontend',
  run_in_background: true,
  prompt: `Implement tasks 4.1-4.4 and 6.1-6.3 from project-docs/tasks/phase-1-tasks.md
...`
})

// Check on progress using TaskOutput tool:
TaskOutput({ task_id: '<task_id>', block: false, timeout: 5000 })

// Or read the output file directly:
Read({ file_path: '<output_file_path>' })
```

**After all coders complete:** Coordinator verifies task file updated + all project checks pass globally

## Example Parallel Coder Distribution

### For Phase 1 (Backend-Heavy) with 3 Coders:

**Coder 1: Database Schema & Foundation**
├── Tasks 1.1-1.5: Database schema setup
├── Task 2.1-2.2: Core functions
└── Run project checks when complete

**Coder 2: Backend Features & Seed Data**
├── Tasks 2.3-2.4: Feature-specific functions
├── Tasks 3.1-3.2: Seed data generation
└── Run project checks when complete

**Coder 3: Frontend Structure & Integration**
├── Tasks 4.1-4.4: Frontend project structure
├── Tasks 6.1-6.3: Backend integration
└── Run project checks when complete

### For Larger Phases with 4 Coders:

**Coder 1: Backend Core**
├── Database models
├── Core API endpoints
├── Authentication logic
└── Run project checks

**Coder 2: Backend Features**
├── Feature-specific endpoints
├── Data validation
├── Business logic
└── Run project checks

**Coder 3: Frontend Components**
├── UI components
├── React hooks
├── State management
└── Run project checks

**Coder 4: Integration & Quality**
├── API integration
├── Testing setup
├── Build verification
├── Documentation
└── Run project checks

## How Coders Communicate

1. **Shared Task File** (supplied from the user)
   - Single source of truth for phase tasks
   - Coders read it to understand assigned tasks
   - **Coders MUST update checkboxes when complete**
   - **NOT updating = FAILED process**
   - Coordinator verifies updates

2. **Status Updates**
   - Daily summary in a status file
   - Blockers escalated immediately
   - Dependencies tracked

3. **Code Integration**
   - Agents work on separate files/components
   - Regular git commits with clear messages
   - Code review between agents as needed

4. **Coordinator Decisions**
   - Breaks deadlocks
   - Reassigns work if needed
   - Escalates critical issues
   - Approves task completion


## Task Completion Flow

```
1. Agent selects task from [ ] (pending)
2. Agent works on subtasks
3. Agent checks subtask boxes as completed
4. Agent marks main task as [x] (complete)
5. Agent marks task with "✅ Completed by Agent N"
6. Coordinator verifies task is truly done
7. Coordinator marks task as fully complete
8. Move to next task
```

## Quality Gates (All Required Before Phase Completion)

### Critical Requirements (MUST PASS)
- [ ] **All tasks marked `[x]` in phase tasks file**
- [ ] **Task file updated by each coder (verified via git diff or file read)**
- [ ] **All project checks pass with ZERO errors globally** (type check, lint, format)
- [ ] **Code follows project type conventions** (e.g., no `any` in TypeScript)
- [ ] **All tests pass** (if phase includes testing tasks)
- [ ] **Build succeeds** (using project's build command from CLAUDE.md/README)

### Quality Standards
- [ ] Code follows project patterns (see CLAUDE.md)
- [ ] Proper types (as defined by the project's language/framework)
- [ ] Functions have explicit return types (where applicable)
- [ ] Error handling implemented properly
- [ ] Documentation comments on public functions (JSDoc, docstrings, etc.)
- [ ] No critical security issues

### Documentation
- [ ] Code is self-documenting with clear naming
- [ ] Complex logic has inline comments
- [ ] README updated if needed (new features, setup steps)

**IF ANY CRITICAL REQUIREMENT FAILS, PHASE IS NOT COMPLETE AND MUST BE FIXED.**


## Parallel Coder Capacity

- **2 coders**: Small phases (backend + frontend combined, or two independent feature groups)
- **3 coders**: Optimal for most phases (backend core + backend features + frontend, or database + backend + frontend)
- **4 coders**: Recommended for larger phases (backend core + backend features + frontend + integration/testing)
- **5+ coders**: Coordination overhead exceeds benefits

**Key Principle**: Assign independent work to each coder to minimize dependencies and file conflicts

## Handling Blockers

If an agent encounters a blocker:

1. Agent marks task with `⚠️ BLOCKER: [description]`
2. Coordinator is immediately notified
3. Coordinator either:
   - Reassigns to another agent
   - Resolves the blocker
   - Reorders work to unblock
4. Agent continues with next independent task

## Context Management

Each agent gets:
- **Task focus**: Only their assigned tasks
- **Shared context**: PRD, tech stack, personas
- **Code context**: Relevant files for their domain
- **Phase scope**: Phase document and dependencies

Agents do NOT duplicate full project context to conserve context usage.
