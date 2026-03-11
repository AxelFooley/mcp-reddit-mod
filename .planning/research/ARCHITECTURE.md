# Architecture Research

**Domain:** MCP Server with HTTP Transport
**Researched:** 2025-03-11
**Confidence:** HIGH

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client Layer                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Claude Code  │  │ Claude Desktop│  │   MCP Inspector│        │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
│         │                 │                 │                   │
├─────────┼─────────────────┼─────────────────┼───────────────────┤
│         │     HTTP/JSON-RPC over TCP        │                   │
│         ▼                 ▼                 ▼                   │
│  ┌─────────────────────────────────────────────────────┐       │
│  │              FastMCP Server (Python)                 │       │
│  ├─────────────────────────────────────────────────────┤       │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │       │
│  │  │   Tools     │  │  Resources  │  │   Prompts   │  │       │
│  │  │ Registry    │  │  Registry   │  │  Registry   │  │       │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  │       │
│  │         │                │                │          │       │
│  │  ┌──────┴────────────────┴────────────────┴──────┐  │       │
│  │  │         Transport Layer (Streamable HTTP)      │  │       │
│  │  │  - Stateful/Stateless modes                    │  │       │
│  │  │  - Session management                          │  │       │
│  │  │  - JSON-RPC 2.0 message handling               │  │       │
│  │  └──────────────────────┬─────────────────────────┘  │       │
│  └─────────────────────────┼───────────────────────────┘       │
├─────────────────────────────┼───────────────────────────────────┤
│                             ▼                                   │
│  ┌─────────────────────────────────────────────────────┐       │
│  │              Reddit API Integration                 │       │
│  ├─────────────────────────────────────────────────────┤       │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │       │
│  │  │ PRAW Client │  │ Mod Queue   │  │   User      │  │       │
│  │  │ (Singleton) │  │ Operations  │  │  History    │  │       │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  │       │
│  └─────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| **FastMCP Server** | Main server instance, lifecycle management, protocol compliance | `FastMCP(name, lifespan, stateless_http, json_response)` |
| **Tools Registry** | Decorator-based tool registration, schema generation, validation | `@mcp.tool()` decorator with type hints |
| **Resources Registry** | Data source registration, URI templating | `@mcp.resource()` decorator |
| **Prompts Registry** | Prompt template management | `@mcp.prompt()` decorator |
| **Transport Layer** | HTTP/JSON-RPC message handling, session management | Built-in Streamable HTTP transport |
| **Session Manager** | Connection lifecycle, initialization, shutdown | `mcp.session_manager.run()` context manager |
| **Context Injection** | Request metadata, logging, progress reporting, lifespan resources | `Context[ServerSession, AppContext]` type hint |
| **PRAW Client** | Reddit API communication, rate limiting, authentication | `praw.Reddit()` singleton instance |

## Recommended Project Structure

```
src/
├── server.py              # FastMCP server initialization and entry point
├── config.py              # Configuration management (environment variables)
├── lifespan.py            # Application lifespan (startup/shutdown)
├── reddit/
│   ├── __init__.py
│   ├── client.py          # PRAW client singleton wrapper
│   ├── tools.py           # Reddit moderation tools (approve, remove, ban)
│   ├── modqueue.py        # Mod queue fetching and filtering
│   └── history.py         # User history for repeat offender detection
├── schemas/
│   ├── __init__.py
│   ├── modqueue.py        # Pydantic models for mod queue items
│   ├── actions.py         # Request/response schemas for actions
│   └── history.py         # Schemas for user history responses
└── utils/
    ├── __init__.py
    ├── logging.py         # MCP-aware logging utilities
    └── errors.py          # Custom error handling and propagation
tests/
├── test_tools.py          # Tool logic tests (with PRAW mocking)
├── test_modqueue.py       # Mod queue processing tests
├── test_history.py        # User history tests
└── conftest.py            # Pytest fixtures including Reddit mock
Dockerfile                 # Container image definition
docker-compose.yml         # Service orchestration
.env.example               # Required environment variables template
```

### Structure Rationale

- **`server.py`**: Single entry point for MCP server initialization, simplifies deployment
- **`config.py`**: Centralized configuration management, all env vars in one place
- **`lifespan.py`**: Separates startup/shutdown logic from server definition
- **`reddit/` module**: Encapsulates all Reddit-specific logic, clear boundary with MCP layer
- **`schemas/` module**: Pydantic models for structured output, type safety, and auto-validation
- **`utils/` module**: Shared utilities that don't fit in other modules
- **`tests/`**: Comprehensive test coverage with mocked PRAW for fast, reliable testing

## Architectural Patterns

### Pattern 1: FastMCP Decorator-Based Tool Registration

**What:** FastMCP provides decorators that automatically register functions as MCP tools, generate JSON schemas from type hints, and handle request/response lifecycle.

**When to use:** All tool registration in FastMCP servers. This is the primary pattern for exposing functionality.

**Trade-offs:**
- **Pros:** Minimal boilerplate, automatic schema generation, type-safe, idiomatic Python
- **Cons:** Magic behavior can be opaque for debugging, decorator complexity for advanced use cases

**Example:**
```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Reddit Moderation Server", stateless_http=True, json_response=True)

@mcp.tool()
async def approve_item(thing_id: str) -> dict[str, str]:
    """Approve a Reddit post or comment."""
    # Implementation here
    return {"status": "approved", "thing_id": thing_id}
```

### Pattern 2: Lifespan Context Management

**What:** FastMCP supports lifespan context managers that initialize resources on startup and clean up on shutdown, with type-safe access in tool functions through the `Context` parameter.

**When to use:** Managing shared resources like database connections, API clients, or configuration objects that need proper initialization and cleanup.

**Trade-offs:**
- **Pros:** Type-safe resource sharing, automatic cleanup, clear lifecycle management
- **Cons:** Adds complexity for simple servers, requires understanding of async context managers

**Example:**
```python
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from mcp.server.fastmcp import Context, FastMCP
from mcp.server.session import ServerSession
import praw

@dataclass
class AppContext:
    reddit: praw.Reddit

@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    # Initialize on startup
    reddit = praw.Reddit(
        client_id=os.getenv("REDDIT_CLIENT_ID"),
        client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
        user_agent=os.getenv("REDDIT_USER_AGENT"),
        username=os.getenv("REDDIT_USERNAME"),
        password=os.getenv("REDDIT_PASSWORD"),
    )
    try:
        yield AppContext(reddit=reddit)
    finally:
        # Cleanup on shutdown (PRAW uses context manager)
        await reddit.close()

mcp = FastMCP("Reddit Mod Server", lifespan=app_lifespan, stateless_http=True, json_response=True)

@mcp.tool()
async def get_modqueue(subreddit: str, ctx: Context[ServerSession, AppContext]) -> list[dict]:
    """Get mod queue items for a subreddit."""
    reddit = ctx.request_context.lifespan_context.reddit
    subreddit = reddit.subreddit(subreddit)
    modqueue = subreddit.mod.modqueue()
    return [{"id": item.id, "title": item.title} for item in modqueue]
```

### Pattern 3: Structured Output with Pydantic Models

**What:** FastMCP automatically validates tool outputs against JSON schemas generated from type hints, supporting Pydantic models, TypedDicts, dataclasses, and typed dicts.

**When to use:** All tool returns to provide type safety, automatic validation, and clear contracts for clients.

**Trade-offs:**
- **Pros:** Type-safe, auto-validated responses, clear API contracts, better IDE support
- **Cons:** Requires defining data models, adds boilerplate for simple returns

**Example:**
```python
from pydantic import BaseModel, Field

class ModQueueItem(BaseModel):
    """A mod queue item."""
    id: str = Field(description="Reddit thing ID")
    title: str = Field(description="Post title")
    author: str = Field(description="Username of author")
    subreddit: str = Field(description="Subreddit name")
    created_utc: float = Field(description="Unix timestamp")
    permalink: str = Field(description="Link to the content")

@mcp.tool()
async def get_modqueue(subreddit: str, limit: int = 25) -> list[ModQueueItem]:
    """Get mod queue items for a subreddit."""
    # Implementation returns validated ModQueueItem list
```

### Pattern 4: Streamable HTTP Transport

**What:** FastMCP's Streamable HTTP transport supports both stateful (session-based) and stateless (request-scoped) modes, with JSON or SSE response formats.

**When to use:** Production deployments where multiple clients need access, or when scaling across multiple nodes.

**Trade-offs:**
- **Pros:** Better scalability, resumability with event stores, multi-node support
- **Cons:** More complex than stdio transport, requires HTTP infrastructure

**Example:**
```python
# Recommended configuration for production
mcp = FastMCP(
    "Production Server",
    stateless_http=True,  # Stateless for scalability
    json_response=True,   # JSON responses (not SSE)
)

# Run with streamable HTTP transport
if __name__ == "__main__":
    mcp.run(transport="streamable-http")
```

## Data Flow

### Request Flow

```
[AI Client]
    ↓ HTTP POST /mcp with JSON-RPC request
[FastMCP Transport Layer]
    ↓ Parse JSON-RPC, route to handler
[Tool Function with Context Injection]
    ↓ Access lifespan resources (PRAW client)
[Reddit API via PRAW]
    ↓ Rate-limited API calls
[Response Serialization]
    ↓ Structured output validation
[HTTP Response with JSON-RPC result]
[AI Client receives structured data]
```

### State Management

```
[Lifespan Context (App-wide)]
    ↓ (Created at startup, shared across requests)
[PRAW Reddit Client (Singleton)]
    ↓ (Accessed via ctx.request_context.lifespan_context)
[Request Context (Per-request)]
    ↓ (Includes request_id, client_id, meta)
[Session State (if stateful mode)]
    ↓ (Managed by FastMCP session manager)
[Response]
```

### Key Data Flows

1. **Mod Queue Retrieval:** Client → `get_modqueue(subreddit)` → PRAW → Reddit API → Structured `ModQueueItem[]` → Client
2. **Item Approval:** Client → `approve_item(thing_id)` → PRAW → Reddit API → Success/error response → Client
3. **User History:** Client → `get_user_history(username, subreddit)` → PRAW → Reddit API (search in subreddit) → Filtered flagged items → Client

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 1-10 concurrent users | Single container with stateless HTTP, PRAW's built-in rate limiting handles Reddit API constraints |
| 10-100 concurrent users | Multiple containers behind load balancer, consider connection pooling for PRAW |
| 100+ concurrent users | Implement request queuing, caching for mod queue data, consider Reddit API rate limit sharing across instances |

### Scaling Priorities

1. **First bottleneck:** Reddit API rate limits (60 requests/minute for OAuth). PRAW handles this, but concurrent requests will queue. Implement caching for frequently accessed data like mod queue.
2. **Second bottleneck:** Memory usage for large mod queues. Stream results using generators rather than loading all items into memory.
3. **Third bottleneck:** Network latency to Reddit API. Use async operations to avoid blocking during API calls.

## Anti-Patterns

### Anti-Pattern 1: Creating New PRAW Clients Per Request

**What people do:** Creating a new `praw.Reddit()` instance inside each tool function.

**Why it's wrong:** Wasteful resource consumption, slower requests (authentication overhead), misses PRAW's internal rate limiting benefits.

**Do this instead:** Create a single PRAW client instance during lifespan and access it via the lifespan context.

```python
# BAD
@mcp.tool()
async def get_modqueue(subreddit: str) -> list:
    reddit = praw.Reddit(...)  # New client every request!
    return reddit.subreddit(subreddit).mod.modqueue()

# GOOD
@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    reddit = praw.Reddit(...)  # Single instance
    try:
        yield AppContext(reddit=reddit)
    finally:
        await reddit.close()

@mcp.tool()
async def get_modqueue(subreddit: str, ctx: Context) -> list:
    reddit = ctx.request_context.lifespan_context.reddit  # Reuse instance
    return reddit.subreddit(subreddit).mod.modqueue()
```

### Anti-Pattern 2: Ignoring Structured Output

**What people do:** Returning plain dictionaries or unstructured data from tools.

**Why it's wrong:** Loses type safety, no automatic validation, unclear API contracts for clients.

**Do this instead:** Define Pydantic models with proper field descriptions and return them from tools.

```python
# BAD
@mcp.tool()
async def get_modqueue(subreddit: str):
    items = reddit.subreddit(subreddit).mod.modqueue()
    return [{"id": i.id, "title": i.title} for i in items]  # Unstructured

# GOOD
class ModQueueItem(BaseModel):
    id: str = Field(description="Reddit thing ID")
    title: str = Field(description="Post title")

@mcp.tool()
async def get_modqueue(subreddit: str) -> list[ModQueueItem]:
    items = reddit.subreddit(subreddit).mod.modqueue()
    return [ModQueueItem(id=i.id, title=i.title) for i in items]
```

### Anti-Pattern 3: Synchronous API Calls in Async Tools

**What people do:** Using synchronous PRAW calls without awaiting in async tool functions.

**Why it's wrong:** Blocks the event loop, poor performance under load, doesn't leverage FastMCP's async capabilities.

**Do this instead:** Use `asyncio.to_thread()` to run blocking PRAW calls in a thread pool.

```python
# BAD
@mcp.tool()
async def get_modqueue(subreddit: str) -> list:
    return reddit.subreddit(subreddit).mod.modqueue()  # Blocks!

# GOOD
import asyncio

@mcp.tool()
async def get_modqueue(subreddit: str, ctx: Context) -> list:
    reddit = ctx.request_context.lifespan_context.reddit
    return await asyncio.to_thread(
        lambda: list(reddit.subreddit(subreddit).mod.modqueue(limit=25))
    )
```

### Anti-Pattern 4: Hardcoding Credentials

**What people do:** Putting Reddit API credentials directly in source code.

**Why it's wrong:** Security risk, credentials can't be changed without code deployment, prevents multi-environment configs.

**Do this instead:** Use environment variables with proper defaults and validation.

```python
# BAD
reddit = praw.Reddit(
    client_id="abc123",
    client_secret="xyz789",
    ...
)

# GOOD
import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    reddit_client_id: str
    reddit_client_secret: str
    reddit_user_agent: str
    reddit_username: str
    reddit_password: str

    class Config:
        env_file = ".env"

settings = Settings()
reddit = praw.Reddit(
    client_id=settings.reddit_client_id,
    client_secret=settings.reddit_client_secret,
    user_agent=settings.reddit_user_agent,
    username=settings.reddit_username,
    password=settings.reddit_password,
)
```

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| **Reddit API** | PRAW library (Python wrapper) | Handles rate limiting, authentication, data models. Use singleton pattern. |
| **AI Clients** | MCP over Streamable HTTP | JSON-RPC 2.0 protocol. Stateless mode recommended. |
| **Docker** | Container deployment with docker-compose | Expose port 8000, volume mount for config if needed. |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| **FastMCP Server ↔ Reddit Module** | Direct function calls, lifespan context injection | Clean separation: MCP layer handles protocol, Reddit module handles API logic |
| **Tools ↔ Schemas** | Type annotations, Pydantic validation | Schemas define contracts, tools implement logic |
| **Server ↔ Config** | Environment variables via Settings class | Centralized config, validation on startup |

## Build Order Implications

### Component Dependencies

```
1. Config/Settings (foundation)
   ↓
2. Schemas (define contracts)
   ↓
3. Reddit/PRAW Module (implements API logic)
   ↓
4. Lifespan (initializes Reddit client)
   ↓
5. Tools (use schemas + Reddit client)
   ↓
6. FastMCP Server (registers tools, manages lifecycle)
   ↓
7. Entry Point (runs server with HTTP transport)
```

### Recommended Build Phases

**Phase 1: Foundation (Config + Schemas)**
- Define all environment variables in `config.py`
- Create Pydantic models for all tool inputs/outputs
- Set up basic project structure

**Phase 2: Reddit Integration**
- Implement PRAW client wrapper
- Create Reddit API functions (mod queue, approve, remove, ban, user history)
- Write unit tests with mocked PRAW

**Phase 3: MCP Server Assembly**
- Create FastMCP server instance with lifespan
- Register tools with proper decorators
- Implement Context injection for accessing Reddit client
- Add error handling and logging

**Phase 4: Deployment**
- Create Dockerfile and docker-compose.yml
- Set up environment variable templates
- Test with MCP Inspector
- Document installation and usage

## Sources

- [MCP Python SDK - Official Documentation](https://github.com/modelcontextprotocol/python-sdk) - HIGH confidence
- [FastMCP - Official GitHub Repository](https://github.com/jlowin/fastmcp) - HIGH confidence
- [MCP Specification - Official](https://spec.modelcontextprotocol.io/specification/) - HIGH confidence
- [FastMCP Documentation](https://gofastmcp.com/) - MEDIUM confidence (not fully accessible due to rate limits)

---
*Architecture research for: MCP Server with HTTP Transport*
*Researched: 2025-03-11*
