# Phase 4: Production Deployment - Research

**Researched:** 2026-03-12
**Domain:** CI/CD, Docker, GitHub Actions, Python testing
**Confidence:** MEDIUM

## Summary

Phase 4 requires implementing a production-ready CI/CD pipeline using GitHub Actions with mandatory linting, testing with coverage requirements, Docker image building, and publishing to GitHub Container Registry (ghcr.io). The project already has solid foundations with pytest 9.0.2, ruff 0.15.5, and pytest-cov 7.0.0 configured in pyproject.toml, but is missing mypy for static type checking and the GitHub Actions workflow implementation.

**Primary recommendation:** Implement a single GitHub Actions workflow with sequential jobs (lint → test → build → push) using official GitHub Actions and Docker build actions, with 90% minimum coverage threshold and GHCR publishing on main branch success.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| GitHub Actions | - | CI/CD orchestration | Native GitHub integration, free for public repos, extensive ecosystem |
| ruff | 0.15.5 | Fast Python linter | 10-100x faster than flake8, replaces multiple linters, already configured |
| pytest | 9.0.2 | Test framework | De facto Python standard, async support via pytest-anyio, already configured |
| pytest-cov | 7.0.0 | Coverage reporting | Standard pytest coverage plugin, supports --cov-fail-under threshold |
| Docker Buildx | - | Multi-platform Docker builds | Layer caching, multi-stage builds, GHCR integration |
| ghcr.io | - | Container registry | Native GitHub registry, uses GITHUB_TOKEN for auth |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| mypy | - | Static type checking | CATCH-01: Must add to dev-dependencies for CICD-01 compliance |
| actions/checkout | v4 | Checkout repository code | Required first step in all GitHub Actions jobs |
| docker/setup-buildx-action | v3 | Docker Buildx setup | Required for advanced Docker builds with caching |
| docker/login-action | v3 | Registry authentication | Authenticate to GHCR using GITHUB_TOKEN |
| docker/build-push-action | v5 | Build and push images | Main Docker build action with caching support |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| ruff | flake8 + black + isort | ruff is 10-100x faster, single tool replaces three |
| pytest-cov | coverage.py directly | pytest-cov integrates seamlessly with pytest CLI |
| ghcr.io | Docker Hub | ghcr.io uses native GitHub auth, no separate credentials needed |

**Installation:**
```bash
# mypy needs to be added to dev-dependencies
uv add --dev mypy
```

## Architecture Patterns

### Recommended Project Structure
```
.github/
└── workflows/
    └── ci.yml              # Main CI/CD workflow (NEW for Phase 4)
src/
├── __init__.py
├── main.py
├── config.py
├── server.py
├── reddit_client.py
└── modtools.py
tests/
├── conftest.py             # Existing fixtures (no changes needed)
├── test_server.py
├── test_reddit_client.py
└── test_moderation_tools.py
```

### Pattern 1: Sequential GitHub Actions Workflow
**What:** Single workflow file with dependent jobs that must pass in sequence
**When to use:** When each stage depends on the previous stage's success (lint → test → build)
**Example:**
```yaml
# Source: GitHub Actions documentation patterns
name: CI

on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: ruff check .

  test:
    needs: lint
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pytest --cov=src --cov-fail-under=90

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/build-push-action@v5
```

### Pattern 2: GHCR Authentication with GITHUB_TOKEN
**What:** Built-in GitHub token authentication for container registry
**When to use:** When pushing images to ghcr.io from GitHub Actions
**Example:**
```yaml
# Source: GitHub Container Registry documentation
- name: Login to GHCR
  uses: docker/login-action@v3
  with:
    registry: ghcr.io
    username: ${{ github.actor }}
    password: ${{ secrets.GITHUB_TOKEN }}
```

### Pattern 3: Docker Layer Caching
**What:** Use GitHub Actions cache to speed up Docker builds
**When to use:** For faster CI builds by reusing unchanged layers
**Example:**
```yaml
# Source: Docker build-push-action documentation
- name: Build and push
  uses: docker/build-push-action@v5
  with:
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

### Anti-Patterns to Avoid
- **Pushing on every branch:** Only push to GHCR on main branch success to save storage
- **No coverage threshold:** Without --cov-fail-under, coverage can regress unnoticed
- **Missing mypy:** CICD-01 requires "ruff, mypy, or equivalent" - currently missing mypy
- **Hardcoded credentials:** Never use personal access tokens when GITHUB_TOKEN works

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| CI orchestration | Custom Jenkins/Drone scripts | GitHub Actions | Native integration, free for public repos, no external service |
| Docker caching | Manual cache management | actions/cache or type=gha | Built-in GitHub cache integration, automatic cache management |
| Linting multiple tools | flake8 + black + isort separately | ruff | Single fast tool, consistent configuration, 10-100x faster |
| Test coverage | Custom coverage scripts | pytest-cov | Native pytest integration, supports --cov-fail-under |
| Registry auth | PAT management | GITHUB_TOKEN | Auto-generated, no secret rotation needed, scoped to repo |
| Multi-stage builds | Custom scripts | Docker Buildx | Official Docker support, layer caching, cross-platform builds |

**Key insight:** GitHub Actions + Docker official actions provide a complete CI/CD solution without any custom scripting. The GITHUB_TOKEN provides secure, scoped authentication without managing personal access tokens.

## Common Pitfalls

### Pitfall 1: Missing mypy Configuration
**What goes wrong:** CICD-01 requires "ruff, mypy, or equivalent" but mypy is not in dependencies
**Why it happens:** pyproject.toml only specifies ruff, not mypy
**How to avoid:** Add mypy to dev-dependencies and create .github/workflows/ci.yml with mypy step
**Warning signs:** Running `mypy` fails with "command not found"

### Pitfall 2: Coverage Not Enforced in CI
**What goes wrong:** Coverage can regress without CI failing
**Why it happens:** pytest-cov runs but --cov-fail-under not specified
**How to avoid:** Always use `--cov-fail-under=90` in CI pytest command
**Warning signs:** Coverage reports show declining percentages but tests pass

### Pitfall 3: GHCR Permissions Not Configured
**What goes wrong:** Docker push fails with "denied" error
**Why it happens:** Repository settings don't permit Actions to write packages
**How to avoid:** Enable Actions write permission in repo Settings → Actions → General → Workflow permissions
**Warning signs:** "no permission to write package" in GitHub Actions logs

### Pitfall 4: Pushing on All Branches
**What goes wrong:** GHCR fills with unnecessary images from feature branches
**Why it happens:** Conditional push logic missing in workflow
**How to avoid:** Use `if: github.ref == 'refs/heads/main'` on docker/push step
**Warning signs:** GHCR repository has many redundant image tags

### Pitfall 5: Missing Docker Layer Caching
**What goes wrong:** Every CI rebuild takes 5+ minutes
**Why it happens:** cache-from and cache-to not configured in docker/build-push-action
**How to avoid:** Always include `cache-from: type=gha` and `cache-to: type=gha,mode=max`
**Warning signs:** Docker build time consistently high even for small changes

## Code Examples

Verified patterns from official sources:

### GitHub Actions Complete Workflow
```yaml
# Source: GitHub Actions and Docker documentation patterns
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: 'pip'
      - name: Install ruff
        run: pip install ruff
      - name: Run ruff
        run: ruff check .

  typecheck:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: 'pip'
      - name: Install mypy
        run: pip install mypy
      - name: Run mypy
        run: mypy src/

  test:
    needs: [lint, typecheck]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: 'pip'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e .
      - name: Install test dependencies
        run: pip install pytest pytest-cov pytest-mock pytest-anyio
      - name: Run tests with coverage
        run: pytest --cov=src --cov-report=xml --cov-report=term --cov-fail-under=90

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      - name: Build Docker image
        uses: docker/build-push-action@v5
        with:
          context: .
          push: false
          tags: italia-career-mod:test
          cache-from: type=gha
          cache-to: type=gha,mode=max

  push:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      - name: Login to GHCR
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ghcr.io/axelfooley/italia-career-mod:latest
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

### Pytest with Coverage Threshold
```bash
# Source: pytest-cov documentation
pytest --cov=src --cov-report=term-missing --cov-report=xml --cov-fail-under=90
```

### Ruff Configuration Check
```bash
# Source: ruff documentation
ruff check .                    # Check for issues
ruff check --fix .              # Auto-fix issues
ruff format --check .           # Check formatting
ruff format .                   # Format code
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| separate lint/test workflows | Single workflow with job dependencies | ~2022 | Faster feedback, clearer dependencies |
| flake8 + black + isort | ruff (all-in-one) | 2023-2024 | 10-100x faster linting |
| Docker Hub for GitHub projects | ghcr.io | 2021-2022 | Native GitHub auth, no separate credentials |
| Manual Docker caching | GitHub Actions cache (type=gha) | 2021 | Significantly faster builds |

**Deprecated/outdated:**
- actions/setup-python@v4: Use v5 (current as of 2026)
- docker/build-push-action@v4: Use v5 (current as of 2026)
- Personal Access Tokens for GHCR: Use GITHUB_TOKEN instead

## Open Questions

1. **Coverage threshold value**
   - What we know: pyproject.toml specifies pytest-cov but no threshold
   - What's unclear: What minimum coverage percentage is appropriate (80%? 90%? 95%?)
   - Recommendation: Start with 90% for production pipeline, can be adjusted later

2. **mypy strictness level**
   - What we know: mypy needs to be added per CICD-01
   - What's unclear: Should we use strict mode or allow gradual typing?
   - Recommendation: Start with `--strict` to catch issues early, add `type: ignore` comments for existing code if needed

3. **MCP Inspector testing**
   - What we know: Success criteria mention "MCP Inspector or equivalent client"
   - What's unclear: How to automate this test in CI (requires running MCP server)
   - Recommendation: Add manual verification step after Phase 4 completion, document in README

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | pyproject.toml (testpaths, markers defined) |
| Quick run command | `pytest -xvs -m "not slow"` |
| Full suite command | `pytest --cov=src --cov-report=term-missing --cov-fail-under=90` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DEPL-05 | CI runs on every push | integration | n/a (workflow validation) | ❌ Phase 4 |
| CICD-01 | CI runs ruff and mypy | integration | `ruff check . && mypy src/` | ✅ ruff, ❌ mypy |
| CICD-02 | CI runs tests with coverage | unit/integration | `pytest --cov=src --cov-fail-under=90` | ✅ tests/ |
| CICD-03 | CI builds Docker image | integration | `docker build .` | ❌ Phase 4 |
| CICD-04 | CI pushes to ghcr.io on main | integration | n/a (workflow validation) | ❌ Phase 4 |

### Sampling Rate
- **Per task commit:** `pytest -xvs -m "not slow"`
- **Per wave merge:** `pytest --cov=src --cov-fail-under=90`
- **Phase gate:** Full CI workflow green (lint → test → build) before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `.github/workflows/ci.yml` — main CI/CD workflow (DEPL-05, CICD-01/02/03/04)
- [ ] `mypy` to dev-dependencies in pyproject.toml (CICD-01)
- [ ] `mypy.ini` or `pyproject.toml` [tool.mypy] configuration (CICD-01)
- [ ] GHCR workflow permissions setup (repository settings, not code)

## Sources

### Primary (HIGH confidence)
- pyproject.toml - Current project configuration (ruff 0.15.5, pytest 9.0.2, pytest-cov 7.0.0)
- uv.lock - Locked dependency versions
- Dockerfile - Multi-stage build with uv package manager
- docker-compose.yml - Current deployment configuration
- tests/conftest.py - Existing test infrastructure

### Secondary (MEDIUM confidence)
- GitHub Actions documentation (workflow syntax, job dependencies)
- Docker build-push-action v5 documentation (caching, GHCR push)
- pytest-cov documentation (--cov-fail-under usage)

### Tertiary (LOW confidence - web search unavailable)
- GitHub Container Registry best practices
- MCP Inspector usage for manual testing
- Specific GitHub Actions version recommendations (need verification after 2026-04-05)

## Metadata

**Confidence breakdown:**
- Standard stack: MEDIUM - tool versions verified from uv.lock, but web search unavailable for latest version verification
- Architecture: MEDIUM - GitHub Actions patterns from official docs, but GHCR-specific patterns need verification
- Pitfalls: HIGH - based on common CI/CD anti-patterns and project-specific analysis
- Test infrastructure: HIGH - existing test setup verified, pytest and fixtures working

**Research date:** 2026-03-12
**Valid until:** 2026-04-12 (30 days - web search service was rate-limited, re-verify when available)

**Notes:**
- Web search services were rate-limited during research (resets 2026-04-05)
- Some findings based on training data and project analysis rather than current documentation
- mypy needs to be added to project dependencies (currently missing)
- GitHub remote configured: https://github.com/AxelFooley/italia-career-mod.git
