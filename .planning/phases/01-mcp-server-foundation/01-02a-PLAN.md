---
phase: 01-mcp-server-foundation
plan: 02a
type: execute
wave: 1
depends_on: []
files_modified:
  - Dockerfile
  - .dockerignore
autonomous: true
requirements:
  - DEPL-01
  - DEPL-02
must_haves:
  truths:
    - "Dockerfile uses python:3.12-slim base image"
    - "Dockerfile installs uv for dependency management"
    - "Docker image builds successfully"
    - ".dockerignore excludes .env and build artifacts"
  artifacts:
    - path: "Dockerfile"
      provides: "Multi-stage Docker build with uv"
      min_lines: 25
      contains: "FROM python:3.12-slim"
    - path: ".dockerignore"
      provides: "Build context optimization"
      min_lines: 15
      contains: ".env"
  key_links:
    - from: "Dockerfile"
      to: "pyproject.toml"
      via: "COPY pyproject.toml for uv pip install"
      pattern: "COPY.*pyproject.toml"
    - from: "Dockerfile"
      to: "src/"
      via: "COPY application code to /app/src/"
      pattern: "COPY src/"
---

<objective>
Create multi-stage Dockerfile with uv package manager for fast builds and .dockerignore for build optimization.

Purpose: Enable containerized deployment of MCP server with fast dependency resolution using uv. Optimize build context by excluding unnecessary files and credentials.
Output: Dockerfile that builds successfully with python:3.12-slim and uv
</objective>

<execution_context>
@/Users/alessandro.anghelone/.claude/get-shit-done/workflows/execute-plan.md
@/Users/alessandro.anghelone/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/REQUIREMENTS.md
@.planning/phases/01-mcp-server-foundation/01-RESEARCH.md
@.planning/phases/01-mcp-server-foundation/01-VALIDATION.md

# Docker Patterns from RESEARCH.md

## Multi-Stage Dockerfile with uv
```dockerfile
FROM python:3.12-slim AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

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

EXPOSE 8000

CMD ["python", "-m", "src.main"]
```
</context>

<tasks>

<task type="auto">
  <name>Task 1: Create multi-stage Dockerfile with uv</name>
  <files>Dockerfile</files>
  <action>
    Create Dockerfile in project root:

    Use multi-stage build pattern from RESEARCH.md:

    Builder stage:
    1. FROM python:3.12-slim AS builder (DEPL-01)
    2. Install uv: COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv (DEPL-02)
    3. WORKDIR /app
    4. COPY pyproject.toml ./ (if uv.lock exists, COPY uv.lock* ./)
    5. RUN uv pip install --system -e .

    Runtime stage:
    1. FROM python:3.12-slim
    2. WORKDIR /app
    3. COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
    4. COPY --from=builder /usr/local/bin /usr/local/bin
    5. COPY src/ /app/src/
    6. COPY .env.example /app/.env.example (for reference in container)
    7. EXPOSE 8000
    8. CMD ["python", "-m", "src.main"]

    DO NOT include .env file in COPY - credentials should be mounted via docker-compose env_file.

    Multi-stage build keeps final image small by excluding uv binary and build artifacts.
  </action>
  <verify>
    <automated>grep -E "FROM python:3.12-slim|COPY.*uv|uv pip install" Dockerfile | wc -l | grep -q "3"</automated>
  </verify>
  <done>Dockerfile created with python:3.12-slim and uv package manager</done>
</task>

<task type="auto">
  <name>Task 2: Create .dockerignore for build optimization</name>
  <files>.dockerignore</files>
  <action>
    Create .dockerignore to exclude unnecessary files from Docker build context:

    Include:
    - .git/
    - .gitignore
    - __pycache__/
    - *.pyc
    - .env (never commit credentials)
    - .pytest_cache/
    - .coverage
    - .planning/ (not needed in container)
    - tests/ (not needed in production container)
    - README.md (optional)
    - *.md (optional docs)
    - .vscode/ (editor config)
    - .idea/ (editor config)

    This speeds up builds by reducing context size and prevents accidentally including credentials.
  </action>
  <verify>
    <automated>test -f .dockerignore && grep -q ".env" .dockerignore && grep -q "__pycache__" .dockerignore</automated>
  </verify>
  <done>.dockerignore created, excludes .env and build artifacts</done>
</task>

</tasks>

<verification>
Docker build infrastructure created: Dockerfile uses correct base image and uv, .dockerignore excludes unnecessary files.
</verification>

<success_criteria>
- [ ] Dockerfile uses python:3.12-slim base image (DEPL-01)
- [ ] Dockerfile installs and uses uv for dependency installation (DEPL-02)
- [ ] .dockerignore excludes .env and build artifacts
- [ ] Multi-stage build pattern keeps final image small
</success_criteria>

<output>
After completion, create `.planning/phases/01-mcp-server-foundation/01-02a-SUMMARY.md`
</output>
