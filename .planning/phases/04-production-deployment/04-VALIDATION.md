---
phase: 4
slug: production-deployment
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-12
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 |
| **Config file** | pyproject.toml |
| **Quick run command** | `pytest -v` |
| **Full suite command** | `pytest --cov=src --cov-report=term-missing --cov-fail-under=90` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest -v`
- **After every plan wave:** Run `pytest --cov=src --cov-fail-under=90`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 04-01-01 | 01 | 1 | CICD-01 | unit | `pytest tests/test_reddit_client.py -v` | ✅ W0 | ⬜ pending |
| 04-01-02 | 01 | 1 | CICD-01 | unit | `ruff check .` | ✅ W0 | ⬜ pending |
| 04-01-03 | 01 | 1 | CICD-01 | unit | `mypy src/` | ✅ W0 | ⬜ pending |
| 04-02-01 | 02 | 1 | CICD-02, CICD-03 | integration | `pytest --cov=src --cov-fail-under=90` | ✅ W0 | ⬜ pending |
| 04-02-02 | 02 | 1 | CICD-04 | unit | `docker build -t test .` | ✅ W0 | ⬜ pending |
| 04-03-01 | 03 | 2 | CICD-04 | unit | `grep -q "ghcr.io/axelfooley" .github/workflows/ci.yml` | ✅ W0 | ⬜ pending |
| 04-03-02 | 03 | 2 | DEPL-05 | manual | Test with MCP Inspector | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] No Wave 0 needed for CI/CD phase — existing test infrastructure is sufficient

*If none: "Existing infrastructure covers all phase requirements."*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| MCP Inspector testing | DEPL-05 | Requires manual interaction with MCP Inspector | Start server, connect with MCP Inspector, verify tools work |
| GHCR push on main | CICD-04 | Requires GitHub repo permissions | Push to main branch, verify image appears in GHCR |

*If none: "All phase behaviors have automated verification."*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
