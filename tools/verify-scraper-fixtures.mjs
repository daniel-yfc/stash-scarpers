import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { JSDOM } from 'jsdom';
import { parse } from 'yaml';

const FAILURE_MARKERS = [
  'cf-challenge',
  'Just a moment',
  'Attention Required',
  'age-verification',
  'Application error',
  '404 Not Found',
];

function evaluate(html, expression) {
  const dom = new JSDOM(html);
  const result = dom.window.document.evaluate(
    expression,
    dom.window.document,
    null,
    dom.window.XPathResult.ORDERED_NODE_SNAPSHOT_TYPE,
    null,
  );
  return result.snapshotLength;
}

function classify(html, expected) {
  const marker = FAILURE_MARKERS.find((item) => html.includes(item));
  if (expected === 'completed' && marker) {
    throw new Error(`completed fixture contains failure marker: ${marker}`);
  }
  if (expected === 'failure' && !marker) {
    throw new Error('failure fixture did not contain a known failure marker');
  }
}

function assertCase(item, html) {
  classify(html, item.classification);
  if (item.classification !== 'completed') return;
  const lang = item.locale?.lang;
  if (lang && !html.includes(`lang="${lang}"`) && !html.includes(`lang='${lang}'`)) {
    throw new Error(`${item.name}: locale lang ${lang} missing`);
  }
  if (item.locale?.text && !html.includes(item.locale.text)) {
    throw new Error(`${item.name}: expected source-language text missing`);
  }
  for (const assertion of item.expect || []) {
    const count = evaluate(html, assertion.xpath);
    if (count < assertion.min || count > assertion.max) {
      throw new Error(`${item.name}: ${assertion.xpath} matched ${count}`);
    }
  }
  if (item.optionalField) {
    const count = evaluate(html, item.optionalField.xpath);
    if (count !== item.optionalField.expectedCount) {
      throw new Error(`${item.name}: optional field matched ${count}`);
    }
  }
}

function checkManifest(file) {
  const manifest = parse(fs.readFileSync(file, 'utf8'));
  const cases = manifest.cases || [];
  if (!cases.some((item) => item.classification === 'failure')) {
    throw new Error(`${file}: missing failure-page classification case`);
  }
  if (!cases.some((item) => item.optionalField)) {
    throw new Error(`${file}: missing optional-field case`);
  }
  const base = path.dirname(file);
  for (const item of cases) {
    assertCase(item, fs.readFileSync(path.join(base, item.html), 'utf8'));
  }
}

function selfTest() {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'fixture-self-test-'));
  fs.writeFileSync(path.join(root, 'good.html'), '<html lang="zh-TW"><title>Example</title><a rel="canonical" href="/zh-TW/videos/x"></a></html>');
  fs.writeFileSync(path.join(root, 'optional.html'), '<html lang="zh-TW"><title>Example</title></html>');
  fs.writeFileSync(path.join(root, 'bad.html'), '<html><title>Just a moment</title></html>');
  const manifest = path.join(root, 'self-test-fixtures.yml');
  fs.writeFileSync(manifest, `cases:
  - name: good
    html: good.html
    classification: completed
    locale:
      lang: zh-TW
      text: Example
    expect:
      - xpath: //title
        min: 1
        max: 1
  - name: optional
    html: optional.html
    classification: completed
    locale:
      lang: zh-TW
      text: Example
    optionalField:
      xpath: //a[contains(@href,'twitter.com')]
      expectedCount: 0
    expect:
      - xpath: //title
        min: 1
        max: 1
  - name: bad
    html: bad.html
    classification: failure
`);
  checkManifest(manifest);
  console.log('Fixture runner self-test passed');
}

const args = process.argv.slice(2);
if (args.includes('--self-test')) {
  selfTest();
} else if (args.length === 0) {
  console.log('No fixture manifest supplied; site fixture verification is not established');
} else {
  for (const file of args) checkManifest(file);
  console.log(`Verified ${args.length} fixture manifest(s)`);
}
