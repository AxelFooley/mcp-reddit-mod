# Requirements: ItaliaCareerMod

**Defined:** 2025-03-11
**Core Value:** AI-assisted Reddit moderation with human oversight. Automated review of mod queue items with intelligent repeat offender detection, while keeping humans in control of destructive actions.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### MCP Server Foundation

- [ ] **MCPF-01**: MCP server uses Streamable HTTP transport (not stdio) for Docker deployment
- [ ] **MCPF-02**: Server exposes `/mcp` endpoint on 0.0.0.0:8000 for external access
- [ ] **MCPF-03**: Server implements tool discovery protocol (`list_tools()` method)
- [ ] **MCPF-04**: Server provides metadata (name, version, description) to clients
- [ ] **MCPF-05**: Server returns structured error responses per MCP protocol

### Reddit API Integration

- [ ] **REDI-01**: PRAW client initialized from environment variables (REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USERNAME, REDDIT_PASSWORD, REDDIT_USER_AGENT)
- [ ] **REDI-02**: PRAW uses script app authentication (not OAuth)
- [ ] **REDI-03**: PRAW exceptions propagate to AI agent with error details
- [ ] **REDI-04**: All PRAW API calls wrapped with timeout to prevent indefinite hanging

### Moderation Tools

- [ ] **MODT-01**: `get_modqueue(subreddit)` — fetches current mod queue items via PRAW `/r/{sub}/about/modqueue`
- [ ] **MODT-02**: `approve_item(thing_id)` — approves a post or comment by thing_id
- [ ] **MODT-03**: `remove_item(thing_id, reason)` — removes a post or comment with reason
- [ ] **MODT-04**: `ban_user(subreddit, username, reason, duration_days)` — bans user (duration_days=0 for permanent)
- [ ] **MODT-05**: `get_user_history(username, subreddit)` — fetches user's posts/comments that were previously flagged in the subreddit

### Safety & Validation

- [ ] **SAFE-01**: Thing ID type validation (t1_ for comments, t2_ for users, t3_ for posts) before operations
- [ ] **SAFE-02**: Error responses sanitized to remove credential information

### Deployment

- [ ] **DEPL-01**: Dockerfile uses `python:3.12-slim` base image
- [ ] **DEPL-02**: Dockerfile includes uv package manager for dependency installation
- [ ] **DEPL-03**: docker-compose.yml provided for homelab deployment
- [ ] **DEPL-04**: `.env.example` file includes all 5 required Reddit credential variables
- [ ] **DEPL-05**: GitHub Actions CI workflow runs on every push

### CI/CD Pipeline

- [ ] **CICD-01**: CI runs mandatory linters (ruff, mypy, or equivalent)
- [ ] **CICD-02**: CI runs tests with full coverage requirement
- [ ] **CICD-03**: CI builds Docker image on successful tests
- [ ] **CICD-04**: CI pushes Docker image to `ghcr.io/axelfooley` on main branch

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Enhanced Moderation

- **MODT-10**: `get_modmail()` — fetch modmail messages for triage
- **MODT-11**: `set_flair()` — set post flair for approved content

### Observability

- **OBSV-01**: Audit logging — log all AI-suggested actions to file for review
- **OBSV-02**: Metrics endpoint — expose modqueue depth, action counts

### Resilience

- **RESL-01**: Rate limit awareness — exponential backoff and retry for PRAW rate limits
- **RESL-02**: Retry logic — configurable retry for transient API failures

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| UI / Web interface | This is an API/protocol server, not a web application |
| Database / Local state | Reddit is source of truth, no persistence needed |
| HTTP authentication layer | Runs in private homelab network, trust network-level security |
| Stdio transport | HTTP required for Docker deployment |
| Multi-reddit batch operations | Single-subreddit operations only per call (v1) |
| Fully autonomous bans | Human-in-the-loop required for safety |
| Real-time monitoring / Webhooks | Polling-based modqueue fetch sufficient for v1 |
| OAuth authentication | Script app auth sufficient for homelab use |
| Sentiment analysis / ML features | Deferred to future versions |
| Karma-based auto-actions | Manual review with AI assistance preferred |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| MCPF-01 | Phase 1 | Pending |
| MCPF-02 | Phase 1 | Pending |
| MCPF-03 | Phase 1 | Pending |
| MCPF-04 | Phase 1 | Pending |
| MCPF-05 | Phase 1 | Pending |
| REDI-01 | Phase 2 | Pending |
| REDI-02 | Phase 2 | Pending |
| REDI-03 | Phase 3 | Pending |
| REDI-04 | Phase 3 | Pending |
| MODT-01 | Phase 3 | Pending |
| MODT-02 | Phase 3 | Pending |
| MODT-03 | Phase 3 | Pending |
| MODT-04 | Phase 3 | Pending |
| MODT-05 | Phase 3 | Pending |
| SAFE-01 | Phase 3 | Pending |
| SAFE-02 | Phase 3 | Pending |
| DEPL-01 | Phase 4 | Pending |
| DEPL-02 | Phase 4 | Pending |
| DEPL-03 | Phase 4 | Pending |
| DEPL-04 | Phase 4 | Pending |
| DEPL-05 | Phase 4 | Pending |
| CICD-01 | Phase 4 | Pending |
| CICD-02 | Phase 4 | Pending |
| CICD-03 | Phase 4 | Pending |
| CICD-04 | Phase 4 | Pending |

**Coverage:**
- v1 requirements: 24 total
- Mapped to phases: 24
- Unmapped: 0 ✓

---
*Requirements defined: 2025-03-11*
*Last updated: 2025-03-11 after initial definition*
