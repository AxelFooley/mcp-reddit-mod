---
phase: 1
slug: mcp-server-foundation
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2025-03-11
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.3.4+ |
| **Config file** | pyproject.toml |
| **Quick run command** | `pytest tests/test_server.py -v` |
| **Full suite command** | `pytest -v` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_server.py -v`
- **After every plan wave:** Run `pytest -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | MCPF-01 | unit | `pytest tests/test_server.py::test_http_transport` | ❌ W0 | ⬜ pending |
| 01-01-02 | 01 | 1 | MCPF-02 | unit | `pytest tests/test_server.py::test_endpoint_accessible` | ❌ W0 | ⬜ pending |
| 01-01-03 | 01 | 1 | MCPF-03 | unit | `pytest tests/test_server.py::test_tool_discovery` | ❌ W0 | ⬜ pending |
| 01-01-04 | 01 | 1 | MCPF-04 | unit | `pytest tests/test_server.py::test_server_metadata` | ❌ W0 | ⬜ pending |
| 01-01-05 | 01 | 1 | MCPF-05 | unit | `pytest tests/test_server.py::test_error_responses` | ❌ W0 | ⬜ pending |
| 01-02a-01 | 02a | 1 | DEPL-01 | unit | `docker build -t test .` | ❌ W0 | ⬜ pending |
| 01-02a-02 | 02a | 1 | DEPL-02 | unit | `docker build -t test .` | ❌ W0 | ⬜ pending |
| 01-02b-01 | 02b | 1 | DEPL-03 | unit | `docker compose config` | ❌ W0 | ⬜ pending |
| 01-02b-02 | 02b | 1 | DEPL-04 | manual | Verify .env.example contains all 5 variables | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `tests/test_server.py` — stubs for MCPF-01 through MCPF-05
- [x] `tests/conftest.py` — shared fixtures for MCP client/server
- [x] `pytest` and `pytest-anyio` installed via pyproject.toml

*Wave 0 complete: Plan 01-00 creates all test infrastructure.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| .env.example completeness | DEPL-04 | Human verification of documentation quality | Check that .env.example lists REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USERNAME, REDDIT_PASSWORD, REDDIT_USER_AGENT with descriptions |
| Docker external access | MCPF-02 | Requires network access from outside container | Start container with `docker compose up`, curl `http://localhost:8000/mcp` from host machine |

*If none: "All phase behaviors have automated verification."*

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 60s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
