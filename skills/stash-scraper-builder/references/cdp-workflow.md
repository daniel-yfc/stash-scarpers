# Visible-CDP Workflow

**Load when:** standard HTTP cannot retrieve the page (login, paywall, human check, or JS-only DOM).

> **概要（zh-TW）：** 預設不要開 CDP。需要登入時使用「看得見的」Chrome，並先確認 Stash 版本對應的 CDP path。Current upstream guidance uses `http://localhost:9222/json/version`; some builds may accept another attach form, but do not label either form deprecated without version-specific evidence.

Do not emit `driver:` / `useCDP` unless HTTP failed or the user already established that.

Headless CDP still fails on login gates. Use a **visible** debug Chrome, then let Stash attach.

1. YAML contains:

```yaml
driver:
  useCDP: true
```

2. Start Chrome with remote debugging:

```text
Windows:  chrome.exe --remote-debugging-port=9222
macOS:    /Applications/Google Chrome.app/Contents/MacOS/Google Chrome --remote-debugging-port=9222
Linux:    google-chrome --remote-debugging-port=9222
```

3. In Stash (verified against v0.31.1), the Chrome CDP path is at **Settings → Metadata Providers → Scraping** ("Chrome CDP Path"). The current upstream baseline is `http://localhost:9222/json/version`. If a specific build accepts `ws://localhost:9222`, record the Stash version and test evidence before documenting it as an alternative.
4. In that visible Chrome, open the site and complete login / human check until the target content is visible. Cloudflare Turnstile / reCAPTCHA must be solved in this visible browser first — Stash cannot solve them for you.
5. Paste the item URL in Stash and scrape.

Without steps 2–4, a gated `useCDP: true` scraper can return nothing. Always emit these steps with the YAML.

## CookieURL ↔ useCDP (validator-enforced)

- `useCDP: true` forbids `CookieURL` on every `driver.cookies` entry when enforced by the validator; the attached browser session already carries the cookies.
- `useCDP: false` or omitted requires `CookieURL` on every cookie when cookies are used.

## `clicks` need `sleep`

Click items use `xpath` with an optional `sleep` (seconds). **`waitTillPresent` does not exist** — no Stash source (verified against v0.31.1) and no upstream schema (click items allow only `xpath` + `sleep`) support it; do not emit it. Any `driver.clicks` entry that triggers navigation or AJAX must set `sleep` (seconds) so the DOM settles before extraction. A click without `sleep` may scrape the pre-click page.

```yaml
driver:
  useCDP: true
  clicks:
    - xpath: "//button[@id='age-confirm']"
      sleep: 2
```
