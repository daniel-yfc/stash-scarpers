// JUSTICE finetune regression tests (2026-11-14).
//
// Executes the production selectors/postProcess steps from
// scrapers/JUSTICE.yml against minimal documents whose shapes are taken
// from live pages captured 2026-11-14 (see each test). Offline aid only;
// not a substitute for Stash runtime (Gate B) evidence.
//
// Covered finetune changes:
// 1. Title normalization JUSTICE15(5th) -> "JUSTICE (5th) 15"
// 2. Details truncation at the 特典映像 boilerplate marker
// 3. Performers from Act-prefixed / <strong>-wrapped chapter headings
// 4. Fail-closed behaviour on the Cocoon 404 template
// 5. Slider blank.gif placeholder never emitted as scene Image

import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { test } from "node:test";
import { JSDOM } from "jsdom";
import { parse } from "yaml";

const root = path.resolve(".");
const justice = parse(fs.readFileSync(path.join(root, "scrapers", "JUSTICE.yml"), "utf8"));

function loadDocString(html) {
  return new JSDOM(html).window.document;
}

function resolveSelector(selector, common = {}) {
  let expanded = selector;
  const entries = Object.entries(common).sort((a, b) => b[0].length - a[0].length);
  for (const [rawKey, replacement] of entries) {
    const key = rawKey.startsWith("$") ? rawKey : "$" + rawKey;
    expanded = expanded.replaceAll(key, replacement);
  }
  return expanded;
}

function postProcess(raw, steps = []) {
  let output = raw;
  for (const step of steps || []) {
    if (step.replace) {
      for (const op of step.replace) {
        output = String(output).replace(new RegExp(op.regex, "g"), op.with);
      }
    } else if (typeof step.javascript === "string") {
      const code = "(function () {\n" + step.javascript + "\n})()";
      output = new vm.Script(code).runInNewContext({ value: output }, { timeout: 250 });
    } else {
      throw new Error("Unsupported postProcess step: " + Object.keys(step).join(","));
    }
  }
  return output == null ? "" : String(output);
}

function rawValues(doc, scraperDef, domain, fieldPath) {
  let field = scraperDef[domain];
  for (const part of fieldPath.split(".")) field = field?.[part];
  assert.ok(field !== undefined, `missing field ${fieldPath}`);
  if (typeof field === "object" && field.fixed !== undefined) return [String(field.fixed)];
  const selector = resolveSelector(field.selector, scraperDef.common || {});
  const result = doc.evaluate(
    selector,
    doc,
    null,
    doc.defaultView.XPathResult.ORDERED_NODE_SNAPSHOT_TYPE,
    null,
  );
  return Array.from({ length: result.snapshotLength }, (_, i) => {
    const node = result.snapshotItem(i);
    return (node.nodeValue ?? node.textContent ?? "").trim();
  });
}

function fieldValues(doc, scraperDef, domain, fieldPath) {
  let field = scraperDef[domain];
  for (const part of fieldPath.split(".")) field = field?.[part];
  assert.ok(field !== undefined, `missing field ${fieldPath}`);
  if (typeof field === "object" && field.fixed !== undefined) return [String(field.fixed)];
  const selector = resolveSelector(field.selector, scraperDef.common || {});
  const result = doc.evaluate(
    selector,
    doc,
    null,
    doc.defaultView.XPathResult.ORDERED_NODE_SNAPSHOT_TYPE,
    null,
  );
  const raws = Array.from({ length: result.snapshotLength }, (_, i) => {
    const node = result.snapshotItem(i);
    return (node.nodeValue ?? node.textContent ?? "").trim();
  });
  if (field.concat) {
    // Stash joins the raw values first, then runs postProcess once, then
    // applies split — the same postProcess -> split order as the per-node
    // path below. Until 2026-11-15 no field combined concat with split,
    // so the split stage was never modelled on this branch; Performers.Name
    // now combines them (see scrapers/JUSTICE.yml, 2026-11-15 runtime
    // fix). Details (concat, no split) is unaffected. Empty split pieces
    // are dropped: Stash never surfaces an empty performer name.
    let joined = [postProcess(raws.join(field.concat), field.postProcess)];
    if (field.split) {
      joined = joined.flatMap((v) =>
        v
          .split(field.split)
          .map((p) => postProcess(p, field.postProcess))
          .filter((p) => p !== ""),
      );
    }
    return joined;
  }
  let values = raws.map((r) => postProcess(r, field.postProcess));
  if (field.split) {
    values = values.flatMap((v) =>
      v.split(field.split).map((p) => postProcess(p, field.postProcess)),
    );
  }
  return values;
}

const scene = justice.xPathScrapers.sceneScraper;
const search = justice.xPathScrapers.searchScraper;

function detailDoc({ title, body = "", head = "" }) {
  return loadDocString(
    `<html><head>${head}</head><body><article class="post">` +
      `<h1 class="entry-title">${title}</h1>${body}</article></body></html>`,
  );
}

// ---- 1. Title normalization ---------------------------------------------

test("finetune Title: JUSTICE15(5th) normalizes to 'JUSTICE (5th) 15'", () => {
  const doc = detailDoc({ title: "JUSTICE15(5th)" });
  assert.deepEqual(fieldValues(doc, scene, "scene", "Title"), ["JUSTICE (5th) 15"]);
});

test("finetune Title: non-pattern titles pass through byte-identical", () => {
  for (const t of [
    "JUSTICE16(5th)新発売",
    "PORNO",
    "COMBAT",
    "JUSTICE16&JUSTICEBEST+1再販",
    "GUILTY3rd12購入者特典サイト",
    "JUSTICE公式サイトリニューアル半額フェア！",
  ]) {
    const doc = detailDoc({ title: t });
    assert.deepEqual(fieldValues(doc, scene, "scene", "Title"), [t], t);
  }
});

test("finetune Title: the 22 user acceptance examples (work + BEST grammar, allowlist, controls)", () => {
  const cases = [
    // work titles (2026-11-14, first expansion)
    ["GUILTY3rd14", "GUILTY (3rd) 14"],
    ["GUILTY01(4th)", "GUILTY (4th) 01"],
    ["GUILTY2nd18", "GUILTY (2nd) 18"],
    ["GUILTY18", "GUILTY 18"],
    ["JUSTICE17(5th)", "JUSTICE (5th) 17"],
    ["JUSTICE3rd17", "JUSTICE (3rd) 17"],
    ["JUSTICE4th13", "JUSTICE (4th) 13"],
    ["JUSTICE14", "JUSTICE 14"],
    ["JUSTICE2nd15", "JUSTICE (2nd) 15"],
    // BEST compilations (2026-11-14, second expansion)
    ["JUSTICE3rd BEST2+1", "JUSTICE (3rd) BEST2 +1"],
    ["GUILTY BEST5+1", "GUILTY BEST5 +1"],
    ["JUSTICE3rd BEST+1", "JUSTICE (3rd) BEST +1"],
    ["GUILTY BEST3+1", "GUILTY BEST3 +1"],
    ["JUSTICE2ndBEST5+1", "JUSTICE (2nd) BEST5 +1"],
    ["JUSTICE BEST2+1(4th)", "JUSTICE (4th) BEST2 +1"],
    ["TOKUTENBEST+1", "TOKUTEN BEST +1"],
    ["GUILTY BEST2+1", "GUILTY BEST2 +1"],
    ["JUSTICE2nd BEST2+1", "JUSTICE (2nd) BEST2 +1"],
    ["JUSTICE裏BEST5+1", "JUSTICE裏 BEST5 +1"],
    // control group — not on the series allowlist, byte-identical
    ["PENALTY01", "PENALTY01"],
    ["PORNO002", "PORNO002"],
    ["COMBAT", "COMBAT"],
  ];
  for (const [input, expected] of cases) {
    const doc = detailDoc({ title: input });
    assert.deepEqual(fieldValues(doc, scene, "scene", "Title"), [expected], input);
  }
});

test("finetune Title (search): suffix strip runs before normalization", () => {
  const doc = loadDocString(
    '<html><body><a class="entry-card-wrap" href="https://www.justice01.com/justice155th/">' +
      '<article class="entry-card post-5740"><h2 class="entry-card-title">JUSTICE15(5th)新発売</h2></article></a>' +
      "</body></html>",
  );
  assert.deepEqual(fieldValues(doc, search, "scene", "Title"), ["JUSTICE (5th) 15"]);
});

// ---- 2. Details truncation ----------------------------------------------

test("finetune Details: text ends at the 特典映像 marker", () => {
  const doc = detailDoc({
    title: "JUSTICE15(5th)",
    body:
      '<div class="entry-content"><p>正文そのまま射精！！爆エロ！！満足度MAX！！特典映像『JUSTICE15(5th)EXTRA』収録！！！！</p>' +
      "<p>価格：7,100円　個数：1個</p><p>特典ディスクはなくなり次第終了いたします</p></div>",
  });
  const [details] = fieldValues(doc, scene, "scene", "Details");
  assert.equal(details, "正文そのまま射精！！爆エロ！！満足度MAX！！");
});

test("finetune Details: fallback cuts at 価格 when there is no 特典映像", () => {
  const doc = detailDoc({
    title: "GUILTY14",
    body: '<div class="entry-content"><p>正文テキスト</p><p>価格：8,800円　個数：1個</p><p>特典ディスクはなくなり次第終了いたします</p></div>',
  });
  const [details] = fieldValues(doc, scene, "scene", "Details");
  assert.equal(details, "正文テキスト");
});

test("finetune Details: price block at the very start is kept whole (justice03/porno exception)", () => {
  const doc = detailDoc({
    title: "JUSTICE03",
    body: '<div class="entry-content"><p>価格：7,100円　個数：1個</p><p>特典ディスクはなくなり次第終了いたします</p></div>',
  });
  const [details] = fieldValues(doc, scene, "scene", "Details");
  assert.equal(details, "価格：7,100円　個数：1個\n特典ディスクはなくなり次第終了いたします");
});

test("finetune Details: two-stage is literal — 価格 before 特典映像 is kept, cut still at 特典映像", () => {
  const doc = detailDoc({
    title: "JUSTICE15(5th)",
    body: '<div class="entry-content"><p>価格は税込です。正文そのまま射精！！爆エロ！！満足度MAX！！特典映像『X』収録！！</p><p>価格：7,100円</p></div>',
  });
  const [details] = fieldValues(doc, scene, "scene", "Details");
  assert.equal(details, "価格は税込です。正文そのまま射精！！爆エロ！！満足度MAX！！");
});

test("finetune Details: neither marker means no truncation", () => {
  const doc = detailDoc({
    title: "JUSTICE16(5th)新発売",
    body: '<div class="entry-content"><p>2026年！7月作品！JUSTICE16(5th)！7月17日発売！</p></div>',
  });
  const [details] = fieldValues(doc, scene, "scene", "Details");
  assert.equal(details, "2026年！7月作品！JUSTICE16(5th)！7月17日発売！");
});

// ---- 3. Performers from chapter headings --------------------------------

test("finetune Performers: Act-prefixed headings yield the bracketed names", () => {
  const doc = detailDoc({
    title: "JUSTICE17(5th)",
    body:
      '<h3 class="wp-block-heading">Act1：【REN】</h3>' +
      '<h3 class="wp-block-heading">Act2：【KOUYA】</h3>' +
      '<h3 class="wp-block-heading">【Bonus Track】</h3>',
  });
  assert.deepEqual(fieldValues(doc, scene, "scene", "Performers.Name"), ["REN", "KOUYA"]);
});

test("finetune Performers: <strong>-wrapped heading with pasted prose (justice115th shape)", () => {
  const doc = detailDoc({
    title: "JUSTICE11(5th)",
    body: '<h3 class="wp-block-heading"><strong>Act1：【SUBARU】</strong><p class="MsoNormal">章の説明文テキスト</p></h3>',
  });
  assert.deepEqual(fieldValues(doc, scene, "scene", "Performers.Name"), ["SUBARU"]);
});

test("finetune Performers: bare bracket headings still work (guilty2nd20 shape)", () => {
  const doc = detailDoc({
    title: "GUILTY2nd20",
    body: '<h3 class="wp-block-heading">【ホクト】</h3><h3 class="wp-block-heading">【ジュンタ】</h3>',
  });
  assert.deepEqual(fieldValues(doc, scene, "scene", "Performers.Name"), ["ホクト", "ジュンタ"]);
});

test("finetune Performers: product and bundle headings are not performers (justice4th02 shape)", () => {
  const doc = detailDoc({
    title: "JUSTICE02(4th)",
    body:
      '<h3 class="wp-block-heading">【カズヤ】</h3>' +
      '<h3 class="wp-block-heading">【シュンスケ】</h3>' +
      '<h3 class="wp-block-heading">【JUSTICE02(4th)単品】(A)</h3>' +
      '<h3 class="wp-block-heading">【JUSTICE02(4th)単品】(B)</h3>' +
      '<h3 class="wp-block-heading">【『カズヤ』100パーセット】</h3>',
  });
  assert.deepEqual(fieldValues(doc, scene, "scene", "Performers.Name"), ["カズヤ", "シュンスケ"]);
});

test("finetune Performers: full-width ampersand pair splits into two (justice20 shape)", () => {
  const doc = detailDoc({
    title: "JUSTICE20",
    body: '<h3 class="wp-block-heading">【優馬＆春馬】</h3><h3 class="wp-block-heading">【タケシ】</h3>',
  });
  assert.deepEqual(fieldValues(doc, scene, "scene", "Performers.Name"), ["優馬", "春馬", "タケシ"]);
});

test("finetune Performers: chapter suffix 編 is stripped (justice09 shape)", () => {
  const doc = detailDoc({
    title: "JUSTICE09",
    body:
      '<h3 class="wp-block-heading">【健吾編】</h3>' +
      '<h3 class="wp-block-heading">【コウタ編】</h3>' +
      '<h3 class="wp-block-heading">【マサル編】</h3>',
  });
  assert.deepEqual(fieldValues(doc, scene, "scene", "Performers.Name"), [
    "健吾",
    "コウタ",
    "マサル",
  ]);
});

// ---- 4. 404 template fails closed ----------------------------------------

test("finetune 404: the Cocoon 404 page yields no scene metadata", () => {
  const doc = loadDocString(
    '<html><head><link rel="canonical" href="https://www.justice01.com/404/">' +
      '<meta property="og:url" content="https://www.justice01.com/404/">' +
      '<meta property="og:image" content="https://www.justice01.com/wp-content/themes/cocoon-master/screenshot.jpg"></head>' +
      '<body><article class="post article"><h1 class="entry-title">404 NOT FOUND</h1>' +
      '<figure class="eye-catch"><img data-src="https://www.justice01.com/wp-content/themes/cocoon-master/screenshot.jpg"></figure>' +
      "</article></body></html>",
  );
  assert.deepEqual(fieldValues(doc, scene, "scene", "Title"), []);
  assert.deepEqual(fieldValues(doc, scene, "scene", "URLs"), []);
  assert.deepEqual(fieldValues(doc, scene, "scene", "Image"), []);
  assert.deepEqual(fieldValues(doc, scene, "scene", "Performers.Name"), []);
  assert.deepEqual(fieldValues(doc, scene, "scene", "Groups.Name"), []);
});

// ---- 4b. Announcement posts fail closed -----------------------------------

test("finetune announcement: a 新発売 announcement post yields no scene metadata", () => {
  const doc = loadDocString(
    '<html><head><link rel="canonical" href="https://www.justice01.com/justice165th%e6%96%b0%e7%99%ba%e5%a3%b2/">' +
      '<meta property="og:url" content="https://www.justice01.com/justice165th%e6%96%b0%e7%99%ba%e5%a3%b2/">' +
      '<meta property="og:image" content="https://www.justice01.com/wp-content/themes/cocoon-master/screenshot.jpg"></head>' +
      '<body><article class="post article"><h1 class="entry-title">JUSTICE16(5th)新発売</h1>' +
      '<figure class="eye-catch"><img data-src="https://www.justice01.com/wp-content/themes/cocoon-master/screenshot.jpg"></figure>' +
      '<div class="entry-content"><p>2026年！7月作品！JUSTICE16(5th)！7月17日発売！</p></div>' +
      '<div class="entry-categories"><a class="cat-link" href="https://www.justice01.com/category/whats-new/">新着情報</a></div>' +
      "</article></body></html>",
  );
  assert.deepEqual(fieldValues(doc, scene, "scene", "Title"), []);
  assert.deepEqual(fieldValues(doc, scene, "scene", "URLs"), []);
  assert.deepEqual(fieldValues(doc, scene, "scene", "Image"), []);
  assert.deepEqual(fieldValues(doc, scene, "scene", "Performers.Name"), []);
  assert.deepEqual(fieldValues(doc, scene, "scene", "Groups.Name"), []);
  assert.deepEqual(fieldValues(doc, scene, "scene", "Details"), [""]);
});

test("finetune announcement: a work post is unaffected (series category, bare h1)", () => {
  const doc = detailDoc({
    title: "JUSTICE16(5th)",
    body:
      '<div class="entry-categories"><a class="cat-link" href="https://www.justice01.com/category/gay/">ゲイビデオ・DVD</a>' +
      '<a class="cat-link" href="https://www.justice01.com/category/justice5th/">JUSTICE5th</a></div>',
  });
  assert.deepEqual(fieldValues(doc, scene, "scene", "Title"), ["JUSTICE (5th) 16"]);
  assert.deepEqual(fieldValues(doc, scene, "scene", "Groups.Name"), ["JUSTICE5th"]);
});

// ---- 5. blank.gif placeholder --------------------------------------------

test("finetune Image: blank.gif placeholder is never emitted", () => {
  const doc = detailDoc({
    title: "JUSTICE17(5th)",
    body:
      '<div class="sp-slides">' +
      '<img class="sp-image" src="https://www.justice01.com/wp-content/plugins/ultimate-responsive-image-slider/assets/css/images/blank.gif" data-src="https://www.justice01.com/wp-content/uploads/2026/08/A.jpg">' +
      '<img class="sp-image" src="https://www.justice01.com/wp-content/plugins/ultimate-responsive-image-slider/assets/css/images/blank.gif" data-src="https://www.justice01.com/wp-content/uploads/2026/08/B.jpg">' +
      "</div>",
  });
  const images = fieldValues(doc, scene, "scene", "Image");
  assert.ok(images.length >= 1, "real cover present");
  assert.ok(
    images.every((v) => !v.includes("blank.gif")),
    `no blank.gif in ${JSON.stringify(images)}`,
  );
  assert.equal(images[0], "https://www.justice01.com/wp-content/uploads/2026/08/A.jpg");
});

// ---- 6. Runtime model: multi-node collapse (Gate B GATEB-20261115) -------
//
// Gate B plus the selector-variant diagnosis (lease
// GATEB-JUSTICE-DIAG-20261115) proved the Stash runtime behaviour that
// the harness above does NOT model: for Performers.Name without concat,
// a selector matching several heading nodes delivers only the FIRST
// node's value to postProcess/split — justice115th/155th/175th each
// lost their Act2 performer live ([SUBARU]/[SUBARU]/[REN]) while this
// harness scored them correct. With concat set, the runtime instead
// joins every matched node's value before postProcess (the behaviour
// Details relies on, byte-identical live). The helpers below evaluate a
// field definition under both models; the production fix is pinned by
// showing the frozen pre-fix configuration failing under the runtime
// model and the production configuration passing under it.

const preFixPerformersName = {
  selector:
    "$article//h3[contains(@class,'wp-block-heading')][contains(normalize-space(.), '【')][not(contains(., 'Bonus Track'))][not(contains(normalize-space(.), '【Type'))][not(contains(., '単品'))][not(contains(., 'セット'))]",
  split: "×",
  postProcess: [
    {
      replace: [
        { regex: "^[^【]*【", with: "" },
        { regex: "】.*$", with: "" },
        { regex: "＆", with: "×" },
        { regex: "編$", with: "" },
      ],
    },
    {
      replace: [{ regex: "^\\s+|\\s+$", with: "" }],
    },
  ],
};

function modelFieldValues(doc, field, { collapse }) {
  const selector = resolveSelector(field.selector, scene.common || {});
  const result = doc.evaluate(
    selector,
    doc,
    null,
    doc.defaultView.XPathResult.ORDERED_NODE_SNAPSHOT_TYPE,
    null,
  );
  const raws = Array.from({ length: result.snapshotLength }, (_, i) => {
    const node = result.snapshotItem(i);
    return (node.nodeValue ?? node.textContent ?? "").trim();
  });
  let values;
  if (field.concat) {
    values = [postProcess(raws.join(field.concat), field.postProcess)];
  } else if (collapse) {
    // The proven runtime collapse: only the first node's value survives.
    values = raws.slice(0, 1).map((r) => postProcess(r, field.postProcess));
  } else {
    values = raws.map((r) => postProcess(r, field.postProcess));
  }
  if (field.split) {
    values = values.flatMap((v) =>
      v
        .split(field.split)
        .map((p) => postProcess(p, field.postProcess))
        .filter((p) => p !== ""),
    );
  }
  return values;
}

const prodPerformersName = scene.scene.Performers.Name;

test("runtime model: a single-heading pair page was never broken (justice20 control)", () => {
  const doc = detailDoc({
    title: "JUSTICE20",
    body: '<h3 class="wp-block-heading">【優馬＆春馬】</h3>',
  });
  assert.deepEqual(modelFieldValues(doc, preFixPerformersName, { collapse: true }), [
    "優馬",
    "春馬",
  ]);
  assert.deepEqual(modelFieldValues(doc, prodPerformersName, { collapse: true }), [
    "優馬",
    "春馬",
  ]);
});

test("runtime model: pre-fix loses the Act2 performer, fixed config keeps both (115th shape)", () => {
  const doc = detailDoc({
    title: "JUSTICE11(5th)",
    body:
      '<h3 class="wp-block-heading"><strong>Act1：【SUBARU】</strong><p class="MsoNormal">章の説明文テキスト</p></h3>' +
      '<h3 class="wp-block-heading"><strong>Act2：【YOTA】</strong><p class="MsoNormal">章の説明文テキスト</p></h3>' +
      '<h3 class="wp-block-heading"><strong>【Bonus Track】</strong></h3>',
  });
  assert.deepEqual(modelFieldValues(doc, preFixPerformersName, { collapse: true }), ["SUBARU"]);
  assert.deepEqual(modelFieldValues(doc, preFixPerformersName, { collapse: false }), [
    "SUBARU",
    "YOTA",
  ]);
  assert.deepEqual(modelFieldValues(doc, prodPerformersName, { collapse: true }), [
    "SUBARU",
    "YOTA",
  ]);
  assert.deepEqual(fieldValues(doc, scene, "scene", "Performers.Name"), ["SUBARU", "YOTA"]);
});

test("runtime model: exclusions hold under the fixed config (justice4th02 shape)", () => {
  const doc = detailDoc({
    title: "JUSTICE02(4th)",
    body:
      '<h3 class="wp-block-heading">【カズヤ】</h3>' +
      '<h3 class="wp-block-heading">【シュンスケ】</h3>' +
      '<h3 class="wp-block-heading">【JUSTICE02(4th)単品】(A)</h3>' +
      '<h3 class="wp-block-heading">【JUSTICE02(4th)単品】(B)</h3>' +
      '<h3 class="wp-block-heading">【『カズヤ』100パーセット】</h3>' +
      '<h3 class="wp-block-heading">【Bonus Track】</h3>',
  });
  assert.deepEqual(modelFieldValues(doc, prodPerformersName, { collapse: true }), [
    "カズヤ",
    "シュンスケ",
  ]);
});

// Captured real pages (finetune QA set, outside the repo). These tests
// carry the actual Gate B evidence shapes; they skip where the QA set
// is not present (e.g. CI).
const qaDir = path.resolve(root, "..", "qa-justice-finetune-20261114");
const qaAvailable = fs.existsSync(path.join(qaDir, "pages", "detail-justice115th.html"));
const qaSkip = !qaAvailable && "qa-justice-finetune-20261114 captures not present";

function qaDoc(rel) {
  return new JSDOM(fs.readFileSync(path.join(qaDir, rel), "utf8")).window.document;
}

test(
  "runtime model: captured 115th/155th/175th — pre-fix fails, fixed config passes",
  { skip: qaSkip },
  () => {
    const cases = [
      ["pages/detail-justice115th.html", ["SUBARU"], ["SUBARU", "YOTA"]],
      ["pages/detail-justice155th.html", ["SUBARU"], ["SUBARU", "MITURU"]],
      ["pages/detail-justice175th.html", ["REN"], ["REN", "KOUYA"]],
    ];
    for (const [rel, gateBLive, expected] of cases) {
      const doc = qaDoc(rel);
      // The simulation reproduces the observed Gate B live results for
      // the pre-fix configuration, and the full pair for the fixed one.
      assert.deepEqual(
        modelFieldValues(doc, preFixPerformersName, { collapse: true }),
        gateBLive,
        `${rel} pre-fix runtime`,
      );
      assert.deepEqual(
        modelFieldValues(doc, preFixPerformersName, { collapse: false }),
        expected,
        `${rel} pre-fix offline`,
      );
      assert.deepEqual(
        modelFieldValues(doc, prodPerformersName, { collapse: true }),
        expected,
        `${rel} fixed runtime`,
      );
      assert.deepEqual(
        fieldValues(doc, scene, "scene", "Performers.Name"),
        expected,
        `${rel} fixed offline`,
      );
    }
  },
);

test(
  "runtime fix sweep: fixed config reproduces the pre-fix offline results on every captured page",
  { skip: qaSkip },
  () => {
    const files = [];
    for (const d of ["pages", "pages-gt"]) {
      for (const f of fs.readdirSync(path.join(qaDir, d)).sort()) {
        if (f.endsWith(".html") && !f.startsWith("search-")) files.push(path.join(d, f));
      }
    }
    assert.ok(files.length >= 20, `captured page set present (${files.length})`);
    for (const rel of files) {
      const doc = qaDoc(rel);
      const baseline = modelFieldValues(doc, preFixPerformersName, { collapse: false });
      assert.deepEqual(
        modelFieldValues(doc, prodPerformersName, { collapse: false }),
        baseline,
        `${rel} offline equivalence`,
      );
      assert.deepEqual(
        modelFieldValues(doc, prodPerformersName, { collapse: true }),
        baseline,
        `${rel} runtime equivalence`,
      );
      assert.deepEqual(
        fieldValues(doc, scene, "scene", "Performers.Name"),
        baseline,
        `${rel} harness equivalence`,
      );
    }
  },
);

test("finetune Image: no-image slider plus GIF-only cover yields an honest empty Image", () => {
  const doc = detailDoc({
    title: "JUSTICE03",
    head: '<meta property="og:image" content="https://www.justice01.com/wp-content/uploads/2024/08/jus3.gif">',
    body:
      '<div class="sp-slides">' +
      '<img class="sp-image" src="https://www.justice01.com/wp-content/plugins/ultimate-responsive-image-slider/assets/css/images/blank.gif" data-src="https://www.justice01.com/wp-content/uploads/2024/08/no-image.jpg">' +
      "</div>",
  });
  assert.deepEqual(fieldValues(doc, scene, "scene", "Image"), []);
});
