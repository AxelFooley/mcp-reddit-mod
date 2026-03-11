---
phase: 3
slug: moderation-tools
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2025-03-11
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.3.4+ |
| **Config file** | pyproject.toml |
| **Quick run command** | `pytest tests/test_moderation_tools.py -v` |
| **Full suite command** | `pytest -v` |
| **Estimated runtime** | ~45 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_moderation_tools.py -v`
- **After every plan wave:** Run `pytest -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 90 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 1 | MODT-01 | integration | `pytest tests/test_moderation_tools.py::test_get_modqueue -x` | ✅ W0 | ⬜ pending |
| 03-01-02 | 01 | 1 | SAFE-01 | unit | `pytest tests/test_moderation_tools.py::test_thing_id_validation -x` | ✅ W0 | ⬜ pending |
| 03-01-03 | 01 | 1 | SAFE-02 | unit | `pytest tests/test_moderation_tools.py::test_error_sanitization -x` | ✅ W0 | ⬜ pending |
| 03-01-04 | 01 | 1 | MODT-02 | integration | `pytest tests/test_moderation_tools.py::test_approve_remove -x` | ✅ W0 | ⬜ pending |
| 03-01-05 | 01 | 1 | MODT-03 | integration | `pytest tests/test_moderation_tools.py::test_remove_item -x` | ✅ W0 | ⬜ pending |
| 03-01-06 | 01 | 1 | MODT-04 | integration | `pytest tests/test_moderation_tools.py::test_ban_user -x` | ✅ W0 | ⬜ pending |
| 03-02-01 | 02 | 2 | REDI-04 | unit | `pytest tests/test_moderation_tools.py::test_timeout_wrapper -x` | ✅ W0 | ⬜ pending |
| 03-02-02 | 02 | 2 | REDI-03 | unit | `pytest tests/test_moderation_tools.py::test_exception_propagation -x` | ✅ W0 | ⬜ pending |
| 03-02-03 | 02 | 2 | MODT-05 | integration | `pytest tests/test_moderation_tools.py::test_get_user_history -x` | ✅ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_moderation_tools.py` — stubs for all MODT, SAFE, REDI requirements
- [ ] `tests/conftest.py` — update with PRAW mock fixtures for moderation APIs
- [ ] Timeout test infrastructure in conftest.py

*Wave 0 plan created: 03-00-PLAN.md*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Real Reddit API calls | MODT-01, MODT-02, MODT-03, MODT-04, MODT-05 | Requires valid Reddit mod credentials and test subreddit | Run with real .env file, verify each tool works against actual subreddit |
| Timeout protection | REDI-03 | Requires network delay simulation | Mock slow PRAW responses, verify timeout triggers |

*If none: "All phase behaviors have automated verification."*

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 90s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
