# Production Gate

## Overview

This document describes the business requirements and production checklist for scraper deployment (A-H Workstream).

---

## A-H Workstream

### A: Requirements Analysis & Scenario Definition

- Define scraper purpose and target website
- Identify required fields (Title, Date, Image, etc.)
- Document test URLs and scenarios
- Define success criteria

### B: Technical Implementation & Code Review

- Implement scraper YAML following 5 rules
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

- [ ] All 5 rules pass
- [ ] Schema validation passes
- [ ] A-H workstream completed
- [ ] Documentation complete

### After Merge

- [ ] CI/CD pipeline passes
- [ ] Scraper accessible in production
- [ ] Monitoring configured
- [ ] Team notified

---

## Related Files

- [01_System_Architecture.md](01_System_Architecture.md) - System design
- [02_Quality_Gate_Overview.md](02_Quality_Gate_Overview.md) - Chinese overview
- [03_Quality_Gate_Rules.md](03_Quality_Gate_Rules.md) - 5 rules details
- [05_CI_Workflows.md](05_CI_Workflows.md) - CI/CD workflows
- [06_Testing_Guide.md](06_Testing_Guide.md) - Testing guide
- [07_Rendered_DOM_Fixture_Testing.md](07_Rendered_DOM_Fixture_Testing.md) - Rendered-DOM fixtures and failure-page classification

---

**Last Updated**: 2026-09-29
**Status**: ✅ Active
