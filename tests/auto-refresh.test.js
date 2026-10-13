// Run with: node --test tests/auto-refresh.test.js
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

test('successful unchanged polls do not postpone the fallback reload', async () => {
  const timeouts = new Map();
  let nextId = 0;
  let reloads = 0;
  const context = {
    console,
    document: {
      readyState: 'complete',
      querySelector: () => ({ dataset: { autoRefreshValue: '1' } }),
      querySelectorAll: () => [],
    },
    window: { addEventListener() {}, location: { reload() { reloads++; } }, scrollY: 0 },
    sessionStorage: { setItem() {} },
    setInterval() {},
    setTimeout(fn) { timeouts.set(++nextId, fn); return nextId; },
    clearTimeout(id) { timeouts.delete(id); },
    fetch: async () => ({ ok: true, json: async () => ({ value: 1 }) }),
  };
  vm.createContext(context);
  vm.runInContext(fs.readFileSync('static/js/auto-refresh.js', 'utf8'), context);
  const refresh = new context.window.AutoRefresh({ pollUrl: '/poll/', fallbackReloadMs: 15000 });
  const originalTimer = refresh.fallbackTimerId;
  await refresh.checkForUpdate();
  await refresh.checkForUpdate();
  assert.equal(refresh.fallbackTimerId, originalTimer);
  timeouts.get(originalTimer)();
  assert.equal(reloads, 1);
});
