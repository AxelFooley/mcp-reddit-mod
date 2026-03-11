# Pitfalls Research

**Domain:** MCP Server + Reddit API Integration (Moderation Tools)
**Researched:** 2025-03-11
**Confidence:** MEDIUM (Official documentation sources used, some findings based on documented behavior patterns)

## Critical Pitfalls

### Pitfall 1: Ignoring Reddit's Hidden Rate Limits

**What goes wrong:**
PRAW handles standard API rate limits automatically, but Reddit has additional undocumented rate limits for moderation actions (banning, removing, approving). These can trigger "You're doing that too much" errors that cause cascading failures across your MCP tools. Your bot appears to work fine during testing but fails mysteriously in production when moderating active subreddits.

**Why it happens:**
Developers assume PRAW's built-in rate limiting covers all Reddit API limits. The documentation explicitly states: "there are other unknown ratelimits that Reddit has that might require additional wait time (anywhere from milliseconds to minutes) for things such as commenting, editing comments/posts, banning users, adding moderators, etc."

**How to avoid:**
- Configure `ratelimit_seconds` appropriately (default is 5s, max wait before raising exception)
- Catch and handle `RedditAPIException` for rate limit errors in all moderation tools
- Implement exponential backoff for operations that fail with rate limit errors
- Consider adding delays between successive moderation actions even when PRAW doesn't trigger them

**Warning signs:**
- Intermittent `RedditAPIException` with "doing that too much" messages
- Works in testing but fails under load
- Errors correlate with batch operations on modqueue

**Phase to address:**
Phase 1 (MCP Server Foundation) - implement error handling wrapper for all PRAW calls

---

### Pitfall 2: Reddit Credentials Leaked in Error Messages

**What goes wrong:**
When tools fail due to authentication issues, error messages or stack traces accidentally expose Reddit credentials, client secrets, or session tokens. These get logged by the AI agent, sent in responses to users, or stored in conversation history.

**Why it happens:**
PRAW exceptions may include credential information in debug output. Developers print full exceptions for debugging without sanitization. The MCP protocol returns error details to clients by default.

**How to avoid:**
- Sanitize all exceptions before returning them through MCP tools
- Use environment variables exclusively (never pass credentials as function arguments)
- Implement error response filtering that removes sensitive fields
- Configure PRAW logging appropriately to avoid credential leakage
- Never include raw stack traces in tool responses

**Warning signs:**
- Error responses contain "client_id", "client_secret", or password fields
- Stack traces visible in AI agent conversation history
- Logging shows full authentication objects

**Phase to address:**
Phase 1 (MCP Server Foundation) - implement sanitized error handling middleware

---

### Pitfall 3: MCP Tool Blocking Causes Agent Hangs

**What goes wrong:**
A PRAW call blocks indefinitely (network hang, Reddit API timeout, streaming connection stall). The AI agent waits forever for the MCP tool response, causing the entire conversation to hang. Users perceive the system as frozen.

**Why it happens:**
PRAW's default timeout behavior may not align with MCP server expectations. Long-running operations like fetching large modqueues or streaming submissions can exceed client timeouts. No timeout wrapper is implemented around PRAW calls.

**How to avoid:**
- Implement timeout wrappers for all PRAW operations (recommend 30-60s maximum)
- Use non-blocking patterns for long-running operations
- Return partial results with continuation tokens for large datasets
- Configure FastMCP's HTTP transport with appropriate timeouts
- Test timeout behavior under poor network conditions

**Warning signs:**
- Tools sometimes return quickly but other times hang
- Behavior varies by network conditions
- Large subreddits cause more frequent hangs

**Phase to address:**
Phase 1 (MCP Server Foundation) - implement timeout middleware for all tool calls

---

### Pitfall 4: Subreddit Name Validation Missing

**What goes wrong:**
Invalid subreddit names (typos, private subreddits, non-existent, banned) cause tools to fail with cryptic errors. The AI agent doesn't understand why operations fail and provides unhelpful feedback to users. Common with user-provided subreddit names.

**Why it happens:**
PRAW doesn't validate subreddit names until you attempt to access them. Error messages like "redirect" or "Subreddit not found" aren't caught and translated into helpful MCP error responses. No pre-flight validation exists.

**How to avoid:**
- Implement subreddit validation before operations
- Check if subreddit exists and is accessible
- Verify moderator permissions before attempting mod-only operations
- Return clear error messages distinguishing between: not found, private, banned, no permissions
- Cache validation results to avoid repeated checks

**Warning signs:**
- Tools fail with confusing error messages
- "redirect" errors appearing in responses
- User typo in subreddit name causes cascade of failures

**Phase to address:**
Phase 2 (Reddit Integration) - implement subreddit validation utility

---

### Pitfall 5: Docker HTTP Transport Binding Issues

**What goes wrong:**
MCP server runs in Docker but AI agent cannot connect. Server binds to `127.0.0.1` inside container making it inaccessible externally. Or port conflicts prevent container startup. Or environment variables not properly passed to containerized PRAW instance.

**Why it happens:**
FastMCP's default binding may be `localhost` which only works inside container. Docker networking isn't properly configured. Environment variable configuration differs between local and containerized execution. Port mapping missing in docker-compose.

**How to avoid:**
- Explicitly bind to `0.0.0.0:8000` in FastMCP configuration
- Use docker-compose for consistent environment variable injection
- Document required environment variables in .env.example
- Test container networking from host before AI agent integration
- Include health check endpoint for container monitoring
- Use Docker networks properly if connecting to other services

**Warning signs:**
- Works locally but fails in Docker
- Connection refused from AI agent
- Container logs show server running but unreachable

**Phase to address:**
Phase 1 (MCP Server Foundation) - implement and test Docker deployment

---

### Pitfall 6: Thing ID Confusion and Type Mismatches

**What goes wrong:**
Operations fail because of wrong thing ID format (t1_ vs t3_ prefix missing/wrong). Approving a comment when expecting a post, or vice versa. Banning operations receive submission IDs instead of user IDs. AI agent doesn't understand Reddit's fullname system.

**Why it happens:**
Reddit uses "fullnames" (type prefix + base36 ID) like `t1_abc123` for comments, `t3_abc123` for posts, `t2_abc123` for users. Tools don't validate ID types. PRAW methods expect specific types but accept strings. No clear error messages when wrong type passed.

**How to avoid:**
- Validate thing ID format and type in all tools that accept IDs
- Return clear errors distinguishing "wrong format" vs "thing not found"
- Document expected ID types in tool descriptions
- Use PRAW's object model when possible instead of string IDs
- Implement helper functions to extract/validate type prefixes

**Warning signs:**
- "invalid fullname" errors from PRAW
- Operations silently succeed on wrong object type
- AI agent confused about ID formats

**Phase to address:**
Phase 2 (Reddit Integration) - implement ID validation helpers

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| No timeout on PRAW calls | Simpler error handling | Agent hangs, poor UX | Never - MCP requires responsive tools |
| Printing raw exceptions | Faster debugging | Credential leaks, security risk | Development only - sanitize before production |
| Hardcoded subreddit for testing | Faster iteration | Can't test multi-subreddit scenarios | MVP only - must parameterize before production |
| Skipping ID validation | Less code upfront | Confusing errors, harder debugging | Never - causes cascading failures |
| Ignoring rate limit config | Works in testing | Production failures under load | Never - documented in PRAW docs |
| Using default PRAW user agent | Less configuration | Harder to debug issues with Reddit | Never - Reddit requires descriptive user agents |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| PRAW Authentication | Passing credentials as arguments to `Reddit()` | Use environment variables or `praw.ini` file, never hardcode |
| Modqueue fetching | Assuming `limit=None` returns everything | Use pagination, limit results to avoid timeouts |
| Ban operations | Not checking if user is already banned | Check existing ban status first, handle gracefully |
| HTTP transport | Binding to `localhost` in Docker | Bind to `0.0.0.0` for external access |
| Error responses | Returning raw PRAW exceptions | Sanitize and translate to MCP-friendly errors |
| Subreddit access | Not verifying moderator permissions | Check permissions before mod-only operations |
| User history | Fetching all user submissions/comments | Filter by subreddit relevance to match scope |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Fetching entire modqueue at once | Tool timeouts on active subreddits | Implement pagination, limit results | Breaks at ~100+ items in queue |
| Streaming without limits | Memory grows indefinitely | Always use `limit` parameter on streams | Breaks after minutes of streaming |
| Repeated subreddit validation | Tools get slower with each call | Cache validation results | Noticeable after 10+ calls |
| No connection pooling | Slower response times under load | Let PRAW manage connections (default) | Under concurrent requests |
| Fetching user history without filters | Returns massive datasets | Filter by subreddit, date range | Breaks for power users |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Credentials in error messages | Credential theft via AI conversation logs | Sanitize all exceptions, filter sensitive fields |
| Trusting all subreddit inputs | Potential for unintended actions | Validate subreddit names, check permissions |
| No input validation on thing IDs | Potential for injection attacks | Validate ID format and type prefixes |
| Exposing full user data | Privacy violations | Return only necessary fields, respect Reddit's privacy model |
| Logging Reddit credentials | Credential leakage in logs | Never log credential objects, use secure logging |
| Open HTTP endpoint in production | Unauthorized access to moderation tools | Deploy behind network-level security as documented |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Cryptic Reddit API errors | Users don't know what went wrong | Translate errors to clear, actionable messages |
| Tools hang without feedback | Users think system is broken | Always return progress or timeout with clear message |
| No indication of rate limiting | Users don't understand why things are slow | Return rate limit info in tool responses |
| Confusing ID format errors | AI agent can't help users fix typos | Validate IDs early, return format hints |
| Silent permission failures | Operations appear to work but don't | Check permissions before operations, fail fast |

## "Looks Done But Isn't" Checklist

- [ ] **Modqueue tool:** Often missing pagination — verify with subreddits having 100+ queued items
- [ ] **Ban operations:** Often missing duration validation — verify both temporary and permanent bans work
- [ ] **User history:** Often missing proper filtering — verify it only returns flagged items, not all user content
- [ ] **HTTP transport:** Often missing Docker networking — verify AI agent can actually connect from outside container
- [ ] **Error handling:** Often missing sanitization — verify no credentials leak in any error response
- [ ] **Timeout configuration:** Often missing — verify tools return errors rather than hanging forever
- [ ] **Environment configuration:** Often missing .env.example — verify all required variables documented

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Rate limit exhaustion | LOW | Wait for limit to expire (minutes to hours), implement better rate limit handling |
| Credential exposure | HIGH | Immediately rotate Reddit credentials, review logs for exposure, implement sanitization |
| Subreddit validation missing | MEDIUM | Add validation layer, update tool descriptions, test with edge cases |
| Docker networking issues | LOW | Reconfigure port binding to `0.0.0.0`, test from host machine |
| Timeout issues | MEDIUM | Add timeout wrappers, test with poor network conditions, set reasonable defaults |
| ID type confusion | MEDIUM | Add validation helpers, update error messages, test with various ID types |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Ignoring hidden rate limits | Phase 1 - Error handling foundation | Test with rapid successive operations |
| Credential leakage in errors | Phase 1 - Secure error middleware | Verify all error responses are sanitized |
| MCP tool blocking/hangs | Phase 1 - Timeout implementation | Test with network delays and API hangs |
| Subreddit validation missing | Phase 2 - Reddit integration | Test with invalid, private, and non-existent subreddits |
| Docker HTTP binding issues | Phase 1 - Foundation deployment | Test from host machine and AI agent |
| Thing ID type confusion | Phase 2 - Input validation | Test with all ID types (t1, t2, t3, etc.) |

## Sources

- PRAW 7.7.1 Documentation - Ratelimits: https://praw.readthedocs.io/en/stable/getting_started/ratelimits.html
- PRAW 7.7.1 Documentation - Quick Start: https://praw.readthedocs.io/en/stable/getting_started/quick_start.html
- Reddit API Documentation: https://www.reddit.com/dev/api/
- FastMCP GitHub Repository: https://github.com/jlowin/fastmcp
- FastMCP Documentation - Installation: https://gofastmcp.com/getting-started/installation.md
- Project Context: .planning/PROJECT.md

**Confidence Notes:**
- HIGH: PRAW rate limiting behavior (official docs)
- HIGH: Reddit fullname/thing ID system (official API docs)
- HIGH: Docker networking requirements (standard practice)
- MEDIUM: MCP HTTP transport best practices (based on FastMCP docs and general HTTP server patterns)
- MEDIUM: Common failure patterns (based on documented API behaviors and standard integration issues)

---
*Pitfalls research for: MCP Server + Reddit API Integration (Moderation Tools)*
*Researched: 2025-03-11*
