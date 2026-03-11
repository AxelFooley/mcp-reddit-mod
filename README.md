# ItaliaCareerMod - AI-Assisted Reddit Moderation MCP Server

An intelligent MCP (Model Context Protocol) server that provides AI-assisted Reddit moderation tools with human-in-the-loop oversight. Automatically review mod queue items, detect repeat offenders, and assist moderators while keeping destructive actions under human control.

## Features

- **Mod Queue Management**: Fetch and analyze mod queue items programmatically
- **Moderation Tools**: Approve, remove, and ban actions with AI assistance
- **User History Lookup**: Investigate user posting patterns and history
- **Repeat Offender Detection**: Identify users with repeated rule violations
- **Human-in-the-Loop**: AI suggests actions, humans make the final decisions
- **MCP Protocol Compatible**: Works with any MCP-compliant AI client

## Prerequisites

- **Docker**: 20.10 or later
- **Docker Compose**: 2.0 or later
- **Reddit API Credentials**: Client ID and secret from [Reddit App Preferences](https://www.reddit.com/prefs/apps)

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/AxelFooley/italia-career-mod.git
cd italia-career-mod
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and fill in your Reddit API credentials:

```env
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_client_secret_here
REDDIT_USER_AGENT=your_app_name/1.0 by your_reddit_username
REDDIT_USERNAME=your_reddit_username
REDDIT_PASSWORD=your_reddit_password
```

### 3. Start the Server

```bash
docker compose up --build
```

The server will be accessible at `http://localhost:8000/mcp`

### 4. Verify Connection

Connect any MCP-compatible client to `http://localhost:8000/mcp` to access moderation tools.

## Configuration

| Environment Variable | Description | Required |
|---------------------|-------------|----------|
| `REDDIT_CLIENT_ID` | Reddit app client ID from app preferences | Yes |
| `REDDIT_CLIENT_SECRET` | Reddit app client secret | Yes |
| `REDDIT_USER_AGENT` | Unique identifier for your app (format: `app_name/version by username`) | Yes |
| `REDDIT_USERNAME` | Reddit username for moderation actions | Yes |
| `REDDIT_PASSWORD` | Reddit password (or app-specific password if 2FA enabled) | Yes |
| `MCP_SERVER_HOST` | Host address to bind to (default: `0.0.0.0`) | No |
| `MCP_SERVER_PORT` | Port to listen on (default: `8000`) | No |

### Getting Reddit API Credentials

1. Go to [Reddit App Preferences](https://www.reddit.com/prefs/apps)
2. Click "create another app..."
3. Select "script" as the application type
4. Fill in name and description
5. Set `http://localhost:8000` as redirect URI (not used but required)
6. Copy the client ID and secret (the string next to "secret")

## Development

### Setup Local Development Environment

```bash
# Install uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Run the server locally
python -m src.main
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_server.py -v
```

### Code Quality

```bash
# Check code style
ruff check .

# Auto-fix issues
ruff check . --fix

# Format code
ruff format .
```

## Project Structure

```
italia-career-mod/
├── src/
│   ├── __init__.py
│   ├── config.py        # Configuration and environment loading
│   ├── server.py        # FastMCP server with Reddit tools
│   └── main.py          # Server entry point
├── tests/
│   ├── __init__.py
│   └── test_server.py   # Server and tools tests
├── Dockerfile           # Container image definition
├── docker-compose.yml   # Multi-container orchestration
├── .dockerignore        # Docker build exclusions
├── .env.example         # Environment variable template
├── pyproject.toml       # Python project configuration
└── README.md            # This file
```

## MCP Protocol

This server implements the [Model Context Protocol (MCP)](https://modelcontextprotocol.io), a standardized protocol for AI assistants to interact with external tools and data sources.

### Available Tools

- **get_mod_queue**: Fetch items from the moderation queue
- **approve_post**: Approve a post/comment
- **remove_post**: Remove a post/comment
- **ban_user**: Ban a user from the subreddit
- **get_user_history**: Retrieve user's posting history

### Connecting Clients

Configure your MCP client to connect to:

```
URL: http://localhost:8000/mcp
Transport: Streamable HTTP (JSON-RPC)
```

## Safety & Philosophy

This project follows a **human-in-the-loop** philosophy:

- AI assistants can **read** mod queue items and user history
- AI assistants can **suggest** moderation actions
- Humans **must approve** destructive actions (removals, bans)

This ensures AI acts as an intelligent assistant rather than an autonomous moderator, preserving human control over community management decisions.

## Deployment

### Docker Deployment (Recommended)

```bash
docker compose up -d
```

### Building the Image

```bash
docker build -t italia-career-mod:latest .
```

### Running with Custom Configuration

```bash
docker run -d \
  -p 8000:8000 \
  --env-file .env \
  italia-career-mod:latest
```

## License

MIT License - see LICENSE file for details

## Acknowledgments

Built with:
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) - Model Context Protocol implementation
- [FastMCP](https://github.com/jlowin/fastmcp) - Fast MCP server framework
- [PRAW](https://praw.readthedocs.io/) - Python Reddit API Wrapper
- [Docker](https://www.docker.com/) - Container platform

## Support

For issues, questions, or contributions, please visit the [GitHub repository](https://github.com/AxelFooley/italia-career-mod).

---

**Note**: This tool is intended to assist moderators, not replace them. Always review AI suggestions before taking moderation actions.
