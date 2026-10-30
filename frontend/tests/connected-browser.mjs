// Real localhost API/SQLite journey. Requires tools.connected_browser_demo, never a hosted URL.
import assert from 'node:assert/strict';
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { resolve, join } from 'node:path';
const { chromium } = await import(process.env.FAULTTRACE_PLAYWRIGHT_MODULE || 'playwright');
const config = JSON.parse(readFileSync('../.local/connected-browser/current.json', 'utf8'));
const origin = `http://127.0.0.1:${config.port}`;
assert.equal(new URL(origin).hostname, '127.0.0.1');
const output = join(config.root, 'browser'); mkdirSync(output, { recursive: true });
const browser = await chromium.launch({ headless: true, executablePath: process.env.FAULTTRACE_CHROMIUM_EXECUTABLE });
const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, recordVideo: { dir: output, size: { width: 1440, height: 900 } } });
const requests = [], errors = [], steps = [];
await context.route('**/*', route => new URL(route.request().url()).origin === origin ? route.continue() : route.abort());
context.on('response', response => { const u = new URL(response.url()); if (u.pathname.startsWith('/api/')) requests.push({ path: u.pathname, method: response.request().method(), status: response.status() }); });
const commander = await context.newPage(), operator = await context.newPage();
for (const page of [commander, operator]) page.on('pageerror', error => errors.push(error.message));
const state = page => page.evaluate(async () => (await fetch('/api/state')).json());
async function wait(page, expression) {
  // Evaluate test predicates in Node, not inside the application's strict CSP.
  const predicate = new Function('s', `return (${expression})`);
  const deadline = Date.now() + 30000;
  while (Date.now() < deadline) {
    const value = await state(page);
    if (predicate(value)) return value;
    await new Promise(resolve => setTimeout(resolve, 100));
  }
  throw new Error('Expected server transition not reached: ' + expression);
}
async function refresh(page) { await page.getByRole('button', { name: 'Refresh server state' }).click(); }
async function shot(page, name) {
  await page.screenshot({ path: join(output, `${name}.png`), fullPage: true });
  steps.push({ name, state: await state(page) });
  console.log('PASS ' + name);
}
async function open(page, view) {
  await page.goto(origin + '/' + view);
  await page.getByRole('button', { name: 'Verify local server', exact: true }).click();
  await page.locator('.workspace-masthead').waitFor();
}
async function human(page, { photo, asset, type, reading, unit, position }) {
  const form = page.locator('.human-observation');
  for (const select of await form.locator('select').all()) assert.equal(await select.inputValue(), '', 'independent answers start blank');
  await form.getByLabel('Observation source').selectOption(photo ? 'confirm' : 'independent');
  if (photo) await form.getByLabel('Source photograph').selectOption(photo);
  await form.getByLabel('Equipment identity you independently observed').selectOption(asset);
  await form.getByLabel('Measurement type you observed').selectOption(type);
  if (reading !== undefined) {
    assert.equal(await form.getByLabel('Your reading', { exact: true }).inputValue(), '');
    await form.getByLabel('Your reading', { exact: true }).fill(String(reading));
    await form.getByLabel('Your observed unit').selectOption(unit);
  }
  if (position) await form.getByLabel('Your position observation').selectOption(position);
  await form.getByLabel('I entered my own observation', { exact: false }).check();
  await form.getByRole('button', { name: 'Record human observation', exact: true }).click();
}
try {
  await open(commander, 'commander');
  if (!(await state(commander)).incident) await commander.getByRole('button', { name: 'Start restriction-to-recovery simulation', exact: true }).click();
  else assert.equal((await state(commander)).planning.length, 0, 'only an empty isolated setup can resume');
  await wait(commander, 's.journey?.evidence_mode === "task-evidence"');
  await commander.getByRole('button', { name: 'Choose next observation', exact: true }).click();
  await wait(commander, 's.task?.asset_id === "F-17"');
  await shot(commander, '01-planned-assignment-offline-double');
  await open(operator, 'operator');
  await operator.getByLabel('Choose a photograph from files', { exact: false }).setInputFiles(resolve('../fixtures/image-evidence/panel-a.png'));
  await operator.getByRole('button', { name: 'Submit image / collection only', exact: true }).click();
  let s = await wait(operator, 's.evidence.some(e => e.kind === "image")');
  const photo = s.evidence.find(e => e.kind === 'image').id;
  await operator.getByText('Analysis options', { exact: true }).click();
  await operator.getByRole('button', { name: 'Analyze photographic observation', exact: true }).click();
  s = await wait(operator, 's.evidence.some(e => e.analysis?.status === "interpreted")');
  assert.equal(s.evidence.find(e => e.id === photo).analysis.interpretation.reading, 180);
  assert.equal(s.journey.assessment.eligible, false, 'model claim alone cannot approve');
  await refresh(operator);
  await operator.locator('.human-observation').waitFor();
  await shot(operator, '02-upload-and-structured-claim-offline-double');
  await human(operator, { photo, asset: 'F-17', type: 'differential_pressure', reading: 180, unit: 'kPa' });
  s = await wait(operator, 's.evidence.some(e => e.human_observation?.photo_id)');
  const humanRef = 'evidence-' + s.evidence.find(e => e.human_observation?.photo_id).id;
  assert.equal(s.journey.assessment.eligible, false, 'V-08 report still missing');
  await refresh(commander);
  await commander.getByRole('button', { name: 'Choose next observation', exact: true }).click();
  s = await wait(commander, 's.task?.asset_id === "V-08"');
  assert.ok(s.planning.at(-1).proposal.evidence_refs.includes(humanRef), 'next proposal cites the independent report');
  await shot(commander, '03-reviewed-evidence-informs-next-task');
  await refresh(operator);
  await operator.getByRole('heading', { name: 'Observe valve position only', exact: true }).waitFor();
  await human(operator, { asset: 'V-08', type: 'position', position: 'intermediate' });
  await wait(operator, 's.journey?.assessment.eligible === true');
  await refresh(commander);
  await commander.getByLabel('I approve only this simulated replacement', { exact: false }).check();
  await shot(commander, '04-eligible-human-approval');
  await commander.getByRole('button', { name: 'Approve simulated correction', exact: true }).click();
  await wait(commander, 's.journey?.approval_current === true');
  await refresh(operator);
  await operator.getByRole('button', { name: 'Complete simulated filter replacement', exact: true }).click();
  s = await wait(operator, 's.journey?.maintenance_status === "simulated_replacement_completed"');
  assert.notEqual(s.journey.recovery.status, 'verified', 'maintenance is not recovery');
  await shot(operator, '05-operator-completion-not-recovery');
  await refresh(commander);
  await commander.getByRole('button', { name: 'Start simulated recovery monitoring', exact: true }).click();
  await wait(commander, 's.journey?.monitoring?.status === "running"');
  await shot(commander, '06-independent-monitoring');
  s = await wait(commander, 's.journey?.recovery.status === "verified"');
  assert.ok(s.journey.recovery.sample_count >= 5);
  assert.ok(s.journey.recovery.window_seconds >= 40);
  await refresh(commander); await refresh(operator);
  await shot(commander, '07-sample-derived-recovery');
  for (const page of [commander, operator]) {
    await page.reload();
    await page.getByRole('button', { name: 'Verify local server', exact: true }).click();
    await page.locator('.investigation-activity').waitFor();
    assert.equal((await state(page)).journey.recovery.status, 'verified', 'reload retains recovered state');
  }
  await operator.setViewportSize({ width: 390, height: 844 });
  await shot(operator, '08-mobile-persisted-outcome');
  assert.deepEqual(errors, []);
  assert.ok(requests.every(r => r.status < 400), 'no API error on successful journey');
  writeFileSync(join(output, 'result.json'), JSON.stringify({ label: 'OFFLINE TEST OUTPUT / scripted doubles and synthetic human inputs', result: 'PASS', requests, steps, external_provider_calls: 0 }, null, 2));
} catch (error) {
  await commander.screenshot({ path: join(output, 'failure-commander.png'), fullPage: true });
  await operator.screenshot({ path: join(output, 'failure-operator.png'), fullPage: true }).catch(() => {});
  writeFileSync(join(output, 'failure.json'), JSON.stringify({ error: error.message, requests, steps, errors }, null, 2));
  throw error;
} finally { await context.close(); await browser.close(); }
