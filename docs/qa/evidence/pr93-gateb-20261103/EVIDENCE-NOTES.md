# Evidence notes — PR #93 Gate B (pr93-gateb-20261103)

Committed here: offline verification (E1–E8 + manifest), live run 1 (HEAD 86e34a2)
and live run 2 (HEAD ce7ef6c) GraphQL request/response JSON, package/config
records, lease records, and SHA-256 manifests of the full local bundles.

Retained only in the local QA bundle (~/workspace/qa-pr93-gateb-20261103/),
referenced by digest — full text not committed because it is third-party page
content or contains raw page-widget text:

| File | SHA-256 | Note |
|---|---|---|
| evidence-live/dom-284.html | f10858aeb0c02fd8bcaab90b349f80ad4a37cdf6b9301a2ae5707b6abc4fc324 | rendered DOM full text (~900KB) via stash-test Chrome CDP |
| evidence-live/dom-282.html | f0b654feaead88fed77d886ae9ab96b3051d9f614e229eb6b4003ce3bf6851f5 | rendered DOM full text (~900KB) |
| evidence-live/L11-gvwiki-control.json | d6a50bf6c9bcc57705e68dc0929d194e34bf5b382f1f10966911f6752cf2b599 | GVWiki control scrape; result: Title + Code GV-OAV1372 returned (PASS) |
| evidence-live2/R8-gvwiki-control.json | 1d8e96b5cf80c3568a36338ec5c8a9099c6752e4ccd5b5b40856642e8cec141e | same control, run 2 (PASS) |

The MANIFEST*.sha256 files describe the complete local bundles (including the
retained files above). All committed JSON was sanitized before posting: tailnet
addresses replaced with <tailnet-ip>, temporary isolated-source URLs replaced
with <isolated-source-url-expired>. No credentials, cookies or tokens appear in
any artifact (the control scrapes contain no secrets; their raw files are
retained locally only because the scraped Details field embeds page widget
text).
