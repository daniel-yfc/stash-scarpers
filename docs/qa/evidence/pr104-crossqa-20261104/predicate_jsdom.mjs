// CrossQA PR104: evaluate PR #104 gated URLs selector with jsdom (the
// evaluator used by tools/verify-scraper-mappings.mjs and by
// tools/tests/test_bravo_dvd_integration.py eval_xpath).
import fs from "node:fs";
import path from "node:path";
import { JSDOM } from "/home/hatch/workspace/crossqa-pr104/repo/node_modules/jsdom/lib/api.js";

const FIX = "/home/hatch/workspace/crossqa-pr104/repo/tests/fixtures/bravo";
const ADV = "/home/hatch/workspace/crossqa-pr104/output/evidence";
const GATED = "//link[@rel='canonical'][//h2[contains(.,'品番')]]/@href";
const PLAIN = "//link[@rel='canonical']/@href";
const TITLE = "//h2[contains(.,'品番')]/preceding::h2[2]";
const CODE = "//h2[contains(.,'品番')]/following::h2[1]";

const pages = [
  ["fixture", "dvd-synthetic-234.html"], ["fixture", "dvd-synthetic-084.html"],
  ["fixture", "dvd-synthetic-046.html"], ["fixture", "dvd-synthetic-404-00.html"],
  ["fixture", "dvd-synthetic-404-999999.html"], ["fixture", "dvd-synthetic-cloudflare-challenge.html"],
  ["fixture", "dvd-synthetic-logo-empty-alt.html"],
  ["adversarial", "adversarial-fake-marker-777.html"],
  ["adversarial", "adversarial-canonical-only-404.html"],
  ["adversarial", "adversarial-marker-in-p.html"],
  ["adversarial", "adversarial-code-missing.html"],
  ["adversarial", "adversarial-canonical-mismatch.html"],
  ["adversarial", "adversarial-marker-after-canonical-position.html"],
];

function ev(doc, sel) {
  try {
    const r = doc.evaluate(sel, doc, null, doc.defaultView.XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
    const out = [];
    for (let i = 0; i < r.snapshotLength; i++) {
      const n = r.snapshotItem(i);
      out.push((n.nodeValue ?? n.textContent ?? "").trim());
    }
    return out;
  } catch (e) { return ["ERROR: " + e.message]; }
}

for (const [kind, name] of pages) {
  const file = path.join(kind === "fixture" ? FIX : ADV, name);
  const doc = new JSDOM(fs.readFileSync(file, "utf-8")).window.document;
  console.log(`== ${name}`);
  console.log("   URLs_GATED  ", JSON.stringify(ev(doc, GATED)));
  console.log("   URLs_PLAIN  ", JSON.stringify(ev(doc, PLAIN)));
  console.log("   Title       ", JSON.stringify(ev(doc, TITLE)));
  console.log("   Code        ", JSON.stringify(ev(doc, CODE)));
}
