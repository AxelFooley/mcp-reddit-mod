# Stack Research

**Domain:** MCP Server with Reddit API Integration
**Researched:** 2025-03-11
**Confidence:** HIGH

## Executive Summary

The standard 2025 stack for building Python MCP servers with Reddit API integration centers on the **official MCP Python SDK (v1.26.0)** which now includes **FastMCP** as the recommended framework. For Reddit integration, **PRAW 7.8.2+** remains the authoritative library with full moderation API support. The stack prioritizes **HTTP transport (Streamable HTTP)** over stdio for Docker deployments, uses **uvicorn 0.41.0 + Starlette 0.52.1** for ASGI server capabilities, and adopts **uv** for Python package management due to its 10-100x performance improvement over pip.

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| **mcp** (Python SDK) | 1.26.0+ | Official MCP protocol implementation with FastMCP framework | FastMCP is the standard framework for MCP—70% of MCP servers across all languages use some version of FastMCP. Official SDK with active development, built-in HTTP transport support, and type-safe tool definitions. |
| **PRAW** | 7.8.2+ | Python Reddit API Wrapper for moderation actions | Official Reddit API wrapper with automatic rate limiting, full moderation API support (modqueue, approve/remove, ban user), script app authentication (no OAuth complexity). Python 3.9+ support. |
| **Python** | 3.11+ | Runtime language | Minimum requirement for FastMCP compatibility. Python 3.12+ recommended for better performance and typing features. |
| **uvicorn** | 0.41.0+ | ASGI server for HTTP transport | Lightning-fast ASGI server, production-ready, supports Gunicorn integration for multi-worker deployments. |
| **Starlette** | 0.52.1+ | ASGI toolkit for mounting MCP servers | Officially supported by MCP SDK for mounting FastMCP servers. Enables custom routing, middleware (CORS), and integration with other ASGI apps. |

### Package Management

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| **uv** | Latest | Python package and project manager | 10-100x faster than pip, single tool replacing pip/pip-tools/pipx/poetry/pyenv/virtualenv, universal lockfile, Rust-based for reliability. Recommended by MCP SDK documentation. |
| **python-dotenv** | 1.2.2 | Environment variable management from .env files | Industry standard for loading secrets from .env files, essential for credential management (Reddit API keys). |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| **MCP Inspector** | Development and testing of MCP servers | Official CLI tool: `npx -y @modelcontextprotocol/inspector` - Connect to HTTP endpoints to test tools/resources/prompts |
| **Ruff** | Python linting and formatting | Fast Rust-based linter, integrates with uv, replaces multiple linting tools |
| **pytest** | Testing framework | Async test support for testing MCP server tools |
| **pre-commit** | Git hooks for code quality | Officially supported in MCP SDK repository |

### Docker Infrastructure

| Component | Version | Purpose | Notes |
|-----------|---------|---------|-------|
| **python:3.12-slim** | Latest | Base Docker image | Official slim image, smaller footprint, includes Python 3.12 for FastMCP compatibility |
| **docker-compose** | Latest | Container orchestration | Simplified local development and deployment |

## Installation

```bash
# Initialize project with uv
uv init italia-career-mod
cd italia-career-mod

# Add core dependencies
uv add "mcp>=1.26.0"
uv add "praw>=7.8.2"
uv add "python-dotenv>=1.2.2"

# Add development dependencies
uv add --dev uvicorn starlette pytest ruff

# Alternative: Install all at once
uv add "mcp>=1.26.0" "praw>=7.8.2" "python-dotenv>=1.2.2" "uvicorn>=0.41.0" "starlette>=0.52.1"
```

### Docker Installation

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy dependency files
COPY requirements.txt .
# Or use pyproject.toml if using uv

# Install dependencies
RUN uv pip install --system -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run the server
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| **mcp (official SDK)** | Standalone FastMCP (jlowin/fastmcp) | Use standalone FastMCP v2 for stability (pin: `fastmcp<3`). v3 is RC. Official SDK integrates FastMCP v1.x, which is stable and production-ready. |
| **PRAW (synchronous)** | Async PRAW (apraw) | Only consider if async-first architecture is critical. PRAW can be wrapped in `asyncio.to_thread()` for concurrent operations. Async PRAW has limited maintenance. |
| **HTTP transport** | stdio transport | Use stdio only for local CLI integrations (Claude Desktop). HTTP required for Docker deployments and remote AI agents. |
| **uvicorn** | hypercorn, daphne | Uvicorn is faster and more widely adopted. Hypercorn for HTTP/2 support only if needed. |
| **uv** | pip, poetry, rye | uv is significantly faster and replaces all these tools. Poetry for complex dependency resolution only. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| **PRAW < 7.0** | Missing moderation API features, outdated rate limit handling | PRAW 7.8.2+ |
| **python:3.11-slim (Docker)** | Python 3.12 has better typing and performance, FastMCP optimized for 3.11+ | python:3.12-slim |
| **pip for dependency management** | 10-100x slower than uv, no lockfile support, fragmented tooling | uv (universal lockfile, faster) |
| **Standalone FastMCP v3** | Currently release candidate (3.0.0rc1), not production-stable | Official mcp SDK (includes FastMCP v1.x) or pin `fastmcp<3` |
| **OAuth app type for Reddit** | Requires redirect URI setup, token refresh logic, unnecessary complexity | Script app type (user account tokens via password) |
| **Raw HTTP calls to Reddit API** | Manual rate limiting, authentication handling, error recovery | PRAW (handles all Reddit API quirks automatically) |
| **SSE transport** | Being superseded by Streamable HTTP, less scalable | Streamable HTTP (stateless mode with JSON responses) |

## Stack Patterns by Variant

**If building for production with multiple servers:**
- Use FastMCP with `stateless_http=True, json_response=True` for optimal scalability
- Mount multiple servers in a Starlette application with different paths
- Implement proper CORS for browser-based clients

**If building for Claude Desktop integration:**
- Use stdio transport for direct integration
- Follow MCP SDK install command: `uv run mcp install server.py`
- Environment variables via `-v` flag or `-f .env`

**If building for Docker homelab deployment:**
- Use Streamable HTTP transport on 0.0.0.0:8000
- Expose `/mcp` endpoint
- Configure Reddit credentials via environment variables
- No HTTP auth (trust network-level security per project constraints)

## Version Compatibility

| Package | Compatible With | Notes |
|-----------|-----------------|-------|
| mcp 1.26.0 | Python 3.11+, Starlette 0.52.1+, uvicorn 0.41.0+ | Requires Python 3.11 minimum for FastMCP |
| PRAW 7.8.2 | Python 3.9+, Reddit API (any current version) | Supports script and OAuth apps |
| uvicorn 0.41.0 | Python 3.8+, ASGI3 applications | Compatible with all MCP server types |
| python-dotenv 1.2.2 | Python 3.8+ | Standard .env file loading |

## FastMCP Configuration for Reddit MCP Server

```python
from mcp.server.fastmcp import FastMCP
import praw
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize Reddit client
reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    password=os.getenv("REDDIT_PASSWORD"),
    user_agent=os.getenv("REDDIT_USER_AGENT"),
    username=os.getenv("REDDIT_USERNAME"),
)

# Create MCP server with recommended settings
mcp = FastMCP(
    "ItaliaCareerMod",
    stateless_http=True,  # Recommended for production
    json_response=True,   # JSON responses for better client compatibility
)

@mcp.tool()
def get_modqueue(subreddit: str) -> str:
    """Fetch current mod queue items for a subreddit."""
    # Implementation using PRAW
    pass

# Run with Streamable HTTP transport
if __name__ == "__main__":
    mcp.run(transport="streamable-http")
```

## Environment Variables (.env.example)

```bash
# Reddit API Credentials (Script App Type)
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USERNAME=your_reddit_username
REDDIT_PASSWORD=your_reddit_password
REDDIT_USER_AGENT=script:italia-career-mod:v1.0 (by /u/your_username)

# Server Configuration
MCP_HOST=0.0.0.0
MCP_PORT=8000
```

## Sources

### HIGH Confidence (Official Documentation)
- [MCP Python SDK GitHub](https://github.com/modelcontextprotocol/python-sdk) — Official SDK with FastMCP integration, transport options, authentication
- [FastMCP GitHub](https://github.com/jlowin/fastmcp) — Standalone FastMCP framework, incorporated into official SDK
- [PRAW Documentation](https://praw.readthedocs.io/en/latest/) — PRAW 7.8.2 documentation, authentication, moderation API
- [PRAW GitHub](https://github.com/praw-dev/praw) — Official repository, Python 3.9+ support, installation
- [uv Documentation](https://docs.astral.sh/uv/) — Package manager installation, project management, pip interface
- [PyPI: mcp](https://pypi.org/pypi/mcp/json) — Version 1.26.0 verified
- [PyPI: praw](https://pypi.org/pypi/praw/json) — Version 7.8.2 verified
- [PyPI: uvicorn](https://pypi.org/pypi/uvicorn/json) — Version 0.41.0 verified
- [PyPI: starlette](https://pypi.org/pypi/starlette/json) — Version 0.52.1 verified
- [PyPI: python-dotenv](https://pypi.org/pypi/python-dotenv/json) — Version 1.2.2 verified

### MEDIUM Confidence (Web Search - Rate Limited)
- Due to rate limit exhaustion on 2025-03-11, some web searches were unavailable. All critical information verified from official documentation above.

### LOW Confidence (Training Data - Avoided)
- No recommendations based solely on training data. All version-specific claims verified with official sources or PyPI.

---
*Stack research for: MCP Server with Reddit API Integration*
*Researched: 2025-03-11*
