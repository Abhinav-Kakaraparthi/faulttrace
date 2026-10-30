// Actual Chromium against built demo assets, with all network requests intercepted.
// No workflow/database, provider connection, new incident or persistent browser session.
import assert from 'node:assert/strict';
import { readFileSync, mkdirSync, writeFileSync } from 'node:fs';
import { resolve, join, extname } from 'node:path';
import { layoutState, run } from './layout-fixture.mjs';

const { chromium } = await import(process.env.FAULTTRACE_PLAYWRIGHT_MODULE || 'playwright');
const output = resolve(process.env.FAULTTRACE_LAYOUT_OUTPUT || '../.local/visual/layout-repair');
mkdirSync(output, { recursive: true });
const observe = process.argv.includes('--observe');
const browser = await chromium.launch({ headless: true, executablePath: process.env.FAULTTRACE_CHROMIUM_EXECUTABLE || undefined });
const results = [], forbidden = [], errors = [];
try {
  for (const width of [1440, 1024, 768, 390]) {
    for (const view of ['commander', 'operator']) {
      const context = await browser.newContext({ viewport: { width, height: width === 390 ? 844 : 900 } });
      const page = await context.newPage();
      page.on('pageerror', error => errors.push(error.message));
      await context.route('**/*', async route => {
        const request = route.request(), url = new URL(request.url());
        if (url.origin !== 'https://layout.invalid' || request.method() !== 'GET') {
          forbidden.push({ method: request.method(), path: url.pathname }); return route.abort();
        }
        const json = value => route.fulfill({ contentType: 'application/json', body: JSON.stringify(value) });
        if (url.pathname === '/api/demo/session') return json({ active_run: run, csrf_token: 'a'.repeat(43), expires_at: Date.now() / 1000 + 3600, inference_enabled: false });
        if (url.pathname === '/api/identity') return json({ profile: 'demo', principal_id: 'offline-layout-review', role: request.headers()['x-faulttrace-workspace'], capabilities: { create_incident: false }, incident_ids: [run] });
        if (url.pathname === '/api/state') return json(layoutState(view === 'operator'));
        if (url.pathname === '/api/evidence/layout-photo/image') return route.fulfill({ contentType: 'image/png', body: readFileSync('../fixtures/image-evidence/panel-b.png') });
        if (['/commander', '/operator', '/'].includes(url.pathname)) return route.fulfill({ contentType: 'text/html', body: readFileSync('dist/index.html') });
        if (/^\/assets\/[\w.-]+$/.test(url.pathname) || url.pathname === '/favicon.svg') {
          const type = { '.js': 'text/javascript', '.css': 'text/css', '.png': 'image/png', '.svg': 'image/svg+xml' }[extname(url.pathname)];
          return route.fulfill({ contentType: type, body: readFileSync(join('dist', url.pathname)) });
        }
        forbidden.push({ method: request.method(), path: url.pathname }); return route.abort();
      });
      await page.goto(`https://layout.invalid/${view}`);
      await page.locator('.investigation-activity').waitFor();
      const metrics = await page.evaluate(() => {
        const rect = selector => { const r = document.querySelector(selector).getBoundingClientRect(); return { x: r.x, y: r.y, width: r.width, height: r.height, bottom: r.bottom }; };
        const matching = [];
        const collect = rules => { for (const rule of rules) {
          if (rule.media && !matchMedia(rule.conditionText).matches) continue;
          if (rule.selectorText && document.querySelector('.connected-shell').matches(rule.selectorText) && rule.style.display) matching.push({ selector: rule.selectorText, display: rule.style.display });
          else if (rule.cssRules) collect(rule.cssRules);
        } };
        for (const sheet of document.styleSheets) collect(sheet.cssRules);
        return { shellDisplay: getComputedStyle(document.querySelector('.connected-shell')).display, matching,
          masthead: rect('.workspace-masthead'), workspace: rect('.workspace'), main: rect('main'),
          action: document.querySelector('.current-action') ? rect('.current-action') : null,
          scrollWidth: document.documentElement.scrollWidth, width: innerWidth,
          schematic: document.querySelector('.schematic') ? rect('.schematic') : null,
          schematicWrap: document.querySelector('.schematic-wrap') ? rect('.schematic-wrap') : null,
          telemetry: [...document.querySelectorAll('.journey-metrics>div')].slice(0, 4).map(el => ({ client: el.clientWidth, scroll: el.scrollWidth })) };
      });
      const file = `${observe ? 'before' : 'after'}-${view}-${width}.png`;
      await page.screenshot({ path: join(output, file), fullPage: false });
      results.push({ view, width, file, ...metrics });
      if (!observe) {
        assert.equal(metrics.shellDisplay, 'block', `${view}/${width}: shell must stack`);
        assert.ok(metrics.masthead.width >= width - 1, 'masthead spans viewport');
        assert.ok(metrics.workspace.y >= metrics.masthead.bottom - 1, 'workspace below masthead');
        assert.ok(metrics.workspace.width >= width - 1, 'workspace uses full width');
        assert.ok(metrics.masthead.height < 180, 'compact masthead');
        assert.ok(metrics.scrollWidth <= width + 1, 'no page horizontal overflow');
        if (metrics.action) assert.ok(metrics.action.x >= 0 && metrics.action.x + metrics.action.width <= width + 1, 'action panel fits');
        assert.ok(metrics.telemetry.every(item => item.scroll <= item.client + 1), 'telemetry labels/units fit');
        if (width >= 1024 && metrics.schematic) assert.ok(metrics.schematic.width <= metrics.schematicWrap.width + 1, 'desktop schematic fits');
        if (view === 'operator') assert.ok(Math.abs(metrics.main.x - (width - metrics.main.width) / 2) < 2, 'Operator centered');
        await page.getByText('Demo session', { exact: true }).click();
        await page.getByText('Operator in second tab', { exact: false }).waitFor({ state: 'visible' });
        const menu = await page.locator('.session-menu-body').boundingBox();
        assert.ok(menu.x >= 0 && menu.x + menu.width <= width + 1, 'session menu stays on screen');
        await page.getByText('Demo session', { exact: true }).click();
        if (view === 'commander') {
          await page.getByRole('button', { name: 'Inspect V-08 Flow control valve', exact: true }).press('Enter');
          assert.equal(await page.getByRole('button', { name: 'Inspect V-08 Flow control valve', exact: true }).getAttribute('aria-pressed'), 'true');
          await page.locator('.process-and-signals').screenshot({ path: join(output, `process-${width}.png`) });
          if (width === 390) {
            const region = page.getByRole('region', { name: 'Scrollable P-04 F-17 V-08 process schematic' });
            await region.evaluate(el => { el.scrollLeft = 0; });
            await region.focus(); await page.keyboard.press('ArrowRight');
            await page.waitForFunction(() => document.querySelector('.schematic-wrap').scrollLeft > 0);
          }
        } else {
          const inspection = page.getByRole('button', { name: /^Inspect evidence for F-17,/ });
          await inspection.click();
          await page.getByRole('dialog', { name: 'Evidence inspection' }).waitFor({ state: 'visible' });
          await page.getByRole('dialog', { name: 'Evidence inspection' }).screenshot({ path: join(output, `inspection-${width}.png`) });
          await page.keyboard.press('Escape');
          assert.equal(await page.getByRole('dialog').isVisible(), false);
          assert.equal(await inspection.evaluate(el => el === document.activeElement), true);
        }
      }
      await context.close();
    }
  }
  assert.deepEqual(forbidden, [], 'No unexpected network request or mutation');
  assert.deepEqual(errors, [], 'No page exception');
  console.log(JSON.stringify({ result: observe ? 'baseline recorded; no acceptance claimed' : 'PASS', rendered: results.length, provider_calls: 0, incidents_created: 0 }));
} finally {
  writeFileSync(join(output, `${observe ? 'before' : 'after'}-metrics.json`), JSON.stringify({ results, forbidden, errors }, null, 2));
  await browser.close();
}
