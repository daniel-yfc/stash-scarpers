---
doc_id: DOC-OPS-30
title: Production Gate
status: active
layer: repository
owner: maintainer
audience:
  - agent
  - maintainer
last_verified: "2026-10-07"
authority: canonical
routing:
  intents:
    - production-readiness
---

# Production Gate

## Overview

This document describes the business requirements and production checklist for scraper deployment (A-H Workstream).

A completed checklist is not production readiness by itself. Schema validation, policy-gate success, fixture verification, live Stash/CDP verification, and production readiness are separate evidence states.

---

## A-H Workstream

### A: Requirements Analysis & Scenario Definition

- Define scraper purpose and target website
- Identify required fields (Title, Date, Image, etc.)
- Document test URLs and scenarios
- Define success criteria

### B: Technical Implementation & Code Review

- Implement scraper YAML following the rules in [`21-quality-gate-rules.md`](21-quality-gate-rules.md)
- Code review for best practices
- Verify CDP configuration
- Public scrapers (`scrapers/*.yml`) contain no `driver.cookies`; session-dependent scrapers belong in `scrapers/private/`

### C: Content Quality & Field Coverage

- Verify all required fields are extracted
- Check data quality and formatting
- Validate image URLs
- Test date parsing

### D: Testing Verification & Evaluation

- Run local quality gate tests
- Verify schema validation passes
- Test with multiple URLs
- JS-rendered sites: verify against completed, sanitized rendered-DOM fixtures; record live Stash/CDP status separately
- Document test results

### E: Documentation Completeness

- Add `# Last Updated` header
- Document verification status
- Add test URLs in comments
- Update README if needed

### F: Security Check

- No hardcoded credentials
- No sensitive data in scraper
- Never commit, copy, or reconstruct session material: credentials, session cookies, clearance tokens, CSRF values, browser-profile data, analytics identifiers — not from private scrapers, not from repository history. Record policy and status only.
- Verify external dependencies
- Check for security vulnerabilities

### G: Performance Optimization

- Optimize XPath selectors
- Minimize API calls
- Add proper error handling
- Test execution time

### H: Deployment & Monitoring

- Merge to main branch
- Monitor CI/CD pipeline
- Track scraper performance
- Set up alerts for failures

---

## Production Checklist

### Before Merge

- [ ] Quality-gate rules in [`21-quality-gate-rules.md`](21-quality-gate-rules.md) pass
- [ ] Schema validation passes
- [ ] A-H workstream completed
- [ ] Documentation complete
- [ ] A green workflow is not treated as production readiness

### After Merge

- [ ] CI/CD pipeline passes
- [ ] Scraper accessible in production
- [ ] Monitoring configured
- [ ] Team notified

---

## Related Files

- [10-system-architecture.md](10-system-architecture.md) - System design
- [20-quality-gate-overview.md](20-quality-gate-overview.md) - Chinese overview
- [21-quality-gate-rules.md](21-quality-gate-rules.md) - Quality-gate rules
- [40-ci-workflows.md](40-ci-workflows.md) - CI/CD workflows
- [50-testing-guide.md](50-testing-guide.md) - Testing guide
- [51-rendered-dom-fixture-testing.md](51-rendered-dom-fixture-testing.md) - Rendered-DOM fixtures and failure-page classification

---

**Status**: ✅ Active
