---
phase: 01-mcp-server-foundation
plan: 02b
type: execute
wave: 2
depends_on: ["01-02a"]
files_modified:
  - docker-compose.yml
  - .env.example
autonomous: true
requirements:
  - DEPL-03
  - DEPL-04
must_haves:
  truths:
    - "docker-compose.yml defines MCP server service"
    - "Container starts and exposes port 8000"
    - ".env.example documents all 5 Reddit credential variables"
    - "Docker build and compose config validate successfully"
  artifacts:
    - path: "docker-compose.yml"
      provides: "Service definition for homelab deployment"
      min_lines: 15
      contains: "services:"
    - path: ".env.example"
      provides: "Reddit credential template"
      min_lines: 10
      contains: "REDDIT_CLIENT_ID"
  key_links:
    - from: "docker-compose.yml"
      to: ".env"
      via: "env_file directive loads environment"
      pattern: "env_file:"
    - from: "docker-compose.yml"
      to: "Dockerfile"
      via: "build: . uses Dockerfile in current directory"
      pattern: "build:"
---

<objective>
Create docker-compose.yml for homelab deployment and .env.example template for Reddit credentials. Verify Docker infrastructure is ready.

Purpose: Provide reproducible deployment configuration for homelab use with proper environment variable documentation. Ensure Docker build and compose configurations are valid before Wave 2 testing.
Output: Valid docker-compose.yml and complete .env.example template
</objective>

<execution_context>
@/Users/alessandro.anghelone/.claude/get-shit-done/workflows/execute-plan.md
@/Users/alessandro.anghelone/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/REQUIREMENTS.md
@.planning/phases/01-mcp-server-foundation/01-RESEARCH.md
@.planning/phases/01-mcp-server-foundation/01-VALIDATION.md

# Docker Compose for Homelab
```yaml
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
```

## Environment Variables Template
```bash
# Reddit API credentials
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_client_secret_here
REDDIT_USERNAME=your_reddit_username
REDDIT_PASSWORD=your_reddit_password
REDDIT_USER_AGENT=python:italia-career-mod:0.1.0
```
</context>

<tasks>

<task type="auto">
  <name>Task 1: Create docker-compose.yml for homelab deployment</name>
  <files>docker-compose.yml</files>
  <action>
    Create docker-compose.yml in project root:

    Service definition:
    - services: mcp-server:
      - build: . (uses Dockerfile in current directory)
      - container_name: italia-career-mod
      - ports: - "8000:8000" (expose MCP endpoint to host)
      - environment:
        - SERVER_HOST=0.0.0.0
        - SERVER_PORT=8000
      - env_file:
        - .env (load credentials from .env file in project root)
      - restart: unless-stopped
      - healthcheck:
        - test: ["CMD", "curl", "-f", "http://localhost:8000/mcp"]
        - interval: 30s
        - timeout: 10s
        - retries: 3

    Use pattern from RESEARCH.md. Healthcheck uses curl to verify /mcp endpoint is responding.

    DEPL-03 satisfied: docker-compose.yml provided for homelab deployment.
  </action>
  <verify>
    <automated>docker compose config >/dev/null 2>&1 && echo "docker-compose.yml is valid" || echo "docker-compose.yml has errors"</automated>
  </verify>
  <done>docker-compose.yml created with valid configuration</done>
</task>

<task type="auto">
  <name>Task 2: Create .env.example with Reddit credential template</name>
  <files>.env.example</files>
  <action>
    Create .env.example with all 5 required Reddit credential variables (DEPL-04):

    Include:
    1. REDDIT_CLIENT_ID - with description and example format
    2. REDDIT_CLIENT_SECRET - with description
    3. REDDIT_USERNAME - with description
    4. REDDIT_PASSWORD - with description
    5. REDDIT_USER_AGENT - with description and default format

    Include comments explaining:
    - How to get credentials (https://www.reddit.com/prefs/apps)
    - Create a "script" application type (not web app)
    - USER_AGENT format: python:italia-career-mod:0.1.0 (by /u/yourusername)

    Include SERVER_HOST and SERVER_PORT as optional overrides.

    DO NOT include actual values - only placeholder text like "your_client_id_here".

    Use format from RESEARCH.md. This satisfies DEPL-04 requirement.
  </action>
  <verify>
    <automated>grep -E "REDDIT_(CLIENT_ID|CLIENT_SECRET|USERNAME|PASSWORD|USER_AGENT)" .env.example | wc -l | grep -q "5"</automated>
  </verify>
  <done>.env.example created with all 5 Reddit credential variables documented</done>
</task>

<task type="auto">
  <name>Task 3: Verify Docker build and configuration</name>
  <files>Dockerfile, docker-compose.yml, .env.example</files>
  <action>
    Verify Docker infrastructure is ready:

    1. Test Dockerfile syntax: `docker build -t test-build . --progress=plain`
       - Should build without errors
       - Should use python:3.12-slim (verify in build output)
       - Should install uv (verify in build output)

    2. Test docker-compose syntax: `docker compose config`
       - Should output valid YAML configuration
       - Should show service with port mapping 8000:8000
       - Should show env_file reference

    3. Verify .env.example completeness:
       - Check all 5 Reddit vars present
       - Check comments explain how to obtain credentials

    4. Update tests if needed for deployment verification (manual test later in Wave 2)

    Note: Don't run `docker compose up` yet - that requires .env file with real credentials and is verified in Wave 2.
  </action>
  <verify>
    <automated>docker build -t test-build . >/dev/null 2>&1 && docker compose config >/dev/null 2>&1 && echo "Docker infrastructure verified" || echo "Docker build or compose config failed"</automated>
  </verify>
  <done>Docker infrastructure verified, build succeeds, compose config valid</done>
</task>

</tasks>

<verification>
Docker deployment infrastructure complete: docker-compose.yml valid, .env.example documents all credentials, build succeeds.
</verification>

<success_criteria>
- [ ] docker-compose.yml exists with valid configuration (DEPL-03)
- [ ] .env.example includes all 5 Reddit credential variables (DEPL-04)
- [ ] docker build completes successfully
- [ ] docker compose config validates without errors
</success_criteria>

<output>
After completion, create `.planning/phases/01-mcp-server-foundation/01-02b-SUMMARY.md`
</output>
