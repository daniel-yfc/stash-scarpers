# Scraper Versions

> **快速總覽（zh-TW）：** 本目錄區分公開版（`scrapers/*.yml`）與私有版（`scrapers/private/*.yml`）刮削器。公開版不含登入憑證，可安全分享；私有版可能使用 CDP 會話或 cookie，僅限私人 repo 使用。永遠不要把 session token 寫入公開 repo。

This directory contains Stash scraper YAML files organized by deployment type.

## Directory Structure

```
scrapers/
├── *.yml              # Public versions (safe to share, no credentials)
└── private/
    └── *.yml          # Private versions (may use CDP sessions, personal use)
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

### Private Version (`scrapers/private/*.yml`)

**Use when:** Personal deployment where you control the repository access.

**Characteristics:**

- May include `driver.cookies` with session tokens for sites without CDP
- Requires private repository to prevent credential exposure
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
   - Stash CDP path: `ws://localhost:9222`
   - Sessions persist in browser, not in YAML

2. **HTTP Cookie Mode (Legacy):**
   ```yaml
   driver:
     useCDP: false
     cookies:
       - CookieURL: "https://example.com"
         Cookies:
           - Name: SESSIONID
             Value: "abc123..."
   ```
   - Session tokens embedded in YAML
   - Must rotate when sessions expire
   - Higher security risk

## Security Warnings

### ⚠️ Never commit session tokens to public repos

Session cookies (like `PHPSESSID`, `ECSESSID`, `LOGIN_KEEP_INFO2`) are equivalent to passwords. If committed:

1. Immediately invalidate the session on the target website
2. Rotate all affected credentials
3. Scrub git history or make repo private

### ⚠️ Private scrapers require private repositories

The `scrapers/private/` directory must only exist in private repositories. If your repo becomes public:

- All session tokens are exposed
- Attackers can impersonate your accounts
- Target websites may ban compromised accounts

## Migration Guide

### Public → Private (CDP)

1. Copy `scrapers/Example.yml` to `scrapers/private/Example.yml`
2. Ensure `driver.useCDP: true` is set
3. Remove any `driver.cookies` blocks
4. Setup CDP in Stash:
   - Launch Chrome with `--remote-debugging-port=9222`
   - Stash Settings → System → Application Paths → Chrome CDP path = `ws://localhost:9222`
   - Login to target site in that Chrome window

### Public → Private (HTTP Cookies)

1. Copy `scrapers/Example.yml` to `scrapers/private/Example.yml`
2. Add `driver.cookies` with valid session tokens
3. Ensure `useCDP: false` or omit the field
4. Add `CookieURL` for each cookie entry
5. **Keep repo private**

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

- Public: `Site-Name.yml` (e.g., `CK-Download.yml`)
- Private: Same name in `private/` subfolder (e.g., `private/CK-Download.yml`)
- Do not add `-public` or `-private` suffixes to filenames

## Related Docs

- **Production readiness checklist**: [`docs/04_Production_Gate.md`](../docs/04_Production_Gate.md) — Full A-H workstream checklist for production deployment
- **Automation & CI/CD**: [`docs/05_CI_Workflows.md`](../docs/05_CI_Workflows.md) — Validation scripts, workflows, and local testing
- **Skill references**: [`skills/stash-scraper-builder/references/`](../skills/stash-scraper-builder/references/) — CDP workflow, schema checklist, scraping failures

## References

- Skill documentation: [`skills/stash-scraper-builder/`](../skills/stash-scraper-builder/)
- CDP workflow: [`../skills/stash-scraper-builder/references/cdp-workflow.md`](../skills/stash-scraper-builder/references/cdp-workflow.md)
- Schema checklist: [`../skills/stash-scraper-builder/references/schema-checklist.md`](../skills/stash-scraper-builder/references/schema-checklist.md)
- Scraping failures: [`../skills/stash-scraper-builder/references/debugging.md`](../skills/stash-scraper-builder/references/debugging.md)
- CommunityScrapers canonical reference: https://deepwiki.com/stashapp/CommunityScrapers/

## Questions?

- **Which version should I use?** Start with public. Only use private if the site requires login and CDP is not an option.
- **Can I mix versions?** Yes, but keep private scrapers in `scrapers/private/` and ensure your repo access is restricted.
- **My scraper stopped working:** Check if sessions expired (private HTTP mode) or if the site changed its DOM structure.
