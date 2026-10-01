import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { JSDOM } from 'jsdom';
import { parse } from 'yaml';

const FAILURE_MARKERS = [
  'cf-challenge', 'Just a moment', 'Attention Required',
  'age-verification', 'Application error', '404 Not Found',
];

function fail(message) { throw new Error(message); }

function matches(document, xpath) {
  const result = document.evaluate(
    xpath, document, null, document.defaultView.XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null,
  );
  return Array.from({ length: result.snapshotLength }, (_, i) => result.snapshotItem(i));
}

function value(node) { return node.nodeValue ?? node.textContent ?? ''; }

function assertCase(item, html) {
  const dom = new JSDOM(html);
  const document = dom.window.document;
  const marker = FAILURE_MARKERS.find((text) => html.includes(text));
  if (item.classification === 'failure') {
    if (!marker) fail(`${item.name}: expected failure marker absent`);
    return;
  }
  if (item.classification !== 'completed') fail(`${item.name}: invalid classification`);
  if (marker) fail(`${item.name}: completed page contains failure marker`);
  if (!item.locale?.lang || !item.locale?.canonicalLocale || !item.locale?.text) {
    fail(`${item.name}: lang, canonicalLocale and text are required`);
  }
  if (document.documentElement.getAttribute('lang') !== item.locale.lang) {
    fail(`${item.name}: html lang mismatch`);
  }
  const canonical = document.querySelector('link[rel="canonical"]')?.getAttribute('href');
  if (!canonical) fail(`${item.name}: canonical link absent`);
  const pathname = new URL(canonical, 'https://fixture.invalid').pathname;
  if (!pathname.split('/').includes(item.locale.canonicalLocale)) {
    fail(`${item.name}: canonical locale mismatch`);
  }
  if (!document.documentElement.textContent.includes(item.locale.text)) {
    fail(`${item.name}: source-language text mismatch`);
  }
  if (!Array.isArray(item.expect) || !item.expect.length) fail(`${item.name}: XPath assertions required`);
  for (const assertion of item.expect) {
    if (!assertion.xpath || !Number.isInteger(assertion.min) || !Number.isInteger(assertion.max)
        || assertion.min < 0 || assertion.max < assertion.min) fail(`${item.name}: invalid XPath bounds`);
    const nodes = matches(document, assertion.xpath);
    if (nodes.length < assertion.min || nodes.length > assertion.max) {
      fail(`${item.name}: ${assertion.xpath} matched ${nodes.length}`);
    }
    if (assertion.values && JSON.stringify(nodes.map(value)) !== JSON.stringify(assertion.values)) {
      fail(`${item.name}: representative values mismatch`);
    }
  }
  if (item.optionalField) {
    if (!item.optionalField.xpath || item.optionalField.expectedCount !== 0) {
      fail(`${item.name}: optional case must assert zero matches`);
    }
    if (matches(document, item.optionalField.xpath).length !== 0) {
      fail(`${item.name}: optional field unexpectedly present`);
    }
  }
}

function checkManifest(file) {
  const manifest = parse(fs.readFileSync(file, 'utf8'));
  const cases = manifest?.cases;
  if (!Array.isArray(cases) || !cases.some((c) => c.classification === 'completed')
      || !cases.some((c) => c.classification === 'failure')
      || !cases.some((c) => c.optionalField)) fail(`${file}: completed, failure and optional cases required`);
  const root = path.dirname(path.resolve(file));
  for (const item of cases) {
    if (!item.name || typeof item.html !== 'string') fail(`${file}: case name and html required`);
    const fixture = path.resolve(root, item.html);
    if (!fixture.startsWith(root + path.sep)) fail(`${item.name}: fixture path leaves manifest directory`);
    assertCase(item, fs.readFileSync(fixture, 'utf8'));
  }
  return cases.length;
}

function selfTest() {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'fixture-contract-'));
  try {
    const good = '<html lang="zh-TW"><head><link rel="canonical" href="https://example.invalid/zh-TW/videos/x"></head><body><h1>範例</h1></body></html>';
    const base = {
      name: 'valid', classification: 'completed',
      locale: { lang: 'zh-TW', canonicalLocale: 'zh-TW', text: '範例' },
      expect: [{ xpath: '//h1/text()', min: 1, max: 1, values: ['範例'] }],
      optionalField: { xpath: '//a[@rel="social"]', expectedCount: 0 },
    };
    assertCase(base, good);
    const rejected = [
      [base, good.replace('範例', 'Just a moment')],
      [base, good.replace('lang="zh-TW"', 'lang="en-US"')],
      [base, good.replace('/zh-TW/videos/', '/en-US/videos/')],
      [{ ...base, expect: [{ xpath: '//h1', min: 2, max: 2 }] }, good],
      [{ ...base, expect: [{ xpath: '//h1/text()', min: 1, max: 1, values: ['wrong'] }] }, good],
      [{ ...base, optionalField: { xpath: '//h1', expectedCount: 0 } }, good],
    ];
    for (const [testCase, html] of rejected) {
      let failed = false;
      try { assertCase(testCase, html); } catch { failed = true; }
      if (!failed) fail('self-test did not reject invalid fixture');
    }
    assertCase({ name: 'expected failure', classification: 'failure' }, '<title>Just a moment</title>');
    console.log('Fixture contract self-test: positive and 6 negative cases passed');
  } finally { fs.rmSync(root, { recursive: true, force: true }); }
}

const args = process.argv.slice(2);
if (args.length === 1 && args[0] === '--self-test') selfTest();
else if (!args.length) console.log('SITE FIXTURE VERIFICATION: UNVERIFIED (no manifests supplied)');
else {
  for (const file of args) console.log(`${file}: ${checkManifest(file)} cases verified`);
}
