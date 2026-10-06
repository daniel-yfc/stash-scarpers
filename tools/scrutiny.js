#!/usr/bin/env node
// Real-case scrutiny: for each scraper, derive a real scene URL via its search
// endpoint, fetch the page, then exercise the sceneScraper XPaths to see what
// actually populates. Reports per-scraper field coverage.
//
// Run: node tools/scrutiny.js [scraper-name.yml ...]
//      node tools/scrutiny.js --all
//      node tools/scrutiny.js --probe=word1,word2 scraper.yml
//      node tools/scrutiny.js --paginate scraper.yml
//      node tools/scrutiny.js --search scraper.yml
//      node tools/scrutiny.js --url=<url> scraper.yml
//      node tools/scrutiny.js --cookie=<str> scraper.yml
//      node tools/scrutiny.js --help
//
// Network: yes, hits the live upstream sites. Be polite.

import fs from "node:fs";
import path from "node:path";
import yaml from "yaml";
import { JSDOM, VirtualConsole } from "jsdom";

const quietConsole = new VirtualConsole();
quietConsole.on("jsdomError", () => {});
const _origConsoleError = console.error;
console.error = (...args) => {
  const s = args.join(" ");
  if (/Could not parse CSS stylesheet/.test(s)) return;
  _origConsoleError.apply(console, args);
};

const ROOT = process.cwd();
const SCRAPERS = path.join(ROOT, "scrapers");
const POLITE_UA =
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36";

const XP_ALL = 7;

function showHelp() {
  console.log(`
Usage: node tools/scrutiny.js [options] [scraper.yml ...]

Options:
  --all                 Run scrutiny across all scrapers
  --probe=<csv>         Custom search probe terms
  --paginate            Walk pages 1-3 when searching
  --multi               Test multiple candidate scene URLs
  --search              Also evaluate searchScraper (default: always on)
  --url=<url>           Evaluate sceneScraper directly
  --cookie=<str>        Provide cookie header string
  --help                Show this help

Test Settings File:
  If scrapers/<scraper-name>.test.yaml exists, it will be auto-loaded.
  Also supports scrapers/private/<scraper-name>.test.yaml.
  Test settings are kept alongside the scraper definition.

  Simplified format:
    - url: string | array (auto-enables multi if array)
    - probe: string | array (auto-enables multi if array)
    - cookie: string (auto-detects Netscape or header format)
    - multi: boolean (default: auto)
    - search: boolean (default: true, always test search unless false)

Examples:
  node tools/scrutiny.js scrapers/ACCEED.yml
  node tools/scrutiny.js scrapers/RGBEE.yml  # auto-loads scrapers/RGBEE.test.yaml
`);
}

function parseArgs(argv) {
  const opts = {
    files: [],
    probe: null,
    paginate: false,
    multiUrl: false,
    searchReport: false,
    url: null,
    cookie: null,
  };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--help" || a === "-h") {
      opts.help = true;
      continue;
    }
    if (a === "--all") {
      opts.all = true;
      continue;
    }
    if (a === "--paginate") {
      opts.paginate = true;
      continue;
    }
    if (a === "--multi") {
      opts.multiUrl = true;
      continue;
    }
    if (a === "--search") {
      opts.searchReport = true;
      continue;
    }
    if (a.startsWith("--probe=")) {
      opts.probe = a.slice(8).split(",");
      continue;
    }
    if (a.startsWith("--url=")) {
      opts.url = a.slice(6);
      continue;
    }
    if (a.startsWith("--cookie=")) {
      opts.cookie = a.slice(9);
      continue;
    }
    if (a.startsWith("-")) continue;
    opts.files.push(a);
  }
  return opts;
}

function listScrapers() {
  const out = [];
  for (const dir of [SCRAPERS, path.join(SCRAPERS, "private")]) {
    if (!fs.existsSync(dir)) continue;
    for (const f of fs.readdirSync(dir).filter((x) => x.endsWith(".yml"))) {
      out.push(path.join(dir, f));
    }
  }
  return out.sort();
}

function loadTestSidecar(scraperFile) {
  const basename = path.basename(scraperFile, ".yml");
  const dirname = path.dirname(scraperFile);

  // Try scrapers/RGBEE.test.yaml (same directory as scraper)
  const sidecarPath = path.join(dirname, `${basename}.test.yaml`);

  if (!fs.existsSync(sidecarPath)) {
    return null;
  }

  try {
    const content = fs.readFileSync(sidecarPath, "utf8");
    const settings = yaml.parse(content) || {};
    console.log(`[INFO] Loaded test settings: ${sidecarPath}`);
    return settings;
  } catch (e) {
    console.warn(`[WARN] Failed to load test settings: ${sidecarPath} - ${e.message}`);
    return null;
  }
}

function parseNetscapeCookies(content) {
  const lines = content.split("\n");
  const cookies = [];

  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;

    const parts = trimmed.split("\t");
    if (parts.length >= 7) {
      const name = parts[parts.length - 2];
      const value = parts[parts.length - 1];

      try {
        const decodedValue = decodeURIComponent(value);
        cookies.push(`${name}=${decodedValue}`);
      } catch {
        cookies.push(`${name}=${value}`);
      }
    }
  }

  return cookies.join("; ");
}

function parseCookieInput(cookieInput) {
  if (!cookieInput) return "";

  const trimmed = String(cookieInput).trim();

  if (trimmed.includes("\t")) {
    return parseNetscapeCookies(trimmed);
  }

  if (trimmed.includes("\n")) {
    const lines = trimmed.split("\n");
    const hasTabs = lines.some(line => line.includes("\t"));
    if (hasTabs) {
      return parseNetscapeCookies(trimmed);
    }
  }

  return trimmed;
}

function mergeOptions(cliOpts, scraperFile) {
  const sidecar = loadTestSidecar(scraperFile);

  if (!sidecar) {
    return cliOpts;
  }

  const merged = { ...cliOpts };

  // URL: sidecar takes precedence if CLI didn't specify
  if (!merged.url) {
    let sidecarUrl = null;
    if (sidecar.urls && Array.isArray(sidecar.urls) && sidecar.urls.length > 0) {
      sidecarUrl = sidecar.urls;
    } else if (sidecar.url) {
      sidecarUrl = Array.isArray(sidecar.url) ? sidecar.url : [sidecar.url];
    }

    if (sidecarUrl) {
      merged._urls = sidecarUrl;
      merged.url = merged._urls[0];
    }
  } else if (!merged._urls) {
    merged._urls = [merged.url];
  }

  // Probe: sidecar takes precedence if CLI didn't specify
  if (!merged.probe) {
    let sidecarProbe = null;
    if (sidecar.probes && Array.isArray(sidecar.probes)) {
      sidecarProbe = sidecar.probes;
    } else if (sidecar.probe) {
      sidecarProbe = Array.isArray(sidecar.probe) ? sidecar.probe : [sidecar.probe];
    }

    if (sidecarProbe) {
      merged.probe = sidecarProbe;
    }
  } else if (!Array.isArray(merged.probe)) {
    merged.probe = [merged.probe];
  }

  // Cookie: parse and merge
  if (sidecar.cookie) {
    const parsedCookie = parseCookieInput(sidecar.cookie);
    if (parsedCookie) {
      merged.cookie = parsedCookie;
    }
  }

  // Auto-detect multi mode
  const hasMultipleUrls = merged._urls && merged._urls.length > 1;
  const hasMultipleProbes = merged.probe && merged.probe.length > 1;

  if (sidecar.multi === true) {
    merged.multiUrl = true;
  } else if (sidecar.multi === false) {
    merged.multiUrl = false;
  } else {
    merged.multiUrl = hasMultipleUrls || hasMultipleProbes;
  }

  // Search: default true (always test search unless explicitly disabled)
  // Search and URL tests are independent
  if (sidecar.search === false) {
    merged.searchReport = false;
  } else {
    merged.searchReport = true;  // Default: always test search
  }

  // Flags: sidecar overrides defaults (if explicitly set)
  if (typeof sidecar.paginate === "boolean") {
    merged.paginate = sidecar.paginate;
  }

  return merged;
}

async function fetchHTML(url, cookie, attempt = 1) {
  const headers = {
    "User-Agent": POLITE_UA,
    "Accept-Language": "ja,en;q=0.5",
  };
  if (cookie) {
    headers["Cookie"] = cookie;
  }
  try {
    const res = await fetch(url, { headers, redirect: "follow" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const ct = res.headers.get("content-type") || "";
    if (!/text\/html|xml/.test(ct)) throw new Error(`non-HTML content-type: ${ct}`);
    return await res.text();
  } catch (e) {
    if (attempt < 2 && /ECONNRESET|fetch failed|socket hang up/i.test(e.message)) {
      await new Promise((r) => setTimeout(r, 500));
      return fetchHTML(url, cookie, attempt + 1);
    }
    throw e;
  }
}

function buildProbeURL(template, probe, page) {
  let url = template
    .replaceAll("{}", encodeURIComponent(probe))
    .replaceAll("{query}", encodeURIComponent(probe))
    .replaceAll("{q}", encodeURIComponent(probe))
    .replaceAll("{title}", encodeURIComponent(probe));

  if (page != null) {
    if (url.includes("{page}")) {
      url = url.replaceAll("{page}", page);
    } else if (url.includes("{p}")) {
      url = url.replaceAll("{p}", page);
    } else if (/[?&]page=/.test(url)) {
      url = url.replace(/([?&]page=)\d+/, `$1${page}`);
    } else if (/[?&]p=/.test(url)) {
      url = url.replace(/([?&]p=)\d+/, `$1${page}`);
    } else {
      url += (url.includes("?") ? "&" : "?") + "page=" + page;
    }
  }
  return url;
}

function defaultProbes(scraperDoc) {
  const queryURL = (scraperDoc.sceneByName || scraperDoc.sceneByFragment || {}).queryURL || "";

  // 通用預設關鍵字
  // 預期有結果：中出、ノンケ
  // 預期無結果：蔣中正馮翊綱一條龍、臣亮言先帝創業未半而中道崩殂
  const probes = [
    "中出",
    "ノンケ",
    "蔣中正馮翊綱一條龍",
    "臣亮言先帝創業未半而中道崩殂",
  ];

  // 特定網站的額外關鍵字
  if (/acceed/i.test(queryURL)) probes.unshift("ACST", "ACCEED");
  if (/ck-download/i.test(queryURL)) probes.unshift("CK", "男");
  if (/games-video/i.test(queryURL)) probes.unshift("GV-OAV", "GVO");
  if (/mensrush/i.test(queryURL)) probes.unshift("MR-");
  if (/ko-video|ko-shop|ko-tube/i.test(queryURL)) probes.unshift("KBEA", "KBO");
  if (/justice/i.test(queryURL)) probes.unshift("JUSTICE");
  if (/hunks/i.test(queryURL)) probes.unshift("HUNKS");
  return probes;
}

function extractSceneURLs(searchHTML, scraperDoc, baseURL, probe, page) {
  const dom = new JSDOM(searchHTML, { virtualConsole: quietConsole });
  const xdoc = dom.window.document;
  const searchScraper = (scraperDoc.xPathScrapers || {})[
    (scraperDoc.sceneByName || scraperDoc.sceneByFragment || {}).scraper
  ];
  if (!searchScraper) return [];

  const urlsSel = searchScraper.scene && searchScraper.scene.URLs;
  if (!urlsSel) return [];

  let candidates = [];
  try {
    let sel = typeof urlsSel === "string" ? urlsSel : urlsSel.selector;
    if (!sel) return [];
    const common = searchScraper.common || {};
    for (const [k, v] of Object.entries(common)) {
      const key = k.startsWith("$") ? k : "$" + k;
      sel = sel.replaceAll(key, v);
    }
    const snap = xdoc.evaluate(sel, xdoc, null, XP_ALL, null);
    for (let i = 0; i < snap.snapshotLength; i++) {
      const node = snap.snapshotItem(i);
      let href = node.nodeValue || node.textContent || "";
      if (!href) continue;
      if (typeof urlsSel === "object" && urlsSel.postProcess) {
        for (const pp of urlsSel.postProcess) {
          if (pp.replace) {
            for (const r of pp.replace) {
              href = href.replace(new RegExp(r.regex), r.with);
            }
          }
        }
      }
      try {
        const full = new URL(href, baseURL).toString();
        candidates.push(full);
      } catch {
        // ignore invalid URL
      }
    }
  } catch {
    // evaluate failed
  }

  if (candidates.length === 0) {
    const patterns = (scraperDoc.sceneByURL || []).map((s) => s.url);
    const snap = xdoc.evaluate("//a[@href]/@href", xdoc, null, XP_ALL, null);
    for (let i = 0; i < snap.snapshotLength; i++) {
      const href = snap.snapshotItem(i).nodeValue;
      if (!href) continue;
      try {
        const full = new URL(href, baseURL).toString();
        for (const pat of patterns) {
          const patNorm = pat.replace(/^https?:\/\//, "").replace(/^www\./, "");
          const hostAndPath = full.replace(/^https?:\/\//, "").replace(/^www\./, "");
          if (hostAndPath.startsWith(patNorm.split("?")[0]) || hostAndPath.includes(patNorm)) {
            candidates.push(full);
            break;
          }
        }
      } catch {
        // ignore invalid URL
      }
    }
  }

  const deduped = [];
  const seen = new Set();
  for (const c of candidates) {
    if (!seen.has(c)) {
      seen.add(c);
      deduped.push({ url: c, probe, page });
    }
  }
  return deduped;
}

async function findSceneURLs(scraperDoc, opts) {
  const sb = scraperDoc.sceneByName || scraperDoc.sceneByFragment;
  if (!sb || !sb.queryURL) {
    return { urls: [], reason: "no sceneByName/sceneByFragment.queryURL" };
  }

  const probes = opts.probe || defaultProbes(scraperDoc);
  const pages = opts.paginate ? [1, 2, 3] : [null];

  const PER_PROBE_CAP = 5;
  const seen = new Set();
  const candidates = [];
  let lastReason = "";

  for (const probe of probes) {
    for (const page of pages) {
      let perProbeAdded = 0;
      const probeURL = buildProbeURL(sb.queryURL, probe, page);
      let html;
      try {
        html = await fetchHTML(probeURL, opts.cookie);
      } catch (e) {
        lastReason = `search fetch failed: ${e.message}`;
        continue;
      }
      const hasLoginGate =
        /(?:window\.location|location\.href)\s*=\s*["'][^"']*login\.(?:php|html)/i.test(html) ||
        /<form[^>]+action=["'][^"']*login\.(?:php|html)["']/i.test(html) ||
        /<input[^>]+(?:type=["']password["']|name=["']pass(?:word)?["'])/i.test(html);
      const hasResults =
        html.includes("movie_detail.php") ||
        html.includes("movie_box") ||
        html.includes("item_img") ||
        html.includes("detail.php?product_id") ||
        html.includes("list_title");
      if (hasLoginGate && !hasResults) {
        lastReason = "search redirected to login";
        continue;
      }
      const cands = extractSceneURLs(html, scraperDoc, probeURL, probe, page);
      for (const c of cands) {
        if (!seen.has(c.url) && perProbeAdded < PER_PROBE_CAP) {
          seen.add(c.url);
          candidates.push(c);
          perProbeAdded++;
        }
      }
      if (!opts.paginate && !opts.multiUrl && candidates.length > 0) {
        return {
          urls: candidates,
          probeCount: 1,
          pageCount: 1,
          searchURL: sb.queryURL,
        };
      }
      if (pages.length > 1) {
        await new Promise((r) => setTimeout(r, 200));
      }
    }
    if (!opts.multiUrl && candidates.length > 0) {
      break;
    }
  }

  return {
    urls: candidates,
    probeCount: probes.length,
    pageCount: pages.length,
    searchURL: sb.queryURL,
    reason: candidates.length === 0 ? lastReason || "no candidates from any probe" : null,
  };
}

function runXPath(selector, ctx) {
  const { doc, common } = ctx;
  let sel = selector;
  if (common) {
    for (const [k, v] of Object.entries(common)) {
      const key = k.startsWith("$") ? k : "$" + k;
      sel = sel.replaceAll(key, v);
    }
  }

  try {
    const snap = doc.evaluate(sel, doc, null, XP_ALL, null);
    const count = snap.snapshotLength;
    const samples = [];
    for (let i = 0; i < Math.min(count, 3); i++) {
      const node = snap.snapshotItem(i);
      const text = node.nodeValue || node.textContent || "";
      samples.push(text.trim());
    }
    return { count, samples, selector: sel, error: null };
  } catch (e) {
    return { count: 0, samples: [], selector: sel, error: e.message };
  }
}

function tryFieldWithDoc(val, ctx) {
  if (typeof val === "string") return runXPath(val, ctx);
  if (val && typeof val === "object") {
    const out = {};
    if (val.selector) out.selector = runXPath(val.selector, ctx);
    if (val.fixed !== undefined) out.fixed = val.fixed;
    if (val.postProcess) out.postProcess = val.postProcess;
    if (val.Name) out.Name = tryFieldWithDoc(val.Name, ctx);
    return out;
  }
  return null;
}

function collectSelectors(val, acc = []) {
  if (!val) return acc;
  if (val.selector) acc.push(val.selector);
  if (val.Name) collectSelectors(val.Name, acc);
  return acc;
}

function summarize(v) {
  if (v == null) return "∅";
  if (typeof v === "string") return v;
  if (v.selector) {
    const s = v.selector;
    if (s.error) return `ERROR: ${s.message || JSON.stringify(s)}`;
    if (s.count === 0) return "∅ (0 nodes)";
    return `${s.count} nodes | ${(s.samples || []).map((x) => '"' + x.replace(/\s+/g, " ").slice(0, 60) + '"').join(" / ")}`;
  }
  if (v.Name) {
    return summarize(v.Name);
  }
  if (v.fixed) return `<fixed:${v.fixed}>`;
  return JSON.stringify(v).slice(0, 200);
}

function countPopulated(fields) {
  let n = 0;
  for (const attrs of Object.values(fields)) {
    for (const v of Object.values(attrs)) {
      for (const sel of collectSelectors(v)) {
        if (sel && sel.count > 0) n++;
      }
    }
  }
  return n;
}

function countTotal(fields) {
  let n = 0;
  for (const attrs of Object.values(fields)) {
    for (const v of Object.values(attrs)) {
      n += collectSelectors(v).length;
    }
  }
  return n;
}

async function testScraper(file, opts) {
  const rel = path.relative(ROOT, file);
  const doc = yaml.parse(fs.readFileSync(file, "utf8"));
  const entry = { file: rel, name: doc.name };

  let tested = [];
  let found = { urls: [] };

  if (opts._urls && opts._urls.length > 0) {
    tested = opts._urls.map((url, i) => ({
      url,
      probe: "config",
      page: opts._urls.length > 1 ? i : null,
    }));
    entry.urlCandidates = opts._urls.length;
  } else if (opts.url) {
    tested = [{ url: opts.url, probe: "direct", page: null }];
    entry.urlCandidates = 1;
  } else {
    found = await findSceneURLs(doc, opts);
    if (found.urls.length === 0) {
      entry.status = "SKIP";
      entry.reason = found.reason;
      return entry;
    }
    const limit = opts.multiUrl ? found.urls.length : 1;
    tested = found.urls.slice(0, limit);
    entry.probeCount = found.probeCount;
    entry.pageCount = found.pageCount;
    entry.searchURL = found.searchURL;
    entry.urlCandidates = found.urls.length;
  }

  const perUrl = [];
  for (const cand of tested) {
    const urlEntry = { url: cand.url, probe: cand.probe, page: cand.page };
    let html;
    try {
      html = await fetchHTML(cand.url, opts.cookie);
    } catch (e) {
      urlEntry.status = "FETCH_FAIL";
      urlEntry.reason = e.message;
      perUrl.push(urlEntry);
      continue;
    }
    const dom = new JSDOM(html, { virtualConsole: quietConsole });
    const xdoc = dom.window.document;
    const sceneScraper = (doc.xPathScrapers || {})[doc.sceneByURL?.[0]?.scraper];
    if (!sceneScraper) {
      urlEntry.status = "NO_SCENE_SCRAPER";
      perUrl.push(urlEntry);
      continue;
    }
    const ctx = { doc: xdoc, common: sceneScraper.common || {} };
    const result = {};
    if (sceneScraper.scene) {
      result.scene = {};
      for (const [k, v] of Object.entries(sceneScraper.scene)) {
        result.scene[k] = tryFieldWithDoc(v, ctx);
      }
    }
    urlEntry.fields = result;
    urlEntry.status = "OK";
    perUrl.push(urlEntry);
    await new Promise((r) => setTimeout(r, 300));
  }

  // Also exercise the searchScraper on the search results page, if present
  if (opts.searchReport && (found.searchURL || doc.sceneByName || doc.sceneByFragment)) {
    const sb = doc.sceneByName || doc.sceneByFragment;
    const searchKey = sb && sb.scraper;
    const searchDef = searchKey && doc.xPathScrapers && doc.xPathScrapers[searchKey];
    const bestCand = tested[0] || found.urls[0];
    const probe =
      bestCand && bestCand.probe !== "direct" ? bestCand.probe : opts.probe ? opts.probe[0] : "a";
    const page = opts.paginate ? 2 : bestCand ? bestCand.page : null;
    const searchPageURL = buildProbeURL(sb.queryURL, probe, page);
    if (searchDef) {
      try {
        const html = await fetchHTML(searchPageURL, opts.cookie);
        const dom = new JSDOM(html, { virtualConsole: quietConsole });
        const ctx = { doc: dom.window.document, common: searchDef.common || {} };
        const result = {};
        if (searchDef.scene) {
          result.scene = {};
          for (const [k, v] of Object.entries(searchDef.scene)) {
            result.scene[k] = tryFieldWithDoc(v, ctx);
          }
        }
        entry.searchFields = result;
        entry.searchPageURL = searchPageURL;
        entry.searchProbe = probe;
      } catch (e) {
        entry.searchError = e.message;
      }
    }
  }

  entry.urls = perUrl;
  entry.status = perUrl.some((u) => u.status === "OK") ? "OK" : perUrl[0].status;
  const firstOk = perUrl.find((u) => u.status === "OK");
  if (firstOk) {
    entry.sceneURL = firstOk.url;
    entry.fields = firstOk.fields;
  }
  return entry;
}

function printEntry(e) {
  console.log(`\n=== ${e.file} ===`);
  if (e.probeCount)
    console.log(
      `  probes : ${e.probeCount} (${e.pageCount} page each), ${e.urlCandidates} candidates`,
    );
  if (e.urls && e.urls.length > 1) console.log(`  tested : ${e.urls.length} URLs`);
  if (e.sceneURL) console.log(`  scene  : ${e.sceneURL}`);
  if (e.fields) {
    console.log("  [scene-scraper on detail page]");
    printFields(e.fields);
  }
  if (e.searchFields) {
    console.log("  [search-scraper on search page]");
    printFields(e.searchFields);
  } else if (e.reason) {
    console.log(`  result : ${e.reason}`);
  }
  if (e.searchError) console.log(`  search-error: ${e.searchError}`);
  if (e.urls && e.urls.length > 1) {
    for (const u of e.urls) {
      if (u.status !== "OK") continue;
      const pop = countPopulated(u.fields);
      const tot = countTotal(u.fields);
      console.log(
        `    [${pop}/${tot}] ${u.url}  (probe=${u.probe}${u.page != null ? ` p=${u.page}` : ""})`,
      );
    }
  }
}

function printFields(fields) {
  for (const [field, attrs] of Object.entries(fields)) {
    for (const [k, v] of Object.entries(attrs)) {
      console.log(`    ${field}.${k.padEnd(12)} : ${summarize(v)}`);
    }
  }
}

async function main() {
  const opts = parseArgs(process.argv.slice(2));
  if (opts.help) {
    showHelp();
    return;
  }

  let files;
  if (opts.all) {
    files = listScrapers();
  } else if (opts.files.length > 0) {
    files = opts.files.map((a) => (path.isAbsolute(a) ? a : path.join(ROOT, a)));
  } else {
    showHelp();
    return;
  }

  const summary = [];
  for (const f of files) {
    const mergedOpts = mergeOptions(opts, f);

    const entry = await testScraper(f, mergedOpts);
    summary.push(entry);
    printEntry(entry);
  }

  console.log("\n\n========== SUMMARY ==========");
  for (const e of summary) {
    const populated = e.fields ? countPopulated(e.fields) : 0;
    const total = e.fields ? countTotal(e.fields) : 0;
    const searchPop = e.searchFields ? countPopulated(e.searchFields) : 0;
    const searchTot = e.searchFields ? countTotal(e.searchFields) : 0;
    const extra =
      e.urls && e.urls.length > 1
        ? ` [multi: ${e.urls
            .filter((u) => u.status === "OK")
            .map((u) => countPopulated(u.fields) + "/" + countTotal(u.fields))
            .join(", ")}]`
        : "";
    const searchExtra = e.searchFields ? ` search=${searchPop}/${searchTot}` : "";
    console.log(
      `${e.status.padEnd(12)} ${e.file.padEnd(40)} scene=${populated}/${total}${searchExtra}  candidates=${e.urlCandidates || "-"}  ${e.sceneURL ? e.sceneURL.slice(0, 60) : e.reason || ""}${extra}`,
    );
  }
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});