import vm from "node:vm";

function fail(message) {
  throw new Error(message);
}

function getField(scraper, assertion) {
  const entrypoint = assertion.entrypoint || "sceneByURL";
  const route = scraper[entrypoint];
  if (!route) fail("Unsupported or missing entrypoint: " + entrypoint);
  const routes = Array.isArray(route) ? route : [route];
  const chosen = assertion.scraper
    ? routes.find((candidate) => candidate.scraper === assertion.scraper)
    : routes.length === 1 ? routes[0] : null;
  if (!chosen) fail("Ambiguous entrypoint; specify scraper for " + entrypoint);
  if (chosen.action !== "scrapeXPath") fail("Only scrapeXPath mappings are supported");
  const definition = scraper.xPathScrapers?.[chosen.scraper];
  if (!definition) fail("Missing xPathScraper " + chosen.scraper);
  const fieldPath = assertion.field?.split(".");
  if (!fieldPath?.length) fail("A mapped field path is required");
  let field = definition.scene;
  for (const component of fieldPath) {
    field = field?.[component];
  }
  if (field === undefined) fail("Missing production YAML field " + assertion.field);
  return { field, common: definition.common || {} };
}

function resolveSelector(selector, common) {
  if (typeof selector !== "string") fail("Missing selector string");
  let expanded = selector;
  const entries = Object.entries(common).sort((a, b) => b[0].length - a[0].length);
  for (const [rawKey, replacement] of entries) {
    if (typeof replacement !== "string") fail("Unsupported non-string common selector");
    const key = rawKey.startsWith("$") ? rawKey : "$" + rawKey;
    expanded = expanded.replaceAll(key, replacement);
  }
  if (/\$[a-zA-Z_][a-zA-Z0-9_]*/.test(expanded)) {
    fail("Unresolved common selector: " + expanded);
  }
  return expanded;
}

function postProcessValue(value, steps) {
  let output = value;
  for (const step of steps || []) {
    if (step.replace) {
      for (const operation of step.replace) {
        output = String(output).replace(new RegExp(operation.regex, "g"), operation.with);
      }
    } else if (typeof step.javascript === "string") {
      // Execute committed YAML transformation with a short timeout.
      // This is a regression aid, not a substitute for an actual Stash runtime.
      const code = "(function () {\n" + step.javascript + "\n})()";
      output = new vm.Script(code).runInNewContext({ value: output }, { timeout: 250 });
    } else {
      fail("Unsupported postProcess operation: " + Object.keys(step).join(","));
    }
  }
  return output == null ? "" : String(output);
}

function extractValues(document, mapping, common) {
  if (typeof mapping === "object" && mapping !== null && mapping.fixed !== undefined) {
    return [String(mapping.fixed)];
  }
  const selector = typeof mapping === "string" ? mapping : mapping?.selector;
  const expanded = resolveSelector(selector, common);
  let result;
  try {
    result = document.evaluate(
      expanded, document, null,
      document.defaultView.XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null,
    );
  } catch (error) {
    fail("Invalid production YAML XPath: " + error.message);
  }
  return Array.from({ length: result.snapshotLength }, (_, i) => {
    const node = result.snapshotItem(i);
    const raw = (node.nodeValue ?? node.textContent ?? "").trim();
    return postProcessValue(raw, typeof mapping === "object" ? mapping.postProcess : undefined);
  });
}

export function assertMappedCase(item, document, scraper) {
  if (item.mappedExpect === undefined) return;
  if (!Array.isArray(item.mappedExpect) || !item.mappedExpect.length) {
    fail(item.name + ": mappedExpect must have assertions");
  }
  for (const assertion of item.mappedExpect) {
    if (typeof assertion.field !== "string" || !Array.isArray(assertion.values)) {
      fail(item.name + ": mappedExpect requires field and expected values");
    }
    const { field, common } = getField(scraper, assertion);
    const actual = extractValues(document, field, common);
    if (JSON.stringify(actual) !== JSON.stringify(assertion.values)) {
      fail(
        item.name + ": production YAML field " + assertion.field +
        " expected " + JSON.stringify(assertion.values) +
        " but got " + JSON.stringify(actual),
      );
    }
  }
}
