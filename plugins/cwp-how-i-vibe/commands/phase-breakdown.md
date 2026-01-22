---
name: cwp:phase-breakdown
description: Breaks your PRD into full-stack development phases. Each phase delivers a working product with core functionality. Checks for existing phases and PRD changes via git history. Writes output to /docs/phases/.
disable-model-invocation: true
---

# Phase Breakdown - Break PRD Into Development Phases

Breaks your PRD into full-stack development phases. Each phase delivers a working product with core functionality, using a vertical slice approach (frontend + backend + infrastructure together per feature).

## Process

### 1. Locate and Validate PRD

First, search for PRD files matching `/docs/prd-*.md`:

- **If no PRD found**: Stop and inform user to run `cwp:create-prd` first
- **If single PRD found**: Use it automatically
- **If multiple PRDs found**: Use `AskUserQuestion` to let user select which PRD to break down

Read the selected PRD thoroughly to understand:
- All features and requirements
- User personas and their needs
- Technical considerations
- Success metrics
- Existing milestone suggestions (Section 9)

### 2. Check PRD Git History

Use git to check for recent changes to the PRD:

```bash
git log --oneline -10 -- docs/prd-*.md
git diff HEAD~5 -- <selected-prd-file>
```

If the PRD has been modified recently:
- Summarize what changed (new features, removed scope, updated priorities)
- Consider these changes when creating/updating phases
- Note any changes that might affect existing phase definitions

### 3. Check for Existing Phases

Check if `/docs/phases/` directory exists and contains phase files:

- **If phases exist**: Read all existing phase files (`phase-*.md` and `phases-overview.md`)
  - Determine what has been completed vs in-progress vs planned
  - Identify if PRD changes require phase updates
  - Present options to user: update existing phases, add new phases, or regenerate all
- **If no phases exist**: Proceed to interview for new phase creation

### 4. Interview for Phase Strategy

Use `AskUserQuestion` to gather preferences for phase structure:

**Phase Philosophy**
- Should phases follow vertical/full-stack slices (feature-complete) or horizontal layers (all backend, then all frontend)?
- What's the preferred phase size? (1-2 weeks, 2-4 weeks, or flexible)

**Priority Clarification**
- Which features from the PRD are highest priority for Phase 1 MVP?
- Are there any features that should be deferred to later phases?
- Any external dependencies or deadlines affecting phase ordering?

**Technical Considerations**
- Are there infrastructure prerequisites that must come first?
- Any third-party integrations with long lead times?
- Database migrations or breaking changes to consider?

**Team Context** (if relevant)
- Will phases be worked on sequentially or can some run in parallel?
- Any team specializations affecting phase assignment?

### 5. Design Phase Structure

Based on PRD analysis and user input, design phases following these principles:

**Phase 1: MVP**
- Minimum features to deliver core value
- Complete user journey for primary persona
- Essential infrastructure only

**Phase 2: Critical Enhancements**
- Features that significantly improve Phase 1
- Secondary user personas
- Important integrations

**Phase 3+: Advanced Features**
- Nice-to-have features
- Optimizations and polish
- Analytics and advanced tooling

### 6. Write Phase Documents

Generate the following files:

- `/docs/phases/phases-overview.md` - Summary of all phases with dependencies
- `/docs/phases/phase-1.md` through `/docs/phases/phase-N.md` - Individual phase details

## Output

- `/docs/phases/phases-overview.md` - Phase summary, dependencies, and status
- `/docs/phases/phase-{N}.md` - Detailed phase specifications

## Phase Overview Template

```markdown
# Phases Overview

## PRD Reference
- **Source**: /docs/prd-{slug}.md
- **Last PRD Update**: {date from git}
- **Phases Generated**: {date}

## Phase Summary

| Phase | Name | Status | Dependencies |
|-------|------|--------|--------------|
| 1 | MVP - Core Product | Not Started | None |
| 2 | Enhanced Features | Not Started | Phase 1 |
| 3 | Advanced Capabilities | Not Started | Phase 2 |

## Dependency Graph

```
Phase 1 (MVP)
    └── Phase 2 (Enhancements)
            └── Phase 3 (Advanced)
```

## Phase Descriptions

### Phase 1: MVP - Core Product
{Brief description of what this phase delivers}

### Phase 2: Enhanced Features
{Brief description of what this phase delivers}

### Phase 3: Advanced Capabilities
{Brief description of what this phase delivers}
```

## Individual Phase Template

```markdown
# Phase {N}: {Phase Name}

## Objective
{1-2 sentences describing the goal of this phase and what value it delivers}

## PRD Features Addressed
- Feature X (from PRD Section 4)
- Feature Y (from PRD Section 4)

## Scope

### User Stories Included
Reference user stories from PRD Section 10:
- US-001: {title}
- US-002: {title}

### Frontend Deliverables
- {Page/component description}
- {Page/component description}

### Backend Deliverables
- {API/service description}
- {API/service description}

### Data Model Changes
- {Schema/migration description}

### Infrastructure Requirements
- {Deployment/config requirements}

## Out of Scope
Explicitly list what is NOT included in this phase:
- {Feature/capability deferred to later phase}

## Success Criteria
- [ ] {Measurable criterion}
- [ ] {Measurable criterion}
- [ ] {Measurable criterion}

## Dependencies
- **Prerequisite Phases**: {Phase N-1, or "None" for Phase 1}
- **External Dependencies**: {Third-party services, approvals, etc.}

## Risks & Mitigations
| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| {Risk description} | Low/Med/High | Low/Med/High | {Mitigation strategy} |

## Open Questions
- {Any unresolved questions that need answers before implementation}
```

## Guidelines

- **No time estimates**: Do not include duration, timeline, or time estimates in phase documents
- **No implementation details**: Phases describe WHAT to build, not HOW. Save code and implementation specifics for task planning
- **Interface descriptions only**: If technical detail is needed, limit to interface contracts or API signatures, not implementation
- **Reference PRD sections**: Always link back to specific PRD sections for traceability
- **Testable success criteria**: Each criterion should be verifiable
- **Explicit scope boundaries**: Clearly state what's in AND out of each phase
- Use sentence case for all headings except document titles
- Do not use horizontal rules/dividers

## Phase Design Principles

1. **Vertical Slices Over Horizontal Layers**
   - Each phase delivers working end-to-end functionality
   - Not: "Backend phase, then frontend phase"
   - But: "Authentication phase (includes login UI + auth API + user table)"

2. **Progressive Value Delivery**
   - Phase 1: Minimum viable product - users can accomplish core goal
   - Phase 2: Critical enhancements - significantly better experience
   - Phase 3+: Advanced features - delight and differentiation

3. **Minimal Dependencies**
   - Phases ordered by logical progression
   - Avoid circular dependencies
   - Identify phases that could run in parallel if team allows

4. **Clear Boundaries**
   - Every feature belongs to exactly one phase
   - No ambiguity about what's in vs out
   - Success criteria are binary (done or not done)
