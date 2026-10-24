import { JSDOM, VirtualConsole } from "jsdom";

const XP_ALL = 7;
const quietConsole = new VirtualConsole();
quietConsole.on("jsdomError", () => {});

function normalizeURL(raw, baseURL) {
  try {
    const url = new URL(String(raw).trim(), baseURL);
    return url.protocol === "http:" || url.protocol === "https:" ? url.toString() : null;
  } catch {
    return null;
  }
}

function applySupportedReplacements(value, mapping) {
  let output = value;
  if (!mapping || typeof mapping !== "object") return output;
  for (const operation of mapping.postProcess || []) {
    for (const replacement of operation.replace || []) {
      output = output.replace(new RegExp(replacement.regex, "g"), replacement.with);
    }
  }
  // Intentionally do not claim to emulate the Stash JavaScript post-processor.
  return output;
}

function scenePatterns(scraperDoc) {
  return (scraperDoc.sceneByURL || [])
    .flatMap((mapping) => Array.isArray(mapping.url) ? mapping.url : [mapping.url])
    .filter((p) => typeof p === "string" && p.length > 0)
    .map((p) => p.replace(/^https?:\/\//i, "").replace(/^www\./i, ""));
}

export function extractSceneURLs(searchHTML, scraperDoc, baseURL, probe, page) {
  const dom = new JSDOM(searchHTML, { virtualConsole: quietConsole });
  const document = dom.window.document;
  const search = scraperDoc.sceneByName || scraperDoc.sceneByFragment || {};
  const definition = (scraperDoc.xPathScrapers || {})[search.scraper];
  const mappings = [definition?.scene?.URL, definition?.scene?.URLs].filter(Boolean);
  const candidates = [];

  for (const mapping of mappings) {
    let selector = typeof mapping === "string" ? mapping : mapping.selector;
    if (typeof selector !== "string") continue;
    for (const [key, value] of Object.entries(definition.common || {})) {
      selector = selector.replaceAll(key.startsWith("$") ? key : "$" + key, value);
    }
    try {
      const result = document.evaluate(selector, document, null, XP_ALL, null);
      for (let i = 0; i < result.snapshotLength; i++) {
        const node = result.snapshotItem(i);
        const text = (node.nodeValue || node.textContent || "").trim();
        if (!text) continue;
        const normalized = normalizeURL(applySupportedReplacements(text, mapping), baseURL);
        if (normalized) candidates.push(normalized);
      }
    } catch {
      // A malformed selector is not proof that a website has no valid scene links.
      // The fallback below uses sceneByURL route patterns.
    }
  }

  if (!candidates.length) {
    const patterns = scenePatterns(scraperDoc);
    const anchors = document.querySelectorAll("a[href]");
    for (const anchor of anchors) {
      const normalized = normalizeURL(anchor.getAttribute("href"), baseURL);
      if (!normalized) continue;
      const url = new URL(normalized);
      const target = url.host.replace(/^www\./i, "") + url.pathname + url.search;
      if (patterns.some((pattern) => target.startsWith(pattern))) candidates.push(normalized);
    }
  }

  return [...new Set(candidates)].map((url) => ({ url, probe, page }));
}

export function classifyScrapedFields(fields) {
  const selectors = [];
  function visit(node) {
    if (!node || typeof node !== "object") return;
    if (node.selector && typeof node.selector === "object" &&
        Number.isInteger(node.selector.count)) {
      selectors.push(node.selector);
    }
    for (const [key, child] of Object.entries(node)) {
      if (key !== "selector" && key !== "postProcess") visit(child);
    }
  }
  visit(fields);
  const matched = selectors.filter((s) => s.count > 0).length;
  const errors = selectors.filter((s) => s.error).length;
  let status;
  if (errors) status = "SELECTOR_ERROR";
  else if (!selectors.length) status = "NO_SELECTORS";
  else if (!matched) status = "NO_FIELDS_MATCHED";
  else status = "SELECTOR_MATCHED";
  return { status, matched, total: selectors.length, postProcessExecuted: false };
}
