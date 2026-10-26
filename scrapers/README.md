# Scraper Versions

> **快速總覽（zh-TW）：** 本公開 Repository 包含 `scrapers/*.yml` 與已追蹤的 `scrapers/private/*.yml` 變體。`private/` 只是目錄名稱，不具存取控制；**兩處都禁止提交真實 Cookie、Token 或登入憑證**。需要個人 Session 的部署副本必須放在獨立的私人環境。

This directory contains Stash scraper YAML files organized by deployment type.

## Directory Structure

```
scrapers/
├── *.yml              # Public versions (safe to share, no credentials)
└── private/
    └── *.yml          # Publicly tracked variants; NOT a secret storage area
```

## Public vs Private Scrapers

### Public Version (`scrapers/*.yml`)

**Use when:** Sharing scrapers publicly or in community repositories.

**Characteristics:**

- No `driver.cookies` configuration
- No session tokens or credentials in git history
- May use `driver.useCDP: true` for age-gated sites (requires user to login via visible Chrome)
- Safe to commit to public repositories
- Follows CommunityScrapers security best practices

**Example:**

```yaml
driver:
  useCDP: true
  headers:
    - Key: User-Agent
      Value: "Mozilla/5.0..."
  # NO cookies section
```

### Private deployment (separate from publicly tracked variants)

**Use when:** Deploying a personal configuration in a genuinely private repository or local secrets-controlled environment. **The `scrapers/private/` folder in this repository is public**, and its contents must remain free of session material.

**Characteristics:**

- Publicly tracked variants must not include active session tokens or credentials
- Personal copies may use `driver.cookies` only outside this public Git repository, with strict access control
- Higher maintenance burden (sessions expire, need rotation)
- **Not safe for public sharing**

**Two private deployment modes:**

1. **CDP Mode (Recommended):**

   ```yaml
   driver:
     useCDP: true
     # No CookieURL - browser session carries cookies
   ```

   - Login via visible Chrome browser
   - In Stash v0.31.1: Settings → Metadata Providers → Scraping → Chrome CDP Path: `http://localhost:9222/json/version`
   - Sessions persist in browser, not in YAML

2. **HTTP Cookie Mode (Legacy):**
   ```yaml
   driver:
     useCDP: false
     cookies:
       - CookieURL: "https://example.com"
         Cookies:
           - Name: SESSIONID
             Value: "<private-session-value-never-commit>"
   ```
   - Session tokens embedded in YAML
   - Must rotate when sessions expire
   - Higher security risk

## Security Warnings

### ⚠️ Never commit session tokens to public repos

Session cookies (like `PHPSESSID`, `ECSESSID`, `LOGIN_KEEP_INFO2`) are equivalent to passwords. Only fully commented placement templates with explicit `<LOCAL_ONLY_VALUE>` values may be committed. If committed:

1. Immediately invalidate the session on the target website
2. Rotate all affected credentials
3. Scrub git history or make repo private

### ⚠️ `private/` does not make files private

The `scrapers/private/` directory is tracked by this **public** repository. Only credentials-bearing deployment copies belong in genuinely private repositories or secret-controlled local environments. If active tokens were ever committed publicly, revoke them and review repository history immediately.

## Migration Guide

### Public → Private (CDP)

1. Copy `scrapers/Example.yml` into an **external, private** deployment directory (not this repository's tracked `scrapers/private/`)
2. Ensure `driver.useCDP: true` is set
3. Remove any `driver.cookies` blocks
4. Setup CDP in Stash:
   - Launch Chrome with `--remote-debugging-port=9222`
   - Stash v0.31.1: Settings → Metadata Providers → Scraping → Chrome CDP Path = `http://localhost:9222/json/version` (verify other versions)
   - Login to target site in that Chrome window

### Public → Private (HTTP Cookies)

1. Copy `scrapers/Example.yml` into an **external, private** deployment directory (not this repository's tracked `scrapers/private/`)
2. Add `driver.cookies` with valid session tokens
3. Ensure `useCDP: false` or omit the field
4. Add `CookieURL` for each cookie entry
5. **Keep deployment files and active session material out of this public repo**

### Private → Public

1. Start from the public version (or create new)
2. Remove all `driver.cookies` sections
3. Add `useCDP: true` if the site requires login
4. Update comments to explain CDP setup steps
5. Verify no credentials in git history

## Testing Checklist

Before deploying any scraper:

- [ ] Validator passes (no schema errors)
- [ ] URL patterns are sorted alphabetically (`validator -s`)
- [ ] No hardcoded session tokens in public versions
- [ ] CDP setup documented in YAML comments (if applicable)
- [ ] Tested on 3+ real URLs with expected field values
- [ ] Private versions stored in private repo only

## File Naming

- Public: CamelCase `SiteName.yml` (e.g., `ClubCK.yml`); `CK-Download.yml` is a historical hyphenated exception
- Private: Same name in `private/` subfolder (e.g., `private/ClubCK.yml`)
- Do not add `-public` or `-private` suffixes to filenames

## Related Docs

- **Production readiness checklist**: [`docs/30-production-gate.md`](../docs/30-production-gate.md) — Full A-H workstream checklist for production deployment
- **Automation & CI/CD**: [`docs/40-ci-workflows.md`](../docs/40-ci-workflows.md) — Validation scripts, workflows, and local testing
- **Skill references**: [`skills/stash-scraper-builder/references/`](../skills/stash-scraper-builder/references/) — CDP workflow, schema checklist, scraping failures

## References

- Skill documentation: [`skills/stash-scraper-builder/`](../skills/stash-scraper-builder/)
- CDP workflow: [`../skills/stash-scraper-builder/references/cdp-workflow.md`](../skills/stash-scraper-builder/references/cdp-workflow.md)
- Schema checklist: [`../skills/stash-scraper-builder/references/schema-checklist.md`](../skills/stash-scraper-builder/references/schema-checklist.md)
- Scraping failures: [`../skills/stash-scraper-builder/references/debugging.md`](../skills/stash-scraper-builder/references/debugging.md)
- CommunityScrapers canonical reference: https://deepwiki.com/stashapp/CommunityScrapers/

## Questions?

- **Which version should I use?** Start with public. Only use private if the site requires login and CDP is not an option.
- **Can I mix versions?** Not within this public repository: `scrapers/private/` is tracked and public. Store any credentials-bearing deployment copy outside the Git working tree.
- **My scraper stopped working:** Check if sessions expired (private HTTP mode) or if the site changed its DOM structure.
