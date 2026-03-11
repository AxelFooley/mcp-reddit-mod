# ItaliaCareerMod

## What This Is

A Python MCP (Model Context Protocol) server that exposes Reddit moderation tools via HTTP transport. Moderators can use AI assistants to review mod queue items, approve/remove content, ban users, and identify repeat offenders — all with human-in-the-loop confirmation for critical actions. Works with any subreddit.

## Core Value

AI-assisted Reddit moderation with human oversight. Automated review of mod queue items with intelligent repeat offender detection, while keeping humans in control of destructive actions.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] MCP server runs in Docker container with HTTP transport (not stdio)
- [ ] Server exposes `/mcp` endpoint on 0.0.0.0:8000 using Streamable HTTP
- [ ] `get_modqueue(subreddit)` — fetch current mod queue items via PRAW
- [ ] `approve_item(thing_id)` — approve a post or comment
- [ ] `remove_item(thing_id, reason)` — remove a post or comment with reason
- [ ] `ban_user(subreddit, username, reason, duration_days)` — ban user (duration=0 for permanent)
- [ ] `get_user_history(username, subreddit)` — fetch all posts/comments by user that were flagged in this subreddit
- [ ] Reddit credentials configurable via environment variables
- [ ] Errors propagate to AI agent/human for decision-making
- [ ] Dockerfile and docker-compose.yml provided
- [ ] .env.example file with all required variables

### Out of Scope

- **UI** — This is an API/protocol server, not a web interface
- **Database** — State stored in Reddit, no local persistence
- **HTTP authentication** — Runs in private homelab network, trust network-level security
- **Stdio transport** — HTTP only for easier integration with AI workflows
- **Multi-reddit batch operations** — Single-subreddit operations only per call

## Context

Reddit moderators face repetitive tasks reviewing mod queue items. AI assistants can help surface patterns and automate triage, but need programmatic access to Reddit actions. MCP provides the protocol bridge; this server provides the Reddit API bridge.

The `get_user_history` tool specifically targets repeat offender detection — showing what content from a user was previously flagged in the same subreddit, not just their general post history.

## Constraints

- **Transport**: HTTP (Streamable) — stdio not supported for Docker deployment
- **Python Version**: 3.11+ required for FastMCP compatibility
- **Reddit API**: PRAW library limits apply (rate limits, permissions)
- **PRAW Application Type**: Script app (user account tokens, not OAuth)
- **Network**: Must be accessible to AI agent (homelab/private network)
- **Environment**: All secrets via environment variables, no hardcoded credentials

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| HTTP vs stdio transport | Easier Docker deployment, AI agent can make HTTP calls independently | — Pending |
| FastMCP framework | Official MCP Python SDK, active development, good HTTP support | — Pending |
| No HTTP auth layer | Runs in private homelab network, trust network security | — Pending |
| User history = flagged items only | Focus on repeat offender detection for moderation, not general stalking | — Pending |

---
*Last updated: 2025-03-11 after initialization*
