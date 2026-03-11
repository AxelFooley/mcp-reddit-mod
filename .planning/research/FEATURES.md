# Feature Research

**Domain:** MCP Server + Reddit Moderation Tools
**Researched:** 2025-03-11
**Confidence:** LOW-MEDIUM (web search unavailable, findings based on general knowledge)

## Executive Summary

This research analyzes the feature landscape for MCP (Model Context Protocol) servers and Reddit moderation tools. **Web search tools experienced rate limits during research**, so findings are based on general knowledge of MCP protocol, PRAW library capabilities, and Reddit moderation ecosystem. Key findings indicate that basic moderation operations (approve, remove, ban) are table stakes, while AI-assisted triage and repeat offender detection represent significant differentiators.

**Critical insight:** Most Reddit moderation tools focus on rule-based automation. An AI-assisted approach with human-in-the-loop confirmation for destructive actions fills a gap between fully manual moderation and fully automated bots.

**Research limitation:** All web search and web fetch tools hit rate limits during this research. Findings should be validated against:
- Official PRAW documentation (https://praw.readthedocs.io/)
- Official MCP specification (https://modelcontextprotocol.io/)
- Current Reddit moderation tools (AutoMod, Toolbox)

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Basic CRUD moderation** | Any moderation tool must approve/remove content | LOW | PRAW provides `.approve()`, `.remove()`, `.delete()` methods |
| **User banning** | Core moderation capability | LOW | `subreddit.banned.add()` with duration support |
| **Modqueue access** | Moderators need to see flagged content | LOW | `subreddit.mod.modqueue()` returns stream of items |
| **User history lookup** | Essential for context on repeat offenders | MEDIUM | Need to filter user's contributions by moderation status |
| **Error handling** | API failures must surface to decision-maker | MEDIUM | PRAW exceptions (rate limits, permissions) must propagate |
| **Credential management** | Reddit API requires auth | LOW | Environment variables for client_id, client_secret, user_agent |
| **Transport layer** | MCP servers expose tools over protocol | LOW | HTTP transport required for Docker deployment |
| **Tool discovery** | MCP clients enumerate available tools | LOW | `@server.list_tools()` protocol requirement |

### Differentiators (Competitive Advantage)

Features that set the product apart. Not required, but valuable.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **AI-assisted triage** | LLM can summarize modqueue items and surface patterns | HIGH | Requires well-structured tool responses for AI consumption |
| **Repeat offender detection** | Targeted history (flagged items only) not general stalking | MEDIUM | Filter user activity by moderation action type |
| **Human-in-the-loop for destructive actions** | Safety layer preventing AI from taking irreversible actions | MEDIUM | Design tools to require explicit confirmation |
| **Contextual user profiles** | AI can build offender patterns from moderation history | MEDIUM | Aggregate flagged items across time |
| **Batch operation awareness** | AI can suggest related actions (e.g., "ban + remove all their posts") | HIGH | Requires careful design to prevent cascading errors |
| **Explainable moderation** | AI provides rationale for actions before execution | MEDIUM | Tool responses should include reasoning |
| **Multi-subreddit awareness** | Same user causing issues across communities | HIGH | Out of scope for v1, but powerful differentiator |
| **Moderation audit trail** | All AI-suggested actions logged for review | MEDIUM | Critical for trust and debugging |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem good but create problems.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| **Fully autonomous bans** | "Set and forget" moderation | High risk of false positives, community backlash | Human-in-the-loop confirmation for bans |
| **Real-time monitoring** | Catch issues immediately | Requires WebSocket/long-polling, complexity explosion | Periodic modqueue polling (existing pattern) |
| **Sentiment analysis** | Auto-detect toxic content | LLM hallucinations, context dependence, bias risks | Pattern-based rules (existing AutoMod) |
| **Karma-based auto-actions** | "Low karma = spam" | Gaming vulnerability, false positives on new users | Manual review with AI assistance |
| **Multi-reddit batch operations** | "Ban from all my subs at once" | Coordination complexity, permission matrix explosion | Single-subreddit operations, chain tools in AI workflow |
| **Built-in UI** | "Visual interface for moderation" | Out of scope for MCP server, bloats codebase | Let AI clients provide UI (Claude, ChatGPT, etc.) |
| **Local state/database** | "Remember decisions for ML" | Adds persistence complexity, drift from Reddit source | Use Reddit as source of truth, optional sidecar logging |
| **OAuth flow** | "More secure than script app" | OAuth adds redirect server complexity, overkill for homelab | Script app (user tokens) with network-level security |

---

## Feature Dependencies

```
[Reddit API Authentication]
    └──requires──> [PRAW Client Configuration]
                       └──requires──> [Environment Variable Setup]

[Modqueue Access]
    └──requires──> [Reddit API Authentication]
    └──requires──> [Subreddit Moderator Permissions]

[Approve/Remove Operations]
    └──requires──> [Reddit API Authentication]
    └──requires──> [Thing ID Validation]

[User Banning]
    └──requires──> [Reddit API Authentication]
    └──requires──> [Subreddit Moderator Permissions]

[User History Lookup]
    └──requires──> [Reddit API Authentication]
    └──requires──> [User Activity Filtering Logic]

[AI-Assisted Triage]
    └──enhances──> [Modqueue Access]
    └──enhances──> [User History Lookup]

[Human-in-the-Loop Confirmation]
    └──requires──> [Destructive Action Detection]
    └──conflicts──> [Fully Autonomous Mode]
```

### Dependency Notes

- **Reddit API Authentication requires PRAW Client Configuration:** Must provide valid credentials before any API calls. PRAW's `Reddit()` constructor needs client_id, client_secret, user_agent, username, password.
- **Modqueue Access requires Subreddit Moderator Permissions:** User account must have mod permissions on target subreddit, or API returns 403 Forbidden.
- **User History Lookup requires User Activity Filtering Logic:** PRAW returns all user contributions; need to filter by `.removed()` or `.approved()` status to find previously flagged items.
- **AI-Assisted Triage enhances Modqueue Access:** Raw modqueue data needs structure for AI consumption (summaries, metadata extraction).
- **Human-in-the-Loop Confirmation conflicts with Fully Autonomous Mode:** Design choice — either require confirmation for destructive actions or don't. Can't support both well in same architecture.

---

## MVP Definition

### Launch With (v1)

Minimum viable product — what's needed to validate the concept.

- [ ] **HTTP MCP server transport** — Core requirement for Docker deployment, enables AI agents to call tools independently
- [ ] **Modqueue fetch tool** — `get_modqueue(subreddit)` returns current queue items with metadata
- [ ] **Basic moderation actions** — `approve_item(thing_id)`, `remove_item(thing_id, reason)` for content triage
- [ ] **User banning tool** — `ban_user(subreddit, username, reason, duration_days)` with permanent/temporary support
- [ ] **User history lookup** — `get_user_history(username, subreddit)` returns previously flagged items for repeat offender detection
- [ ] **Environment-based auth** — All Reddit credentials via environment variables, no hardcoded secrets
- [ ] **Error propagation** — PRAW exceptions surface to AI agent for decision-making
- [ ] **Docker deployment** — Dockerfile + docker-compose.yml for homelab deployment

**Why these features for MVP:**
- Validates MCP-over-HTTP for Reddit moderation
- Tests AI-assisted workflow (review → suggest → human confirms)
- Covers core moderation loop (detect → triage → action)
- Minimal dependencies (no database, no OAuth)

### Add After Validation (v1.x)

Features to add once core is working.

- [ ] **Audit logging** — Log all AI-suggested actions to file for review (trigger: need to debug AI decisions)
- [ ] **Bulk operations** — `ban_user_and_remove_content(username)` compound action (trigger: users request efficiency)
- [ ] **Modmail integration** — `get_modmail()` and `reply_modmail()` tools (trigger: moderators need message triage)
- [ ] **Flair management** — `set_flair()` and user flair tools (trigger: post-approval workflow needs)
- [ ] **Rate limit awareness** — Exponential backoff and retry logic (trigger: hitting PRAW rate limits in production)

### Future Consideration (v2+)

Features to defer until product-market fit is established.

- [ ] **Multi-subreddit operations** — Cross-subreddit ban detection and coordinated actions (why defer: permission matrix complexity)
- [ ] **ML-based pattern detection** — Train models on moderation history to predict spam (why defer: requires labeled data, adds ML ops burden)
- [ ] **Webhook support** — Reddit pushes events instead of polling (why defer: requires public endpoint, adds infrastructure)
- [ ] **OAuth authentication** — Support OAuth flow instead of script app (why defer: adds redirect server, complexity vs benefit unclear for homelab)

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| HTTP MCP server transport | HIGH | LOW | P1 |
| Modqueue fetch | HIGH | LOW | P1 |
| Approve/remove operations | HIGH | LOW | P1 |
| User banning | HIGH | LOW | P1 |
| User history lookup (flagged only) | HIGH | MEDIUM | P1 |
| Environment-based auth | HIGH | LOW | P1 |
| Error propagation | HIGH | MEDIUM | P1 |
| Docker deployment | HIGH | LOW | P1 |
| Audit logging | MEDIUM | LOW | P2 |
| Bulk operations | MEDIUM | MEDIUM | P2 |
| Modmail integration | MEDIUM | LOW | P2 |
| Flair management | LOW | LOW | P3 |
| Multi-subreddit operations | HIGH | HIGH | P3 |
| ML-based pattern detection | MEDIUM | HIGH | P3 |
| Webhook support | MEDIUM | HIGH | P3 |
| OAuth authentication | LOW | MEDIUM | P3 |

**Priority key:**
- P1: Must have for launch
- P2: Should have, add when possible
- P3: Nice to have, future consideration

---

## Competitor Feature Analysis

| Feature | Reddit AutoMod | Reddit Toolbox | Moderation Bots | Our Approach |
|---------|---------------|----------------|-----------------|--------------|
| **Auto-removal** | Rule-based config | Manual | Scripted | AI-suggested with human confirmation |
| **User banning** | Yes (temp ban) | Yes (manual) | Yes (automated) | Yes (AI-suggested, human confirmed) |
| **User history** | No (general only) | Yes (user profile) | Varied | Yes (flagged items only, repeat offender focus) |
| **Modqueue triage** | Native interface | Enhanced UI | Bot commands | AI-summarized with pattern detection |
| **Multi-subreddit** | Per-sub config | Per-sub UI | Some support | Single-subreddit per call (v1), future consideration |
| **Audit trail** | Reddit logs | Toolbox logs | Bot logs | Optional sidecar logging for AI decisions |
| **Authentication** | Reddit native | Reddit native | Script app | Script app (environment-based) |
| **Transport** | Reddit web | Browser extension | Standalone | MCP over HTTP (AI agent integration) |

**Key differentiation:** Our tool is **AI-first** with **human-in-the-loop**. AutoMod is rule-based (no AI), Toolbox is UI-enhanced (manual), bots are scripted (fully automated). We're the only one designed for AI-assisted workflow where AI suggests and human confirms.

---

## MCP Server Feature Analysis

Based on Model Context Protocol architecture:

### Standard MCP Server Features (Table Stakes)

| Feature | Purpose | Why Expected |
|---------|---------|--------------|
| **Tool enumeration** | `list_tools()` protocol method | Clients discover available capabilities |
| **Tool calling** | `call_tool()` protocol method | Core interaction pattern |
| **Resource listing** | `list_resources()` if applicable | Some servers expose data resources |
| **Server metadata** | Name, version, description | Client displays server info |
| **Error handling** | Structured error responses | Protocol requirement |
| **Transport support** | stdio or HTTP | Integration flexibility |

### Advanced MCP Features (Differentiators)

| Feature | Purpose | Value |
|---------|---------|-------|
| **Streaming responses** | Incremental results for long operations | Better UX for modqueue fetches |
| **Tool metadata schemas** | Input/output JSON schemas | Strong typing, better AI understanding |
| **Resource subscriptions** | Push updates on data changes | Real-time modqueue updates (future) |
| **Prompt templates** | Pre-built AI prompts | Consistent AI interactions |
| **Tool permissions** | Scoped access control | Safety for destructive actions |

### Our MCP Server Design

**Transport:** HTTP only (stdio explicitly out of scope for Docker deployment)

**Tools to expose:**
1. `get_modqueue(subreddit: str) -> list[ModqueueItem]`
2. `approve_item(thing_id: str) -> SuccessResult`
3. `remove_item(thing_id: str, reason: str) -> SuccessResult`
4. `ban_user(subreddit: str, username: str, reason: str, duration_days: int) -> SuccessResult`
5. `get_user_history(username: str, subreddit: str) -> list[UserActivity]`

**Resources:** None (Reddit is source of truth, no local caching in v1)

**Prompts:** None (let AI client build prompts based on tool outputs)

---

## Sources

**Research Limitations:**

All web search and web fetch tools (WebSearch, webReader) hit rate limits during this research. The following sources were attempted but unavailable:

- https://praw.readthedocs.io/ (PRAW official documentation)
- https://github.com/modelcontextprotocol/servers (MCP server examples)
- https://github.com/praw-dev/praw (PRAW GitHub repository)
- Web searches for "MCP server features", "Reddit moderation tools", "PRAW features"

**Findings are based on:**
- General knowledge of MCP (Model Context Protocol) architecture and server patterns
- Understanding of PRAW (Python Reddit API Wrapper) library and common moderation use cases
- Familiarity with Reddit moderation ecosystem (AutoMod, Toolbox, moderation bots)

**Confidence Level: LOW-MEDIUM**
- Table stakes features: MEDIUM confidence (based on understanding of Reddit moderation basics)
- MCP server features: LOW-MEDIUM confidence (general protocol knowledge, but specifics need verification)
- Differentiators: LOW confidence (AI-assisted moderation is novel, limited direct comparisons)
- Anti-features: MEDIUM confidence (based on common patterns in tool design)

**Recommended Validation:**
1. Review PRAW documentation at https://praw.readthedocs.io/ for exact method signatures
2. Review MCP specification at https://modelcontextprotocol.io/ for protocol requirements
3. Survey r/modsupport and r/toolbox for current moderator workflows and pain points
4. Test PRAW methods in Python REPL to verify exact API behavior
5. Review FastMCP documentation for HTTP transport implementation details

**Areas requiring phase-specific research:**
- Exact PRAW method signatures for current version
- MCP HTTP transport implementation with FastMCP
- Reddit API rate limits for script applications
- Optimal data structures for AI consumption (modqueue items, user history)

---
*Feature research for: MCP Server + Reddit Moderation Tools*
*Researched: 2025-03-11*
*Confidence: LOW-MEDIUM (web search unavailable)*
