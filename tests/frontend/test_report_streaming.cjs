// Run with: node --test tests/frontend/test_report_streaming.cjs
// Exercise the real frontend message handler and bundled Markdown parser offline.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { test } = require('node:test');

const root = path.resolve(__dirname, '../..');
const showdown = require(path.join(root, 'frontend/vendor/js/showdown.min.js'));
const source = fs.readFileSync(path.join(root, 'frontend/scripts.js'), 'utf8');

function createClient(reportType) {
  const element = () => ({
    innerHTML: '', style: {}, value: 'Test research', scrollHeight: 0,
    classList: { add() {}, remove() {} },
    appendChild() {}, querySelectorAll: () => [],
  });
  const elements = Object.fromEntries([
    'output', 'reportContainer', 'selectedImagesContainer', 'status',
    'reportActions', 'task', 'historyPanel', 'toast-notification',
  ].map(id => [id, element()]));
  const sockets = [];
  const sanitized = [];
  const timers = [];
  const context = vm.createContext({
    window: {
      location: { protocol: 'http:', host: 'localhost:8000', pathname: '/' },
      addEventListener() {},
    },
    document: {
      getElementById: id => elements[id] || null,
      querySelector: selector => selector === 'select[name="report_type"]'
        ? { value: reportType } : null,
      querySelectorAll: () => [],
      createElement: element,
    },
    WebSocket: class {
      constructor() { sockets.push(this); }
      close() {}
    },
    // This spy verifies the existing sanitization boundary is retained;
    // DOMPurify's HTML filtering itself is not emulated by this DOM stub.
    DOMPurify: { sanitize(html) { sanitized.push(html); return html; } },
    showdown,
    console: { log() {}, debug() {}, warn() {}, error() {} },
    setTimeout(callback, delay) { timers.push({ callback, delay }); },
    clearTimeout() {},
  });
  vm.runInContext(source, context);
  return {
    start() { vm.runInContext('GPTResearcher.startResearch()', context); },
    send(type, output) {
      sockets.at(-1).onmessage({ data: JSON.stringify({ type, output }) });
    },
    finish() { this.send('path', { md: '/outputs/test.md' }); },
    reconnect() {
      sockets.at(-1).onclose({});
      const timer = timers.findIndex(({ delay }) => delay === 2000);
      assert.notEqual(timer, -1, 'a reconnect should be scheduled');
      timers.splice(timer, 1)[0].callback();
    },
    html() { return elements.reportContainer.innerHTML; },
    sanitized,
  };
}

const tableChunks = [
  '## Comparison\n\n| Method | Result |\n',
  '| --- | --- |\n',
  '| ACT | **Works** |\n',
  '| VLA | See [paper](https://example.com) |\n',
];

for (const reportType of ['research_report', 'deep', 'detailed_report']) {
  test(`${reportType}: table renders during streaming and survives completion`, () => {
    const client = createClient(reportType);
    client.start();
    for (const chunk of tableChunks) client.send('report', chunk);
    const html = client.html();
    assert.match(html, /<table>/);
    assert.equal((html.match(/<tr>/g) || []).length, 3);
    assert.match(html, /<strong>Works<\/strong>/);
    assert.match(html, /href="https:\/\/example.com"/);
    assert.equal(client.sanitized.at(-1), html);
    client.finish();
    assert.equal(client.html(), html);
  });

  test(`${reportType}: token-sized chunks preserve links and fenced code`, () => {
    const client = createClient(reportType);
    client.start();
    const markdown = '[paper](https://example.com)\n\n```python\nprint("ok")\n```\n';
    for (const character of markdown) client.send('report', character);
    assert.match(client.html(), /<a [^>]*href="https:\/\/example.com"/);
    assert.match(client.html(), /<pre><code[^>]*>[\s\S]*print/);
    assert.equal((client.html().match(/<pre>/g) || []).length, 1);
    client.finish();
    assert.match(client.html(), /<pre><code/);
  });

  test(`${reportType}: a new research run does not retain previous content`, () => {
    const client = createClient(reportType);
    client.start();
    for (const chunk of tableChunks) client.send('report', chunk);
    client.finish();
    client.start();
    assert.equal(client.html(), '');
    client.send('report', 'A fresh ');
    client.send('report', 'paragraph.');
    assert.equal(client.html(), '<p>A fresh paragraph.</p>');
    client.finish();
    assert.equal(client.html(), '<p>A fresh paragraph.</p>');
  });

  test(`${reportType}: a table split across connections retains its header`, () => {
    const client = createClient(reportType);
    client.start();
    client.send('report', tableChunks[0]);
    client.reconnect();
    for (const chunk of tableChunks.slice(1)) client.send('report', chunk);
    assert.match(client.html(), /<table>/);
    assert.match(client.html(), /<th[^>]*>Method<\/th>/);
    assert.equal((client.html().match(/<tr>/g) || []).length, 3);
    const html = client.html();
    client.finish();
    assert.equal(client.html(), html);
  });

  test(`${reportType}: starting over before completion clears partial Markdown`, () => {
    const client = createClient(reportType);
    client.start();
    client.send('report', '```python\nunfinished');
    client.start();
    client.send('report', 'New report.');
    assert.equal(client.html(), '<p>New report.</p>');
  });
}
