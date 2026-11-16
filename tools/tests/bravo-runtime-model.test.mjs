// BRAVO_JAPAN runtime-model simulation (Gate B GATEB-BRAVO-FINETUNE-20261115).
//
// Why this file exists: the finetune candidate at 817303b scored perfectly
// in the jsdom harness and in the fixture manifests, yet failed on every
// DVD page in the real Stash runtime — Title returned four segments
// ("体育会DASH! 4 - GO to BRAVO-CLIPS - ヌル穴大学生 - BRAVO-JAPAN") and
// Code a single wrong digit ("BR-1" / "BR-2"). The divergence is in the
// XPath engine, not the page: jsdom implements the spec, the runtime uses
// antchfx/htmlquery, whose axis implementation (antchfx/xpath query.go,
// read at v1.3.9 / htmlquery v1.3.7 and cross-checked with a Go oracle
// harness against these same captures) applies a positional predicate on
// a preceding/following axis STEP per batch of its axis walk instead of
// per axis result set:
//
//   - preceding::h2[n]: the walk climbs ancestor levels; at each level
//     the preceding siblings (nearest first, each subtree in document
//     order) form one batch, the position counts within the batch, and
//     the count resets at the next level. The unfiltered [2]/[1] thus
//     matched the title lines (product-block batch) AND the chrome lines
//     BRAVO-JAPAN / GO to BRAVO-CLIPS (header batch).
//   - following::h2[n]: the position counts within each following
//     sibling subtree and resets per subtree, so following::h2[1]
//     matched EVERY following h2 (17 on dvds/198) and the Code JS —
//     whose digits variable is overwritten by each digits-only part —
//     ended on the last digits-only h2, the 枚数 disc count.
//   - A parenthesized path (//…/following::h2)[n] applies the position
//     to the whole axis result in document order in BOTH engines.
//
// The helpers below evaluate a field definition under that model. The
// pre-fix configuration is frozen here; its postProcess JS is shared
// with production (the fix is selector-only — the JS has not changed
// since 817303b). Certification contract: the model MUST reproduce the
// observed Gate B live values for the pre-fix configuration exactly. If
// it ever stops doing so, the model is wrong, this file fails, and the
// production fix is NOT certified offline — do not weaken the live-value
// assertions to make it pass.

import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { test } from "node:test";
import { JSDOM } from "jsdom";
import { parse } from "yaml";

const root = path.resolve(".");
const scraper = parse(
  fs.readFileSync(path.join(root, "scrapers/BRAVO_JAPAN.yml"), "utf8"),
);
const dvdScene = scraper.xPathScrapers.dvdSceneScraper.scene;
const clipScene = scraper.xPathScrapers.clipSceneScraper.scene;

const runJs = (script, value) => new Function("value", script)(value);

function fieldJs(field) {
  const step = (field.postProcess || []).find((s) => typeof s.javascript === "string");
  assert.ok(step, "field must have a javascript postProcess step");
  return step.javascript;
}

// ---- Frozen pre-fix configuration (817303b, the Gate B candidate) --------

const MARKER = "//h2[contains(.,'品番')]";
const preFixTitleSelector = `${MARKER}/preceding::h2[2] | ${MARKER}/preceding::h2[1]`;
const preFixCodeSelector = `${MARKER}/following::h2[1] | ${MARKER}/following::h2[2][contains(.,'-')]`;

const fixedTitleSelector = `${MARKER}/preceding::h2[not(contains(.,'BRAVO-JAPAN') or contains(.,'BRAVO-CLIPS'))][2] | ${MARKER}/preceding::h2[not(contains(.,'BRAVO-JAPAN') or contains(.,'BRAVO-CLIPS'))][1]`;
const fixedCodeSelector = `(${MARKER}/following::h2)[1] | (${MARKER}/following::h2)[2][contains(.,'-')]`;

const clipTitleSelector = "//h1[1]";
const clipCodeSelector = "//h2[normalize-space()='Clip']/preceding::h2[1]";

test("production DVD Title/Code selectors are the runtime-fixed forms; clips untouched", () => {
  assert.equal(dvdScene.Title.selector, fixedTitleSelector);
  assert.equal(dvdScene.Code.selector, fixedCodeSelector);
  assert.equal(dvdScene.Title.concat, "\n");
  assert.equal(dvdScene.Code.concat, "\n");
  assert.equal(clipScene.Title.selector, clipTitleSelector);
  assert.equal(clipScene.Code.selector, clipCodeSelector);
});

// ---- antchfx axis model ---------------------------------------------------
//
// A branch is parsed into { axis, whole, predicates } where predicates is
// an ordered list applied per batch (step form) or once over the whole
// axis result (parenthesized form):
//   { pos: n }                    positional predicate [n]
//   { contains: "X" }             [contains(.,'X')]
//   { notContainsAny: ["A","B"] } [not(contains(.,'A') or contains(.,'B'))]

function parsePredicates(text) {
  const preds = [];
  const re = /\[([^\]]*)\]/g;
  let m;
  while ((m = re.exec(text)) !== null) {
    const body = m[1];
    if (/^\d+$/.test(body)) {
      preds.push({ pos: Number(body) });
    } else if (/^contains\(\.,'[^']*'\)$/.test(body)) {
      preds.push({ contains: body.match(/'([^']*)'/)[1] });
    } else if (/^not\(contains\(\.,'[^']*'\) or contains\(\.,'[^']*'\)\)$/.test(body)) {
      preds.push({ notContainsAny: [...body.matchAll(/'([^']*)'/g)].map((x) => x[1]) });
    } else {
      throw new Error(`unsupported predicate in model: [${body}]`);
    }
  }
  return preds;
}

function parseBranch(branch) {
  const whole = branch.match(/^\((.*)\)((?:\[[^\]]*\])*)$/);
  if (whole) {
    const inner = whole[1];
    const axis = inner.includes("/preceding::h2")
      ? "preceding"
      : inner.includes("/following::h2")
        ? "following"
        : null;
    assert.ok(axis, `model: unrecognized whole-set branch ${branch}`);
    return { axis, whole: true, predicates: parsePredicates(whole[2]) };
  }
  const step = branch.match(/^(.*)\/(preceding|following)::h2((?:\[[^\]]*\])*)$/);
  assert.ok(step, `model: unrecognized step branch ${branch}`);
  return { axis: step[2], whole: false, predicates: parsePredicates(step[3]) };
}

function h2sInSubtree(node) {
  const out = [];
  const walk = (n) => {
    if (n.nodeType === 1 && n.tagName === "H2") out.push(n);
    for (const c of n.childNodes) walk(c);
  };
  walk(node);
  return out;
}

// preceding axis batches: one batch per ancestor level; within a level,
// preceding siblings nearest-first, each subtree in document order.
function precedingBatches(ctx) {
  const batches = [];
  let node = ctx;
  while (node.parentNode) {
    const seq = [];
    for (let s = node.previousSibling; s; s = s.previousSibling) {
      seq.push(...h2sInSubtree(s));
    }
    batches.push(seq);
    node = node.parentNode;
  }
  return batches;
}

// following axis batches: one batch per following sibling subtree,
// in document order across ancestor levels.
function followingBatches(ctx) {
  const batches = [];
  let node = ctx;
  while (node.parentNode) {
    for (let s = node.nextSibling; s; s = s.nextSibling) {
      batches.push(h2sInSubtree(s));
    }
    node = node.parentNode;
  }
  return batches;
}

function applyPredicates(nodes, predicates) {
  let seq = nodes;
  for (const p of predicates) {
    if (p.pos !== undefined) {
      seq = seq.length >= p.pos ? [seq[p.pos - 1]] : [];
    } else if (p.contains !== undefined) {
      seq = seq.filter((h) => h.textContent.includes(p.contains));
    } else if (p.notContainsAny !== undefined) {
      seq = seq.filter((h) => !p.notContainsAny.some((s) => h.textContent.includes(s)));
    }
  }
  return seq;
}

function modelBranch(ctx, branch) {
  const batches = branch.axis === "preceding" ? precedingBatches(ctx) : followingBatches(ctx);
  if (branch.whole) {
    return applyPredicates(batches.flat(), branch.predicates);
  }
  return batches.flatMap((batch) => applyPredicates(batch, branch.predicates));
}

// Evaluate a Title/Code-style field (selector union + concat + JS) under
// the antchfx model: branches in selector order, each branch's nodes in
// walk order, concatenated with the field's concat string, then the JS.
function modelFieldValue(doc, selector, concat, js) {
  const markerResult = doc.evaluate(
    MARKER,
    doc,
    null,
    doc.defaultView.XPathResult.ORDERED_NODE_SNAPSHOT_TYPE,
    null,
  );
  assert.equal(markerResult.snapshotLength, 1, "exactly one 品番 marker h2");
  const ctx = markerResult.snapshotItem(0);
  const texts = [];
  for (const rawBranch of selector.split(" | ")) {
    const branch = parseBranch(rawBranch);
    for (const node of modelBranch(ctx, branch)) texts.push(node.textContent ?? "");
  }
  return runJs(js, texts.join(concat));
}

function applyPostProcess(field, raw) {
  let value = raw;
  for (const step of field.postProcess || []) {
    if (typeof step.javascript === "string") {
      value = runJs(step.javascript, value);
    } else if (step.replace) {
      for (const op of step.replace) {
        value = String(value).replace(new RegExp(op.regex, "g"), op.with);
      }
    }
  }
  return value == null ? "" : String(value);
}

// Spec-engine evaluation (what the jsdom harness sees).
function specFieldValue(doc, field) {
  const result = doc.evaluate(
    field.selector,
    doc,
    null,
    doc.defaultView.XPathResult.ORDERED_NODE_SNAPSHOT_TYPE,
    null,
  );
  const texts = Array.from({ length: result.snapshotLength }, (_, i) => {
    const node = result.snapshotItem(i);
    return node.nodeValue ?? node.textContent ?? "";
  });
  const raw = field.concat ? texts.join(field.concat) : (texts[0] ?? "");
  return applyPostProcess(field, raw);
}

// ---- Captured pages --------------------------------------------------------

const qaDir = path.resolve(root, "..", "qa-bravo-title-20261114");
const qaAvailable = fs.existsSync(path.join(qaDir, "pages", "dvds-198.html"));
const qaSkip = !qaAvailable && "qa-bravo-title-20261114 captures not present";

function qaDoc(rel) {
  return new JSDOM(fs.readFileSync(path.join(qaDir, rel), "utf8")).window.document;
}

// Expected values are the user ground truth / finetune contract; the
// live values are the Gate B GATEB-BRAVO-FINETUNE-20261115 observations
// for the pre-fix candidate, quoted verbatim from its report.
const DVD_CASES = [
  {
    file: "pages/dvds-046.html",
    title: "ゆるゆる雄太のデブ竿ぽちゃ穴食べ放題!",
    code: "BR-046",
    liveTitle: "ゆるゆる雄太のデブ竿ぽちゃ穴食べ放題! - GO to BRAVO-CLIPS - BRAVO-JAPAN",
    liveCode: "BR-2",
  },
  {
    file: "pages/dvds-084.html",
    title: "少年集団強姦",
    code: "BR-084",
    liveTitle: "少年集団強姦 - GO to BRAVO-CLIPS - BRAVO-JAPAN",
    liveCode: "BR-1",
  },
  {
    file: "pages/dvds-198.html",
    title: "体育会DASH! 4 - ヌル穴大学生",
    code: "BR-198",
    liveTitle: "体育会DASH! 4 - GO to BRAVO-CLIPS - ヌル穴大学生 - BRAVO-JAPAN",
    liveCode: "BR-1",
  },
  {
    file: "pages/dvds-234.html",
    title: "勃起する白き花よ - Mr.Lily 編",
    code: "BR-234",
    liveTitle: "勃起する白き花よ - GO to BRAVO-CLIPS - Mr.Lily 編 - BRAVO-JAPAN",
    liveCode: "BR-1",
  },
  {
    file: "pages/dvds-281.html",
    title: "熊ケツ4 - しゅうた参上！",
    code: "BR-281",
    liveTitle: "熊ケツ4 - GO to BRAVO-CLIPS - しゅうた参上！ - BRAVO-JAPAN",
    liveCode: "BR-1",
  },
  {
    file: "pages/dvds-377.html",
    title: "騒乱みだれ穴５",
    code: "BR-377",
    liveTitle: "騒乱みだれ穴５ - GO to BRAVO-CLIPS - BRAVO-JAPAN",
    liveCode: "BR-1",
  },
  {
    file: "pages/dvds-384.html",
    title: "ナマ狂い種壺待機５",
    code: "BR-384",
    liveTitle: "ナマ狂い種壺待機５ - GO to BRAVO-CLIPS - BRAVO-JAPAN",
    liveCode: "BR-1",
  },
];

test(
  "runtime model: pre-fix configuration reproduces the Gate B live failures exactly",
  { skip: qaSkip },
  () => {
    const titleJs = fieldJs(dvdScene.Title);
    const codeJs = fieldJs(dvdScene.Code);
    for (const c of DVD_CASES) {
      const doc = qaDoc(c.file);
      assert.equal(
        modelFieldValue(doc, preFixTitleSelector, "\n", titleJs),
        c.liveTitle,
        `${c.file} pre-fix Title under runtime model`,
      );
      assert.equal(
        modelFieldValue(doc, preFixCodeSelector, "\n", codeJs),
        c.liveCode,
        `${c.file} pre-fix Code under runtime model`,
      );
    }
  },
);

test(
  "spec engine: pre-fix configuration looks correct offline (the harness/runtime divergence)",
  { skip: qaSkip },
  () => {
    for (const c of DVD_CASES) {
      const doc = qaDoc(c.file);
      assert.equal(
        specFieldValue(doc, { selector: preFixTitleSelector, concat: "\n", postProcess: dvdScene.Title.postProcess }),
        c.title,
        `${c.file} pre-fix Title under spec engine`,
      );
      assert.equal(
        specFieldValue(doc, { selector: preFixCodeSelector, concat: "\n", postProcess: dvdScene.Code.postProcess }),
        c.code,
        `${c.file} pre-fix Code under spec engine`,
      );
    }
  },
);

test(
  "runtime model + spec engine: production configuration is correct on every captured DVD page",
  { skip: qaSkip },
  () => {
    const titleJs = fieldJs(dvdScene.Title);
    const codeJs = fieldJs(dvdScene.Code);
    for (const c of DVD_CASES) {
      const doc = qaDoc(c.file);
      assert.equal(
        modelFieldValue(doc, dvdScene.Title.selector, dvdScene.Title.concat, titleJs),
        c.title,
        `${c.file} production Title under runtime model`,
      );
      assert.equal(
        modelFieldValue(doc, dvdScene.Code.selector, dvdScene.Code.concat, codeJs),
        c.code,
        `${c.file} production Code under runtime model`,
      );
      assert.equal(specFieldValue(doc, dvdScene.Title), c.title, `${c.file} production Title under spec engine`);
      assert.equal(specFieldValue(doc, dvdScene.Code), c.code, `${c.file} production Code under spec engine`);
    }
  },
);

test(
  "clips pages: production configuration unchanged and correct (spec engine)",
  { skip: qaSkip },
  () => {
    const cases = [
      ["pages/clips-282.html", "初撮影ヤマト５Ｐ", "282"],
      ["pages/clips-283.html", "ハルキリーマン交尾", "283"],
      ["pages/clips-284.html", "デカマラ同士 目隠し交尾", "284"],
    ];
    for (const [file, title, code] of cases) {
      const doc = qaDoc(file);
      assert.equal(specFieldValue(doc, clipScene.Title), title, `${file} clip Title`);
      assert.equal(specFieldValue(doc, clipScene.Code), code, `${file} clip Code`);
    }
  },
);
