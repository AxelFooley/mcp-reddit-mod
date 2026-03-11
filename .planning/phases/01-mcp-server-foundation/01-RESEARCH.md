# Phase 1: MCP Server Foundation - Research

**Researched:** 2026-03-11
**Domain:** Model Context Protocol (MCP) server with HTTP transport, Docker deployment
**Confidence:** HIGH

## Summary

The Model Context Protocol (MCP) is a standardized protocol for LLM context exposure, similar to web APIs but specifically designed for AI interactions. The MCP Python SDK (v1.26.0) provides `FastMCP` - a high-level server abstraction that handles protocol compliance, connection management, and message routing through decorator-based tool registration.

For Docker deployment, the Streamable HTTP transport is the recommended approach (superseding SSE transport). It exposes an `/mcp` endpoint that handles bidirectional JSON-RPC communication over HTTP with optional SSE streaming for long-running operations. The SDK uses uvicorn (ASGI server) and starlette (routing framework) under the hood.

**Primary recommendation:** Use FastMCP with `transport="streamable-http"` for the server foundation, uv for package management, and a multi-stage Dockerfile with python:3.12-slim base image.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| MCPF-01 | MCP server uses Streamable HTTP transport (not stdio) for Docker deployment | FastMCP.run(transport="streamable-http") - SDK built-in support |
| MCPF-02 | Server exposes `/mcp` endpoint on 0.0.0.0:8000 for external access | Default endpoint for streamable-http, configurable via uvicorn --host |
| MCPF-03 | Server implements tool discovery protocol (`list_tools()` method) | FastMCP auto-implements via @mcp.tool() decorator |
| MCPF-04 | Server provides metadata (name, version, description) to clients | InitializationOptions passed to FastMCP constructor |
| MCPF-05 | Server returns structured error responses per MCP protocol | SDK handles JSON-RPC error format automatically |
| DEPL-01 | Dockerfile uses `python:3.12-slim` base image | Per requirement, matches SDK Python 3.10+ support |
| DEPL-02 | Dockerfile includes uv package manager for dependency installation | uv pip install, uv sync commands available |
| DEPL-03 | docker-compose.yml provided for homelab deployment | Standard docker-compose format |
| DEPL-04 | `.env.example` file includes all 5 required Reddit credential variables | PRAW credentials: CLIENT_ID, CLIENT_SECRET, USERNAME, PASSWORD, USER_AGENT |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| mcp | 1.26.0 | MCP Python SDK | Official SDK, handles protocol compliance |
| FastMCP | (included in mcp) | High-level server API | Decorator-based tool registration, simpler than low-level Server |
| uvicorn | >=0.31.1 | ASGI server | Runtime for starlette apps, used by MCP SDK |
| starlette | >=0.27 (Python <3.14) | ASGI framework | Routing, HTTP handling, SSE support |
| sse-starlette | >=3.0.0 | SSE support | Server-Sent Events for streaming responses |
| pydantic | >=2.11.0,<3.0.0 | Data validation | JSON-RPC message parsing, type safety |
| anyio | >=4.5 | Async compatibility | Abstraction over asyncio/trio |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| python-dotenv | >=1.0.0 | Environment variables | Loading .env files for credentials |
| httpx | >=0.27.1 | HTTP client | For MCP client implementations (future) |
| httpx-sse | >=0.4 | SSE client | For consuming SSE streams (future) |

### Installation
```bash
# Create project with uv
uv init italia-career-mod
cd italia-career-mod

# Add MCP with CLI extras (includes python-dotenv)
uv add "mcp[cli]"

# Or for pip projects:
pip install "mcp[cli]"
```

**uv alternative:**
```bash
# Install uv if not present
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create project and add dependencies
uv init italia-career-mod
uv add "mcp[cli]"
```

### Python Version Support
- **Minimum:** Python 3.10
- **Recommended:** Python 3.12 (matches requirement DEPL-01)
- **Tested:** Python 3.10, 3.11, 3.12, 3.13, 3.14 (as per SDK classifiers)

## Architecture Patterns

### Recommended Project Structure
```
src/
├── __init__.py
├── server.py           # FastMCP server instance, tool registration
├── config.py           # Environment loading, constants
└── main.py             # Entry point, server.run() invocation
tests/
├── __init__.py
├── conftest.py         # Pytest fixtures
└── test_server.py      # Server tests
pyproject.toml          # uv project config, dependencies
.env.example            # Reddit credential template
Dockerfile              # Multi-stage build
docker-compose.yml      # Homelab deployment
README.md               # Setup instructions
```

### Pattern 1: FastMCP Server with Streamable HTTP
**What:** Create an MCP server using FastMCP decorator pattern with HTTP transport
**When to use:** All MCP server implementations requiring Docker deployment
**Example:**
```python
# Source: https://raw.githubusercontent.com/modelcontextprotocol/python-sdk/v1.12.0/examples/snippets/servers/streamable_config.py
from mcp.server.fastmcp import FastMCP

# Create server with metadata
mcp = FastMCP("ItaliaCareerMod", description="Reddit moderation MCP server")

# Register tool using decorator
@mcp.tool()
def example_tool(param: str) -> str:
    """Tool description visible to LLM clients."""
    return f"Result: {param}"

# Run with streamable HTTP (exposes /mcp endpoint)
if __name__ == "__main__":
    mcp.run(transport="streamable-http")
```

### Pattern 2: Server Initialization Options
**What:** Configure server metadata and capabilities during initialization
**When to use:** Setting server identity, capabilities, description
**Example:**
```python
# Source: mcp/server/models.py
from mcp.server.fastmcp import FastMCP
from mcp.server.models import InitializationOptions
from mcp.types import ServerCapabilities

# Method 1: Direct to FastMCP (metadata auto-set)
mcp = FastMCP(
    name="ItaliaCareerMod",
    description="AI-assisted Reddit moderation for r/italycareer",
    version="0.1.0"
)

# Method 2: Via InitializationOptions (low-level Server class)
from mcp.server import Server

server = Server(
    InitializationOptions(
        server_name="ItaliaCareerMod",
        server_version="0.1.0",
        description="AI-assisted Reddit moderation",
        capabilities=ServerCapabilities(
            tools={},  # Empty in Phase 1, populated in Phase 3
            resources={},
            prompts={}
        )
    )
)
```

### Pattern 3: Environment Configuration
**What:** Load credentials from environment using python-dotenv
**When to use:** All credential and configuration loading
**Example:**
```python
# Source: Standard python-dotenv pattern
import os
from dotenv import load_dotenv

load_dotenv()  # Loads .env file into os.environ

REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USERNAME = os.getenv("REDDIT_USERNAME")
REDDIT_PASSWORD = os.getenv("REDDIT_PASSWORD")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "italia-career-mod/0.1.0")

# Validate required vars
required_vars = ["REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET", "REDDIT_USERNAME", "REDDIT_PASSWORD"]
missing = [var for var in required_vars if not os.getenv(var)]
if missing:
    raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
```

### Pattern 4: Docker with uv
**What:** Multi-stage Docker build using uv for fast dependency installation
**When to use:** All Docker deployments using Python
**Example:**
```dockerfile
# Source: uv Docker best practices (inferred from SDK patterns)
FROM python:3.12-slim AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml ./

# Install dependencies (frozen for reproducibility)
RUN uv pip install --system -e .

# Final stage
FROM python:3.12-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY src/ /app/src/

# Expose MCP endpoint port
EXPOSE 8000

# Run server (bind to 0.0.0.0 for Docker access)
CMD ["python", "-m", "src.main"]
```

### Pattern 5: Docker Compose for Homelab
**What:** Define service, environment, and port mapping
**When to use:** Local development and homelab deployment
**Example:**
```yaml
# Source: Standard docker-compose pattern
services:
  mcp-server:
    build: .
    ports:
      - "8000:8000"  # Expose /mcp endpoint on host port 8000
    environment:
      - REDDIT_CLIENT_ID=${REDDIT_CLIENT_ID}
      - REDDIT_CLIENT_SECRET=${REDDIT_CLIENT_SECRET}
      - REDDIT_USERNAME=${REDDIT_USERNAME}
      - REDDIT_PASSWORD=${REDDIT_PASSWORD}
      - REDDIT_USER_AGENT=${REDDIT_USER_AGENT}
    env_file:
      - .env  # Load from .env file in project root
    restart: unless-stopped
```

### Anti-Patterns to Avoid
- **Using stdio transport:** Not suitable for Docker deployment (use streamable-http)
- **Binding to 127.0.0.1:** Prevents external Docker access (use 0.0.0.0)
- **Hardcoding credentials:** Always use environment variables
- **Using SSE transport:** Superseded by streamable-http for production
- **Installing with pip in Docker:** Use uv for faster builds
- **Exposing all ports:** Only expose 8000 for the MCP endpoint

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| MCP protocol handling | Custom JSON-RPC parsing | FastMCP / Server class | Protocol compliance, version negotiation, error handling |
| HTTP endpoint routing | Custom FastAPI/Starlette app | FastMCP.run(transport="streamable-http") | Built-in routing, SSE streaming, session management |
| Tool registration system | Custom decorator/parser | @mcp.tool() decorator | Type-safe, auto-discovery, schema generation |
| Async server lifecycle | Custom lifespan management | FastMCP lifespan parameter | Proper startup/shutdown, resource cleanup |
| Environment variable loading | Custom .env parser | python-dotenv | Standard, well-tested, handles edge cases |
| Dependency resolution | pip with complex requirements.txt | uv with pyproject.toml | Faster, deterministic, lockfile support |

**Key insight:** The MCP SDK implements the full protocol specification including edge cases like version negotiation (2025-11-25), error codes (PARSE_ERROR -32700, INVALID_REQUEST -32600, etc.), and structured responses. Building this manually would require implementing hundreds of lines of protocol code.

## Common Pitfalls

### Pitfall 1: Binding to localhost instead of 0.0.0.0
**What goes wrong:** Server starts but is inaccessible from outside Docker container
**Why it happens:** Default bind address is often 127.0.0.1 (localhost only)
**How to avoid:** Explicitly bind to 0.0.0.0 in uvicorn config
```python
# Correct
if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)

# Wrong (inaccessible from Docker)
if __name__ == "__main__":
    mcp.run(transport="streamable-http")  # Binds to 127.0.0.1 by default
```
**Warning signs:** `curl: (7) Failed to connect to localhost port 8000` from host machine

### Pitfall 2: Missing SSE/HTTP Dependencies
**What goes wrong:** ImportError for sse_starlette or uvicorn
**Why it happens:** Installing bare `mcp` without transport extras
**How to avoid:** Install with extras or verify dependencies
```bash
# Correct
uv add "mcp[cli]"  # Includes all needed dependencies

# Verify dependencies
uv pip list | grep -E "uvicorn|starlette|sse-starlette"
```
**Warning signs:** `ModuleNotFoundError: No module named 'sse_starlette'`

### Pitfall 3: Not Handling Missing Environment Variables
**What goes wrong:** Server starts but crashes when accessing credentials
**Why it happens:** Assuming .env file exists or variables are set
**How to avoid:** Validate at startup, fail fast with clear message
```python
def load_config():
    load_dotenv()
    required = ["REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET", "REDDIT_USERNAME", "REDDIT_PASSWORD"]
    missing = [var for var in required if not os.getenv(var)]
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}. "
                        f"Copy .env.example to .env and fill in values.")
```
**Warning signs:** `AttributeError: 'NoneType' object has no attribute 'upper'`

### Pitfall 4: Docker Build Caching Issues with uv
**What goes wrong:** Old dependencies cached, changes not reflected
**Why it happens:** Docker layer caching without proper cache invalidation
**How to avoid:** Copy pyproject.toml separately, use --no-cache when needed
```dockerfile
# Correct order - separate dependency layer
COPY pyproject.toml ./
RUN uv pip install --system -e .

# Then copy code (code changes won't reinstall deps)
COPY src/ /app/src/

# For fresh builds
# docker compose build --no-cache
```
**Warning signs:** Changes in pyproject.toml not reflected in running container

### Pitfall 5: Incorrect .env File Placement
**What goes wrong:** Environment variables not loaded in Docker container
**Why it happens:** .env file not in Docker build context or not mounted
**How to avoid:** Use env_file in docker-compose.yml, verify file exists
```yaml
# Correct
services:
  mcp-server:
    env_file:
      - .env  # Must exist in same directory as docker-compose.yml
```
**Warning signs:** Server fails with "Missing required environment variables"

### Pitfall 6: JSON-RPC Response Format Errors
**What goes wrong:** Clients can't parse responses, protocol violations
**Why it happens:** Manually constructing JSON-RPC responses without SDK
**How to avoid:** Always return from tool functions, let SDK handle wrapping
```python
# Correct - SDK wraps in JSON-RPC response
@mcp.tool()
def my_tool() -> str:
    return "result"  # SDK wraps: {"jsonrpc": "2.0", "id": 1, "result": {"content": [{"type": "text", "text": "result"}]}}

# Wrong - manual wrapping, double-encoding
@mcp.tool()
def my_tool() -> dict:
    return {"jsonrpc": "2.0", "result": "result"}  # SDK wraps again, causing protocol error
```
**Warning signs:** Client error: "Invalid JSON-RPC response"

## Code Examples

### Basic MCP Server Setup
```python
# src/server.py
"""MCP server for Reddit moderation."""
from mcp.server.fastmcp import FastMCP
from mcp.server.models import InitializationOptions

# Create server instance
mcp = FastMCP(
    name="italia-career-mod",
    description="AI-assisted Reddit moderation for r/italycareer",
    version="0.1.0"
)

# Placeholder tool - actual tools added in Phase 3
@mcp.tool()
def status() -> str:
    """Get server status (placeholder for Phase 1)."""
    return "Server operational. Reddit tools coming in Phase 3."
```

### Main Entry Point
```python
# src/main.py
"""Entry point for MCP server."""
import os
from dotenv import load_dotenv
from src.server import mcp

def main():
    """Load configuration and start server."""
    load_dotenv()

    # Validate environment (for future use, not used in Phase 1)
    reddit_client_id = os.getenv("REDDIT_CLIENT_ID")
    if not reddit_client_id:
        print("Warning: Reddit credentials not configured. Set up .env for Phase 2.")

    # Run server with streamable HTTP transport
    # Binds to 0.0.0.0 for Docker access
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
```

### Environment Configuration
```python
# src/config.py
"""Configuration and environment variables."""
import os
from dotenv import load_dotenv

load_dotenv()

# Server configuration
SERVER_NAME = "italia-career-mod"
SERVER_VERSION = "0.1.0"
SERVER_DESCRIPTION = "AI-assisted Reddit moderation for r/italycareer"

# Server binding (for Docker compatibility)
SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("SERVER_PORT", "8000"))

# Reddit credentials (for Phase 2, validated but unused in Phase 1)
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USERNAME = os.getenv("REDDIT_USERNAME")
REDDIT_PASSWORD = os.getenv("REDDIT_PASSWORD")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", f"python:italia-career-mod:{SERVER_VERSION}")

def validate_reddit_credentials() -> list[str]:
    """Return list of missing credential variable names."""
    required = [
        "REDDIT_CLIENT_ID",
        "REDDIT_CLIENT_SECRET",
        "REDDIT_USERNAME",
        "REDDIT_PASSWORD"
    ]
    return [var for var in required if not os.getenv(var)]
```

### Example .env.example
```bash
# .env.example
# Copy this file to .env and fill in your Reddit credentials

# Reddit API credentials (https://www.reddit.com/prefs/apps)
# Create a "script" application type
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_client_secret_here
REDDIT_USERNAME=your_reddit_username
REDDIT_PASSWORD=your_reddit_password
REDDIT_USER_AGENT=python:italia-career-mod:0.1.0 (by /u/your_username)

# Server configuration
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
```

### Example Dockerfile
```dockerfile
# Dockerfile
FROM python:3.12-slim AS builder

# Install uv package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml ./
COPY uv.lock* ./

# Install dependencies
RUN uv pip install --system -e .

# Runtime stage
FROM python:3.12-slim

WORKDIR /app

# Copy installed packages
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY src/ /app/src/
COPY .env.example /app/.env.example

# Expose MCP endpoint
EXPOSE 8000

# Run server
CMD ["python", "-m", "src.main"]
```

### Example docker-compose.yml
```yaml
# docker-compose.yml
services:
  mcp-server:
    build: .
    container_name: italia-career-mod
    ports:
      - "8000:8000"
    environment:
      - SERVER_HOST=0.0.0.0
      - SERVER_PORT=8000
    env_file:
      - .env
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/mcp"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Example pyproject.toml
```toml
# pyproject.toml
[project]
name = "italia-career-mod"
version = "0.1.0"
description = "AI-assisted Reddit moderation MCP server"
requires-python = ">=3.10"
dependencies = [
    "mcp[cli]>=1.26.0",
    "python-dotenv>=1.0.0",
]

[project.scripts]
italia-career-mod = "src.main:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.uv]
dev-dependencies = [
    "pytest>=8.3.0",
    "pytest-cov>=5.0.0",
    "ruff>=0.8.0",
]

[tool.ruff]
line-length = 100
target-version = "py310"

[tool.ruff.lint]
select = ["E", "F", "I"]
ignore = []

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| stdio transport | Streamable HTTP transport | 2025 (specification evolution) | HTTP required for Docker deployment |
| SSE transport | Streamable HTTP transport | 2025 | Streamable HTTP supersedes SSE for production |
| pip for dependencies | uv package manager | 2024-2025 | 10-100x faster dependency resolution |
| Manual protocol implementation | FastMCP SDK | 2024-2025 | Declarative tool registration, type-safe |

**Deprecated/outdated:**
- **stdio transport:** Not suitable for Docker, use streamable-http
- **SSE transport:** Being superseded by streamable-http
- **Manual JSON-RPC handling:** Use SDK classes instead
- **Pip-only workflows:** uv is recommended for new projects

## Open Questions

1. **Stateful vs Stateless HTTP mode**
   - What we know: FastMCP supports both modes via `stateless_http` parameter
   - What's unclear: Whether stateless is needed for homelab deployment (likely yes for simplicity)
   - Recommendation: Start with stateful (default), can switch to stateless in Phase 4 if scaling needed

2. **Event Store for Resumability**
   - What we know: StreamableHTTPServerTransport accepts optional EventStore for resumability
   - What's unclear: Whether InMemoryEventStore is sufficient for homelab use
   - Recommendation: Skip in Phase 1, add in Phase 4 if multi-node deployment needed

3. **Health Check Endpoint**
   - What we know: MCP doesn't specify health check, but docker-compose healthcheck needs one
   - What's unclear: Best practice for MCP health checks (GET /mcp may not be sufficient)
   - Recommendation: Use GET /mcp for basic connectivity in Phase 1, refine in Phase 4

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.3.4+ (with anyio plugin) |
| Config file | None (inline in pyproject.toml) |
| Quick run command | `pytest tests/test_server.py -x` |
| Full suite command | `pytest tests/ -v --cov=src` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| MCPF-01 | Server uses streamable-http transport | integration | `pytest tests/test_server.py::test_transport_type -x` | ❌ Wave 0 |
| MCPF-02 | Server exposes /mcp on 0.0.0.0:8000 | integration | `pytest tests/test_server.py::test_endpoint_accessible -x` | ❌ Wave 0 |
| MCPF-03 | Tool discovery protocol implemented | unit | `pytest tests/test_server.py::test_list_tools -x` | ❌ Wave 0 |
| MCPF-04 | Server provides correct metadata | unit | `pytest tests/test_server.py::test_server_metadata -x` | ❌ Wave 0 |
| MCPF-05 | Structured error responses | unit | `pytest tests/test_server.py::test_error_responses -x` | ❌ Wave 0 |
| DEPL-01 | Dockerfile uses python:3.12-slim | manual | `grep "FROM python:3.12-slim" Dockerfile` | N/A |
| DEPL-02 | Dockerfile includes uv | manual | `grep "uv" Dockerfile` | N/A |
| DEPL-03 | docker-compose.yml exists | manual | `test -f docker-compose.yml` | N/A |
| DEPL-04 | .env.example includes all 5 Reddit vars | manual | `grep -E "REDDIT_(CLIENT_ID|CLIENT_SECRET|USERNAME|PASSWORD|USER_AGENT)" .env.example | wc -l` | N/A |

### Sampling Rate
- **Per task commit:** `pytest tests/test_server.py -x`
- **Per wave merge:** `pytest tests/ -v --cov=src`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_server.py` — covers MCPF-01, MCPF-02, MCPF-03, MCPF-04, MCPF-05
- [ ] `tests/conftest.py` — shared fixtures (test server, async client)
- [ ] `pyproject.toml` — add pytest, pytest-cov, pytest-asyncio to dev dependencies
- [ ] `pyproject.toml` — add pytest configuration (anyio plugin, paths)

## Sources

### Primary (HIGH confidence)
- [MCP Python SDK - GitHub](https://github.com/modelcontextprotocol/python-sdk) - Full repository including examples
- [MCP Python SDK v1.26.0 - PyPI](https://pypi.org/pypi/mcp/json) - Package metadata, version, dependencies
- [MCP Specification - GitHub](https://github.com/modelcontextprotocol/specification) - Protocol schema, JSON-RPC format
- [streamable_http.py - MCP SDK source](https://raw.githubusercontent.com/modelcontextprotocol/python-sdk/main/src/mcp/server/streamable_http.py) - Transport implementation
- [types.py - MCP SDK source](https://raw.githubusercontent.com/modelcontextprotocol/python-sdk/main/src/mcp/types.py) - Error codes, response types

### Secondary (MEDIUM confidence)
- [uv Documentation](https://docs.astral.sh/uv/) - Package manager usage
- [README.md - MCP Python SDK](https://raw.githubusercontent.com/modelcontextprotocol/python-sdk/v1.12.0/README.md) - Installation, quickstart examples
- [pyproject.toml - MCP Python SDK](https://raw.githubusercontent.com/modelcontextprotocol/python-sdk/main/pyproject.toml) - Dev dependencies, linting config

### Tertiary (LOW confidence)
- Web search results (limited by rate limits during research) - General ecosystem patterns

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Verified from PyPI and official repository
- Architecture: HIGH - Based on official SDK examples and source code
- Pitfalls: MEDIUM - Based on common Docker/Python patterns, some inferred

**Research date:** 2026-03-11
**Valid until:** 2026-04-11 (30 days - MCP ecosystem is evolving rapidly)

**Key verification notes:**
- MCP Python SDK version 1.26.0 confirmed via PyPI API
- Streamable HTTP transport confirmed as production-ready (supersedes SSE)
- uvicorn >=0.31.1 and starlette >=0.27 confirmed as core dependencies
- FastMCP decorator pattern confirmed from official examples
- JSON-RPC error format confirmed from specification schema
