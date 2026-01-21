---
name: cwp:create-prd
description: Guides you through creating a comprehensive Product Requirements Document (PRD) using an interview process. Checks for existing PRDs and supports updates. Writes output to /docs/prd-{project-name}.md. Use --analyze to reverse-engineer a PRD from an existing codebase.
disable-model-invocation: true
arguments:
  - name: --analyze
    description: Analyze an existing codebase to reverse-engineer a PRD. Uses explorer subagents to discover backend, frontend, database, and infrastructure components.
    required: false
---

# PRD Creator - Product Requirements Document

Creates or updates a comprehensive Product Requirements Document (PRD) by interviewing you about your project's goals, users, features, and technical considerations.

## Modes

This command supports two modes:

1. **Interview Mode** (default): Guides you through questions to create a PRD from scratch
2. **Analyze Mode** (`--analyze`): Reverse-engineers a PRD from an existing codebase

---

## Analyze Mode (`--analyze`)

When the `--analyze` flag is provided, use explorer subagents to discover what the application does and generate a PRD based on the findings.

### A1. Launch Parallel Codebase Exploration

Use the `Task` tool with `subagent_type: Explore` to launch **4 parallel explorations**. Each exploration should be "very thorough" and focus on a specific architectural layer:

**Explorer 1: Backend & APIs**
```
Analyze the backend architecture of this codebase:
- API routes and endpoints (REST, GraphQL, etc.)
- Request/response patterns and data formats
- Authentication and authorization mechanisms
- Business logic and service layers
- Middleware and request processing
- Error handling patterns
Report: What does this backend DO? What operations does it support?
```

**Explorer 2: Frontend & UI**
```
Analyze the frontend architecture of this codebase:
- UI framework and component structure
- Pages, routes, and navigation flow
- State management approach
- User-facing features and interactions
- Forms and user input handling
- Styling and design system
Report: What can users SEE and DO in this application?
```

**Explorer 3: Database & Data Models**
```
Analyze the data layer of this codebase:
- Database type and schema design
- Data models and relationships
- Migrations and schema evolution
- Data validation rules
- Caching strategies
Report: What data does this application store and manage?
```

**Explorer 4: Infrastructure & Integration**
```
Analyze the infrastructure and integrations:
- Deployment configuration (Docker, cloud configs, etc.)
- CI/CD pipelines
- Third-party service integrations
- Environment configuration
- External APIs consumed
- Background jobs and scheduled tasks
Report: How is this application deployed and what does it connect to?
```

### A2. Synthesize Exploration Results

Once all explorers complete, synthesize their findings into a coherent understanding of:
- What the application does (core purpose)
- Who uses it (inferred user types)
- Key features and capabilities
- Technical architecture

### A3. Brief User Interview for Business Context

Use `AskUserQuestion` to fill gaps that can't be determined from code:

- Is the discovered purpose accurate? Any corrections?
- What are the business goals behind this product?
- What are explicit non-goals?
- Any user personas or roles not evident in the code?
- Current project phase and future plans?

### A4. Generate PRD from Analysis

Using the exploration results and user input, generate the complete PRD following the template below. Mark sections derived from code analysis vs user input.

### A5. Write PRD Document

Generate the slug from the project name and write to `/docs/prd-{slug}.md`.

---

## Interview Mode (Default)

When no flags are provided, use the standard interview process.

### I1. Check for Existing PRD

First, search for existing PRD files matching `/docs/prd-*.md`. If found:
- Present the list to the user
- Ask if they want to update an existing PRD or create a new one
- If updating, read the existing document to preserve and build upon current content

### I2. Project Foundation Interview

Use the `AskUserQuestion` tool to gather core project information:

**Project Identity**
- What is the project title?
- What version is this? (default: v1)
- Provide a brief summary of the project and its purpose (2-3 sentences)

**Special Instructions**
- Are there any specific instructions or constraints for this PRD?
- Any particular focus areas or concerns?

### I3. Goals & Users Interview

**Goals**
- What are the business goals? (revenue, market position, efficiency)
- What are the user goals? (what users want to accomplish)
- What are the non-goals? (explicitly out of scope)

**User Personas**
- Who are the key user types? (e.g., Admin, Registered User, Guest)
- Describe each persona briefly
- What role-based access/permissions does each have?

### I4. Functional Requirements Interview

**Features**
- List the main features with their priorities (High/Medium/Low)
- For each feature, what are the specific requirements?
- Are there any dependencies between features?

### I5. User Experience Interview

**Entry Points & Flow**
- How do users discover/access the product?
- What is the first-time user experience?

**Core Experience**
- Walk through the main user journey step by step
- What makes each step successful?

**UI/UX Highlights**
- Any specific UI patterns or design requirements?
- Accessibility considerations?
- Advanced features or edge cases to handle?

### I6. Technical & Planning Interview

**Technical Considerations**
- What are the integration points? (APIs, services, third-party tools)
- Data storage and privacy requirements?
- Scalability and performance expectations?
- Potential technical challenges?

**Success Metrics**
- User-centric metrics (engagement, satisfaction, task completion)
- Business metrics (conversion, retention, revenue)
- Technical metrics (performance, uptime, error rates)

**Project Planning**
- Estimated project size? (Small: 1-2 weeks, Medium: 2-4 weeks, Large: 4+ weeks)
- Team size and composition?
- Suggested phases and milestones?

### I7. Generate User Stories

Based on all gathered information, generate comprehensive user stories:
- Cover all primary user flows
- Include alternative scenarios
- Address edge cases
- Include authentication/authorization stories if applicable
- Each story must have: ID (US-001, etc.), Description, Acceptance Criteria

### I8. Write PRD Document

Generate the slug from the project title (lowercase, hyphens for spaces) and write to `/docs/prd-{slug}.md`.

## PRD Output Template

The generated PRD must follow this exact structure:

```markdown
# PRD: {project_title}

## 1. Product overview

### 1.1 Document title and version
- PRD: {project_title}
- Version: {version_number}

### 1.2 Product summary
[2-3 paragraphs overview of the project]

## 2. Goals

### 2.1 Business goals
- [Bullet list of business goals]

### 2.2 User goals
- [Bullet list of user goals]

### 2.3 Non-goals
- [Bullet list of non-goals]

## 3. User personas

### 3.1 Key user types
- [Bullet list of user types]

### 3.2 Basic persona details
- **{persona_name}**: {persona_description}

### 3.3 Role-based access
- **{role_name}**: {role_description and permissions}

## 4. Functional requirements
- **{feature_name}** (Priority: {High|Medium|Low})
  - [Requirement details]

## 5. User experience

### 5.1 Entry points & first-time user flow
- [Bullet list]

### 5.2 Core experience
- **{step}**: {explanation}
  - {how to make it successful}

### 5.3 Advanced features & edge cases
- [Bullet list]

### 5.4 UI/UX highlights
- [Bullet list]

## 6. Narrative
[Single paragraph describing user journey from their perspective]

## 7. Success metrics

### 7.1 User-centric metrics
- [Bullet list]

### 7.2 Business metrics
- [Bullet list]

### 7.3 Technical metrics
- [Bullet list]

## 8. Technical considerations

### 8.1 Integration points
- [Bullet list]

### 8.2 Data storage & privacy
- [Bullet list]

### 8.3 Scalability & performance
- [Bullet list]

### 8.4 Potential challenges
- [Bullet list]

## 9. Milestones & sequencing

### 9.1 Project estimate
- {Small|Medium|Large}: {scope description}

### 9.2 Team size & composition
- {Team size}: {number} total people
  - {roles list}

### 9.3 Suggested phases
- **Phase 1**: {description} ({scope})
  - Key deliverables: {deliverables}

## 10. User stories

### 10.1 {user_story_title}
- **ID**: US-001
- **Description**: As a {role}, I want to {action} so that {benefit}.
- **Acceptance criteria**:
  - [Criteria list]
```

## Output

- `/docs/prd-{project-slug}.md` - Complete PRD document (created or updated)

## Guidelines

- Use sentence case for all headings except the document title
- Do not use horizontal rules/dividers
- Fix grammatical errors and ensure proper casing
- Refer to the project conversationally ("the project", "this tool") not by variable names
- Ensure all user stories are testable
- Acceptance criteria must be clear and specific
- Include authentication/authorization stories if the app requires user identification
