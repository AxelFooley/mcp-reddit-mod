# Project Research Summary

**Project:** ItaliaCareerMod
**Domain:** MCP Server with Reddit API Integration
**Researched:** 2025-03-11
**Confidence:** HIGH

## Executive Summary

ItaliaCareerMod is an **MCP (Model Context Protocol) server** that provides AI-assisted Reddit moderation tools for the r/ItaliaCareer community. The standard 2025 approach for building Python MCP servers centers on the **official MCP Python SDK (v1.26.0)** with **FastMCP** framework, using **PRAW 7.8.2+** for Reddit API integration. The server uses **HTTP transport (Streamable HTTP)** for Docker deployment, **uvicorn 0.41.0 + Starlette 0.52.1** for ASGI capabilities, and **uv** for modern Python package management.

The recommended architecture follows a **lifespan-based pattern** where a single PRAW client instance is created at startup and shared across all tool functions via context injection. Tools are registered using FastMCP's decorator system with Pydantic models for structured output validation. The key differentiator is **AI-assisted triage with human-in-the-loop confirmation** — AI suggests moderation actions based on modqueue analysis and user history, but humans confirm destructive actions like bans.

**Critical risks** identified in research: (1) Reddit has hidden rate limits beyond PRAW's automatic handling that can cause cascading failures; (2) Error messages can leak Reddit credentials if not properly sanitized; (3) MCP tools can hang indefinitely if PRAW operations block; (4) Docker networking must bind to `0.0.0.0` not `localhost`. All are addressed with specific mitigation strategies in Phase 1.

## Key Findings

### Recommended Stack

The research strongly recommends the official MCP Python SDK with FastMCP as the foundation. This is now the standard framework — 70% of MCP servers across all languages use some version of FastMCP. For Reddit integration, PRAW 7.8.2+ remains the authoritative library with full moderation API support and built-in rate limiting. The stack prioritizes HTTP transport over stdio for Docker deployments and adopts uv for Python package management due to its 10-100x performance improvement over pip.

**Core technologies:**
- **mcp (Python SDK) 1.26.0+** — Official MCP protocol implementation with FastMCP framework; actively developed with built-in HTTP transport support and type-safe tool definitions
- **PRAW 7.8.2+** — Python Reddit API Wrapper with automatic rate limiting, full moderation API support (modqueue, approve/remove, ban user), script app authentication
- **Python 3.11+** — Minimum requirement for FastMCP compatibility; Python 3.12+ recommended for better performance and typing features
- **uvicorn 0.41.0+** — Lightning-fast ASGI server, production-ready, supports Gunicorn integration for multi-worker deployments
- **Starlette 0.52.1+** — ASGI toolkit officially supported by MCP SDK for mounting FastMCP servers with custom routing and middleware
- **uv** — 10-100x faster than pip, single tool replacing pip/pip-tools/pipx/poetry/pyenv/virtualenv, universal lockfile

### Expected Features

The feature research identifies a clear distinction between table-stakes functionality and competitive differentiators. Basic moderation operations (approve, remove, ban) and modqueue access are expected features. The key differentiator is AI-assisted triage with repeat offender detection — the AI can summarize modqueue items and surface patterns from user history, while requiring human confirmation for destructive actions.

**Must have (table stakes):**
- **HTTP MCP server transport** — Required for Docker deployment, enables AI agents to call tools independently
- **Modqueue fetch tool** — `get_modqueue(subreddit)` returns current queue items with metadata
- **Basic moderation actions** — `approve_item(thing_id)`, `remove_item(thing_id, reason)` for content triage
- **User banning tool** — `ban_user(subreddit, username, reason, duration_days)` with permanent/temporary support
- **User history lookup** — `get_user_history(username, subreddit)` returns previously flagged items for repeat offender detection
- **Environment-based auth** — All Reddit credentials via environment variables, no hardcoded secrets
- **Error propagation** — PRAW exceptions surface to AI agent for decision-making

**Should have (competitive):**
- **AI-assisted triage** — LLM summarizes modqueue items and surfaces patterns (requires well-structured tool responses)
- **Repeat offender detection** — Targeted history showing only flagged items, not general stalking
- **Human-in-the-loop for destructive actions** — Safety layer preventing AI from taking irreversible actions
- **Explainable moderation** — AI provides rationale for actions before execution
- **Moderation audit trail** — All AI-suggested actions logged for review

**Defer (v2+):**
- **Multi-subreddit operations** — Cross-subreddit ban detection and coordinated actions (permission matrix complexity)
- **ML-based pattern detection** — Training models on moderation history (requires labeled data, adds ML ops burden)
- **Webhook support** — Reddit pushes events instead of polling (requires public endpoint, adds infrastructure)
- **OAuth authentication** — Support OAuth flow instead of script app (adds redirect server, complexity vs benefit unclear)

### Architecture Approach

The recommended architecture follows a **FastMCP decorator-based pattern** with lifespan context management. A single FastMCP server instance manages tool registration, while a lifespan context manager initializes the PRAW client at startup and shares it across all tool functions via context injection. Tools use Pydantic models for structured output validation, and the server runs on Streamable HTTP transport in stateless mode for optimal scalability.

**Major components:**
1. **FastMCP Server** — Main server instance with lifecycle management and protocol compliance; registers tools via decorators
2. **Tools Registry** — Decorator-based tool registration with automatic schema generation from type hints
3. **Lifespan Manager** — Initializes PRAW client at startup, handles cleanup on shutdown, provides type-safe access via context
4. **PRAW Client (Singleton)** — Single Reddit API client instance shared across all requests; handles rate limiting and authentication
5. **Reddit Module** — Encapsulates all Reddit-specific logic (modqueue, moderation actions, user history) with clear boundary from MCP layer
6. **Schemas Module** — Pydantic models defining structured output contracts for all tools
7. **Transport Layer** — Streamable HTTP with stateless mode and JSON responses for multi-client support

### Critical Pitfalls

The research identified six critical pitfalls that must be addressed in Phase 1. The most severe involve Reddit's hidden rate limits (beyond PRAW's automatic handling), credential leakage in error messages, and indefinite tool blocking when PRAW operations hang. Docker networking issues are also common — servers binding to `localhost` inside containers become inaccessible externally.

1. **Ignoring Reddit's Hidden Rate Limits** — PRAW handles standard API rate limits, but Reddit has additional undocumented limits for moderation actions. Configure `ratelimit_seconds`, catch `RedditAPIException`, implement exponential backoff.
2. **Reddit Credentials Leaked in Error Messages** — PRAW exceptions may include credential information. Sanitize all exceptions before returning through MCP tools, never include raw stack traces.
3. **MCP Tool Blocking Causes Agent Hangs** — PRAW calls can block indefinitely. Implement timeout wrappers (30-60s) for all PRAW operations, return partial results with continuation tokens.
4. **Subreddit Name Validation Missing** — Invalid subreddit names cause cryptic errors. Implement pre-flight validation, check if subreddit exists and is accessible, verify moderator permissions.
5. **Docker HTTP Transport Binding Issues** — Binding to `localhost` inside container makes it inaccessible externally. Explicitly bind to `0.0.0.0:8000`, use docker-compose for environment variables.
6. **Thing ID Confusion and Type Mismatches** — Reddit uses fullname prefixes (t1_, t2_, t3_) for different object types. Validate ID format and type in all tools, return clear errors.

## Implications for Roadmap

Based on combined research, the roadmap should follow a four-phase structure that builds from foundation to deployment. The phase ordering is driven by component dependencies identified in architecture research: config/schemas foundation first, then Reddit integration, then MCP server assembly, then deployment. Each phase addresses specific pitfalls identified in the pitfalls research.

### Phase 1: Foundation & Infrastructure
**Rationale:** Config and schemas are prerequisites for all other components. Docker deployment must be proven early to avoid HTTP transport binding issues (Pitfall 5). Error handling middleware prevents credential leaks (Pitfall 2) and agent hangs (Pitfall 3).
**Delivers:** Configuration management, Pydantic schemas, Docker deployment setup, error handling middleware
**Addresses:** HTTP MCP server transport, Environment-based auth, Error propagation (from FEATURES.md table stakes)
**Avoids:** Docker HTTP binding issues (Pitfall 5), Credential leakage (Pitfall 2), Tool blocking (Pitfall 3)

### Phase 2: Reddit API Integration
**Rationale:** Reddit module must be built and tested before wrapping in MCP tools. This phase implements PRAW client wrapper and core API functions with proper ID validation (Pitfall 6) and subreddit validation (Pitfall 4).
**Delivers:** PRAW client wrapper, Reddit API functions (modqueue, approve, remove, ban, user history), input validation utilities, unit tests with mocked PRAW
**Addresses:** Modqueue fetch, Basic moderation actions, User banning, User history lookup (from FEATURES.md table stakes)
**Avoids:** Subreddit validation missing (Pitfall 4), Thing ID confusion (Pitfall 6)

### Phase 3: MCP Server Assembly
**Rationale:** With Reddit module complete, this phase wraps API functions in FastMCP tools with proper lifespan management and context injection. Implements the core AI-assisted triage pattern.
**Delivers:** FastMCP server with lifespan, tool registration, context injection for PRAW client, structured output with Pydantic models
**Addresses:** AI-assisted triage, Human-in-the-loop confirmation, Explainable moderation (from FEATURES.md differentiators)
**Implements:** FastMCP decorator pattern, Lifespan context management, Structured output with Pydantic (from ARCHITECTURE.md patterns)

### Phase 4: Deployment & Validation
**Rationale:** Production deployment with proper Docker configuration, environment templates, and testing against real Reddit API. Validates rate limit handling (Pitfall 1) under production conditions.
**Delivers:** Production Dockerfile, docker-compose.yml, .env.example, MCP Inspector testing, deployment documentation
**Addresses:** Docker deployment (from FEATURES.md table stakes), Moderation audit trail (from FEATURES.md differentiators)
**Validates:** Rate limit handling (Pitfall 1), timeout behavior (Pitfall 3)

### Phase Ordering Rationale

- **Foundation first:** Config/schemas are prerequisites for both Reddit module and MCP server; error handling middleware prevents security issues that are harder to retrofit
- **Reddit before MCP:** Testing Reddit API functions in isolation (with mocked PRAW) is easier than debugging through MCP protocol layer
- **MCP assembly wraps existing components:** FastMCP server integrates completed Reddit module with proper context injection — this is where AI-assisted triage logic lives
- **Deployment last:** Only after core functionality is proven do we optimize for production deployment and validate against real Reddit API rate limits

### Research Flags

**Phases likely needing deeper research during planning:**
- **Phase 2 (Reddit Integration):** Exact PRAW method signatures for current version — should verify against official docs during implementation
- **Phase 3 (MCP Server Assembly):** MCP HTTP transport implementation with FastMCP — while FastMCP is well-documented, specific timeout configuration and error handling patterns may need exploration

**Phases with standard patterns (skip research-phase):**
- **Phase 1 (Foundation):** Environment variable management, Docker basics, Pydantic models — all well-established patterns
- **Phase 4 (Deployment):** Docker deployment, docker-compose configuration — standard practices, no niche concerns

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All version-specific claims verified with official sources (MCP SDK GitHub, PRAW docs, PyPI) |
| Features | MEDIUM | Table stakes based on solid understanding of Reddit moderation; differentiators based on AI-assisted patterns that are novel but well-reasoned |
| Architecture | HIGH | All patterns verified against official MCP SDK documentation and FastMCP GitHub repository |
| Pitfalls | HIGH-MEDIUM | Rate limits, credential leakage, and ID validation backed by official PRAW docs; Docker issues are standard patterns |

**Overall confidence:** HIGH

### Gaps to Address

- **PRAW method signatures:** While the research identified the correct methods (modqueue, approve, remove, ban), exact signatures should be verified during Phase 2 implementation
- **FastMCP timeout configuration:** Research identified the need for timeouts but specific configuration values may require experimentation during Phase 3
- **Reddit rate limit specifics:** PRAW docs mention hidden rate limits but don't document exact thresholds — will need to test during Phase 4

## Sources

### Primary (HIGH confidence)
- [MCP Python SDK GitHub](https://github.com/modelcontextprotocol/python-sdk) — Official SDK with FastMCP integration, transport options, authentication
- [PRAW Documentation](https://praw.readthedocs.io/en/latest/) — PRAW 7.8.2 documentation, authentication, moderation API, rate limits
- [PRAW GitHub](https://github.com/praw-dev/praw) — Official repository, Python 3.9+ support
- [FastMCP GitHub](https://github.com/jlowin/fastmcp) — Standalone FastMCP framework, incorporated into official SDK
- [PyPI: mcp](https://pypi.org/pypi/mcp/json) — Version 1.26.0 verified
- [PyPI: praw](https://pypi.org/pypi/praw/json) — Version 7.8.2 verified

### Secondary (MEDIUM confidence)
- [uv Documentation](https://docs.astral.sh/uv/) — Package manager installation, project management
- [PyPI: uvicorn](https://pypi.org/pypi/uvicorn/json) — Version 0.41.0 verified
- [PyPI: starlette](https://pypi.org/pypi/starlette/json) — Version 0.52.1 verified
- [MCP Specification](https://spec.modelcontextprotocol.io/specification/) — Protocol requirements

### Tertiary (LOW confidence — web search unavailable)
- General knowledge of MCP protocol architecture and server patterns
- Understanding of Reddit moderation ecosystem (AutoMod, Toolbox)
- Familiarity with AI-assisted workflow patterns

---
*Research completed: 2025-03-11*
*Ready for roadmap: yes*
