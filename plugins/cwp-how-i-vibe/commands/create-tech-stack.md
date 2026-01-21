---
name: cwp:create-tech-stack
description: Analyzes your current project and interviews you about technology preferences to create or update a tech stack document. If /docs/tech-stack.md already exists, updates it with any changes. Use when starting a new project, documenting an existing codebase, or updating technology choices.
disable-model-invocation: true
---

# Tech Stack - Technology Stack Documentation

Creates or updates a comprehensive technology stack document by analyzing your current project and interviewing you about your preferences and requirements.

## Process

### 1. Check for Existing Tech Stack

First, check if `/docs/tech-stack.md` already exists. If it does:
- Read the existing document to understand current decisions
- Use it as a baseline for the interview (confirm or update each section)
- Preserve any custom sections or notes the user has added

### 2. Analyze Current Project

Examine the existing codebase to understand:
- Current technologies in use (package.json, requirements.txt, go.mod, etc.)
- Project structure and architecture patterns
- Existing infrastructure configurations
- Development tooling already configured

### 3. Interview the User

Use the `AskUserQuestion` tool to gather preferences and requirements. Ask about:

**Project Goals & Scale**
- What type of application is this? (web app, API, CLI, library, etc.)
- What's the expected scale? (personal project, startup MVP, enterprise)
- What are the key non-functional requirements? (performance, security, accessibility)

**Frontend Preferences** (if applicable)
- Framework preference (React, Vue, Svelte, vanilla, etc.)
- Styling approach (CSS-in-JS, Tailwind, CSS modules, etc.)
- Component library needs

**Backend Preferences** (if applicable)
- Runtime preference (Node.js, Bun, Deno, Python, Go, etc.)
- Framework preferences
- Database needs (SQL, NoSQL, both)

**Infrastructure & Deployment**
- Hosting preference (cloud provider, serverless, containers)
- CI/CD requirements
- Monitoring and observability needs

**Development Experience**
- Team size and experience levels
- Existing tooling preferences
- Testing requirements

### 4. Recommend Stack

Based on analysis and user input, recommend:
- Frontend framework & libraries
- Backend framework & runtime
- Database & cache solutions
- Infrastructure & deployment
- Development tools & testing

### 5. Document Decisions

Create or update `/docs/tech-stack.md` with:
- Rationale for each choice
- Trade-offs vs alternatives considered
- Compatibility considerations
- Migration path (if updating existing stack)

## Output

- `/docs/tech-stack.md` - Complete technology stack documentation (created or updated)

## Example Tech Stack Document

```markdown
# Technology Stack

## Architecture Overview
[High-level architecture diagram/description]

## Frontend Stack
- Framework: React 19 with TypeScript
- Build Tool: Vite
- UI Component Library: ShadCN/UI
- Styling: TailwindCSS
- State Management: TanStack Query + Zustand

## Backend Stack
- Runtime: Node.js/Bun
- Framework: Hono
- Database: PostgreSQL
- Cache: Redis
- Authentication: Clerk

## Infrastructure
- Hosting: Cloudflare Workers
- Database Hosting: Convex / Supabase
- CDN: Cloudflare
- Email: Resend / SendGrid

## Development Tools
- Package Manager: Bun
- Linter: Biome
- Type Checking: TypeScript Strict Mode
- Testing: Vitest + Testing Library
- CI/CD: GitHub Actions

## Decision Rationale
[Detailed rationale for each choice]

## Trade-offs & Alternatives
[Document what else was considered and why it was rejected]
```
