---
phase: 2
slug: reddit-integration
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2025-03-11
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.3.4+ |
| **Config file** | pyproject.toml |
| **Quick run command** | `pytest tests/test_reddit_client.py -v` |
| **Full suite command** | `pytest -v` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_reddit_client.py -v`
- **After every plan wave:** Run `pytest -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | REDI-01 | unit | `pytest tests/test_reddit_client.py::test_client_initializes_from_env` | ❌ W0 | ⬜ pending |
| 02-01-02 | 01 | 1 | REDI-02 | unit | `pytest tests/test_reddit_client.py::test_script_app_auth` | ❌ W0 | ⬜ pending |
| 02-01-03 | 01 | 1 | REDI-01 | integration | `pytest tests/test_reddit_client.py::test_authenticates_with_reddit_api` | ❌ W0 | ⬜ pending |
| 02-01-04 | 01 | 1 | REDI-02 | unit | `pytest tests/test_reddit_client.py::test_invalid_credentials_safe_error` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_reddit_client.py` — stubs for REDI-01, REDI-02
- [ ] `tests/conftest.py` — update with Reddit client fixtures
- [ ] PRAW dependency added to pyproject.toml

*If none: "Existing infrastructure covers all phase requirements."*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Actual Reddit API connection | REDI-01 | Requires valid Reddit credentials | Run with real .env file, verify no authentication errors |
| Error message clarity | REDI-02 | Human judgment of message quality | Trigger error with bad credentials, verify no credential leakage |

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
