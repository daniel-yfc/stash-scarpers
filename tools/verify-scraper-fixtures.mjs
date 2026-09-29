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

function checkManifest(file) {
  const manifest = parse(fs.readFileSync(file, 'utf8'));
  const base = path.dirname(file);
  for (const item of manifest.cases || []) {
    const html = fs.readFileSync(path.join(base, item.html), 'utf8');
    classify(html, item.classification);
    if (item.classification !== 'completed') continue;
    for (const assertion of item.expect || []) {
      const count = evaluate(html, assertion.xpath);
      if (count < assertion.min || count > assertion.max) {
        throw new Error(`${item.name}: ${assertion.xpath} matched ${count}`);
      }
    }
  }
}

function selfTest() {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'fixture-self-test-'));
  const good = path.join(root, 'good.html');
  const bad = path.join(root, 'bad.html');
  fs.writeFileSync(good, '<html lang="zh-TW"><title>Example</title></html>');
  fs.writeFileSync(bad, '<html><title>Just a moment</title></html>');
  const manifest = path.join(root, 'self-test-fixtures.yml');
  fs.writeFileSync(manifest, `cases:
  - name: good
    html: good.html
    classification: completed
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
  console.log('No fixture manifest supplied; nothing to verify');
} else {
  for (const file of args) checkManifest(file);
  console.log(`Verified ${args.length} fixture manifest(s)`);
}
