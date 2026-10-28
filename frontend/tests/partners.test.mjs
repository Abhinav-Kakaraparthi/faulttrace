// Static semantics/security regression, not browser or keyboard acceptance.
import { test, after } from 'node:test';
import assert from 'node:assert/strict';
import { build } from 'vite';
import { mkdtempSync, writeFileSync, rmSync } from 'node:fs';
import { resolve, join, sep } from 'node:path';
import { pathToFileURL } from 'node:url';
const root = process.cwd();
const temporary = mkdtempSync(resolve('node_modules/.partners-'));
after(() => {
  if (!temporary.startsWith(join(root, 'node_modules') + sep)) throw new Error('unsafe_cleanup_path');
  rmSync(temporary, { recursive: true, force: true });
});
const output = await build({ configFile: false, logLevel: 'silent',
  build: { ssr: 'tests/partners-entry.tsx', write: false, rollupOptions: { output: { format: 'es' } } } });
const chunk = output.output.find(item => item.type === 'chunk' && item.isEntry);
const file = join(temporary, 'render.mjs'); writeFileSync(file, chunk.code);
const { entry, records, safeDocumentationURL, documentationRecords } = await import(pathToFileURL(file));
test('explicit lookup requires independent confirmation and is disabled offline', () => {
  const html = entry();
  assert.match(html, /Human-confirmed equipment model/);
  assert.match(html, /I independently confirmed/);
  assert.match(html, /<input[^>]+value=""/);
  assert.match(html, /<input[^>]+type="checkbox"/);
  assert.match(html, /<button[^>]+disabled=""[^>]*>Search official documentation/);
  assert.match(html, /No Tavily request will be made/);
  assert.doesNotMatch(html, /MAXIMATOR[^<]+180|confidence|API key|access token/);
});
test('references show source, retrieval time and uncertainty without executing retrieved markup', () => {
  const html = records();
  assert.match(html, /https:\/\/www.wika.com\/example/);
  assert.match(html, /rel="noopener noreferrer"/);
  assert.match(html, /Retrieved/);
  assert.match(html, /Model applicability unverified/);
  assert.match(html, /not telemetry, a measured reading or correction authority/);
  assert.match(html, /&lt;script&gt;/);
  assert.doesNotMatch(html, /<script>/);
});
test('citation renderer rejects unsafe schemes and off-domain lookalikes', () => {
  assert.equal(safeDocumentationURL('https://www.wika.com/a', 'wika.com'), true);
  for (const url of ['javascript:alert(1)', 'https://wika.com.evil.invalid/a',
    'https://user@wika.com/a', 'http://wika.com/a', 'https://wika.com:9443/a']) {
    assert.equal(safeDocumentationURL(url, 'wika.com'), false);
  }
});
test('denied access and malformed history cannot display retained source details', () => {
  const previous = [{ id:'private-doc',status:'completed',created_at:'2026-10-28',
    context:{manufacturer:'WIKA',model:'private-model',domain:'wika.com'},result:null }];
  assert.deepEqual(documentationRecords(previous,true),previous);
  assert.deepEqual(documentationRecords(previous,false),[]);
  assert.deepEqual(documentationRecords([{...previous[0],result:{sources:[{url:'https://wika.com'}]}}],true),[]);
  assert.deepEqual(documentationRecords(null,true),[]);
  assert.match(entry(false),/Reference access unavailable/);
  assert.doesNotMatch(entry(false),/<form|private-model|wika.com/);
});
