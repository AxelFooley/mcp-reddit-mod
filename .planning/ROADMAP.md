# Roadmap: ItaliaCareerMod

## Overview

Build an MCP server that enables AI-assisted Reddit moderation with human oversight. The journey begins with MCP protocol foundation and Docker deployment infrastructure, moves through Reddit API integration and safety mechanisms, implements all moderation tools with proper validation, and culminates in production-ready deployment with CI/CD pipeline.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3, 4): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: MCP Server Foundation** - FastMCP server with HTTP transport, Docker deployment, and error handling
- [ ] **Phase 2: Reddit Integration** - PRAW client initialization, authentication, and API wrapper
- [ ] **Phase 3: Moderation Tools** - All moderation tools with safety validation and timeout protection
- [ ] **Phase 4: Production Deployment** - Docker configuration, CI/CD pipeline, and production validation

## Phase Details

### Phase 1: MCP Server Foundation

**Goal**: Working MCP server accessible via HTTP transport with Docker deployment infrastructure

**Depends on**: Nothing (first phase)

**Requirements**: MCPF-01, MCPF-02, MCPF-03, MCPF-04, MCPF-05, DEPL-01, DEPL-02, DEPL-03, DEPL-04

**Success Criteria** (what must be TRUE):
  1. MCP server starts and exposes `/mcp` endpoint on port 8000 accessible from outside Docker container
  2. Server responds to tool discovery requests with proper metadata (name, version, description)
  3. Server returns structured error responses following MCP protocol specification
  4. Docker container can be built and started with `docker compose up` using provided docker-compose.yml
  5. Environment variables from .env.example are properly documented for Reddit credentials

**Plans**: 5 plans in 2 waves

**Plan List:**
- [x] 01-00-PLAN.md — Test infrastructure foundation (Wave 0)
- [x] 01-01-PLAN.md — FastMCP server with HTTP transport and metadata (Wave 1)
- [x] 01-02a-PLAN.md — Docker build infrastructure (Wave 1)
- [x] 01-02b-PLAN.md — Docker deployment configuration (Wave 1)
- [x] 01-03-PLAN.md — Project documentation and git setup (Wave 2)

### Phase 2: Reddit Integration

**Goal**: PRAW client initialized with environment-based authentication and ready for API calls

**Depends on**: Phase 1 (Docker infrastructure and environment setup)

**Requirements**: REDI-01, REDI-02

**Success Criteria** (what must be TRUE):
  1. PRAW client initializes successfully using credentials from environment variables
  2. Client uses script app authentication (not OAuth flow)
  3. Client can authenticate with Reddit API without errors
  4. Invalid credentials produce clear error messages without exposing credential values

**Plans**: 2 plans in 2 waves

**Plan List:**
- [x] 02-00-PLAN.md — Test infrastructure foundation (Wave 0)
- [x] 02-01-PLAN.md — PRAW client with environment auth and singleton pattern (Wave 1)

### Phase 3: Moderation Tools

**Goal**: Complete set of moderation tools accessible via MCP protocol with safety and timeout protection

**Depends on**: Phase 2 (PRAW client initialization)

**Requirements**: REDI-03, REDI-04, MODT-01, MODT-02, MODT-03, MODT-04, MODT-05, SAFE-01, SAFE-02

**Success Criteria** (what must be TRUE):
  1. AI agent can fetch modqueue items for any subreddit via `get_modqueue(subreddit)` tool
  2. AI agent can approve items via `approve_item(thing_id)` and remove via `remove_item(thing_id, reason)`
  3. AI agent can ban users via `ban_user(subreddit, username, reason, duration_days)` with permanent/temporary support
  4. AI agent can fetch user's flagged history via `get_user_history(username, subreddit)` for repeat offender detection
  5. Thing ID type validation rejects invalid IDs (wrong prefix format) before API calls
  6. PRAW exceptions propagate to AI agent with error details but without credential information
  7. All PRAW API calls complete within timeout period (no indefinite hangs)

**Plans**: 3 plans in 2 waves

**Plan List:**
- [ ] 03-00-PLAN.md — Test infrastructure foundation (Wave 0)
- [ ] 03-01-PLAN.md — Core moderation tools with validation and sanitization (Wave 1)
- [ ] 03-02-PLAN.md — User history, timeout protection, and error propagation (Wave 2)

### Phase 4: Production Deployment

**Goal**: Production-ready deployment with CI/CD pipeline and validation against real Reddit API

**Depends on**: Phase 3 (All moderation tools working)

**Requirements**: DEPL-05, CICD-01, CICD-02, CICD-03, CICD-04

**Success Criteria** (what must be TRUE):
  1. GitHub Actions workflow runs on every push and executes mandatory linters (ruff, mypy)
  2. CI runs tests with full coverage requirement and fails if coverage is insufficient
  3. CI builds Docker image on successful test completion
  4. CI pushes Docker image to ghcr.io/axelfooley when main branch builds succeed
  5. Server can be tested against real Reddit API using MCP Inspector or equivalent client

**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. MCP Server Foundation | 5/5 | Complete | 2026-03-11 |
| 2. Reddit Integration | 2/2 | Complete | 2026-03-11 |
| 3. Moderation Tools | 0/3 | Not started | - |
| 4. Production Deployment | 0/TBD | Not started | - |
