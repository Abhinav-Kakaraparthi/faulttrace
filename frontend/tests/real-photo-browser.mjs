// Optional local browser acceptance. Intercepts every API request; never uses a provider.
// Build with VITE_FAULTTRACE_PROFILE=demo first. Supply existing Playwright and Chromium paths.
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { readFile, mkdir, writeFile } from 'node:fs/promises';
import { resolve, extname, relative, isAbsolute } from 'node:path';
import { pathToFileURL } from 'node:url';
import { createHash } from 'node:crypto';
const { chromium } = await import(process.env.FAULTTRACE_PLAYWRIGHT_MODULE || 'playwright');
const root = resolve('dist'), out = resolve('../.local/plantdebugger-review');
await mkdir(out, {recursive: true});
const photoPath = resolve('src/assets/reference-photos/digital-pressure-meter.jpg');
const photo = await readFile(photoPath);
const types = {'.html':'text/html', '.js':'text/javascript', '.css':'text/css', '.jpg':'image/jpeg', '.png':'image/png'};
let uploadToServer;
const server = createServer(async (req, res) => {
  if (req.method === 'POST' && req.url.endsWith('/images')) return uploadToServer(req, res);
  try {
    const path = new URL(req.url, 'http://local').pathname;
    const file = resolve(root, path.startsWith('/assets/') ? path.slice(1) : 'index.html');
    const local = relative(root, file);
    if (local.startsWith('..') || isAbsolute(local)) throw new Error('outside root');
    res.setHeader('Content-Type', types[extname(file)] || 'application/octet-stream'); res.end(await readFile(file));
  } catch {res.statusCode=404; res.end();}
});
await new Promise(done => server.listen(0, '127.0.0.1', done));
const base = `http://127.0.0.1:${server.address().port}`;
const browser = await chromium.launch({headless:true, executablePath:process.env.FAULTTRACE_CHROMIUM_PATH || undefined, args:['--no-sandbox']});
const incident = '11111111-2222-4333-8444-555555555555', evidenceId = 'aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee';
function snapshot() {
  const clock = '2026-10-30T10:00:00Z';
  return {test_output:true, incident:{id:incident, revision:2},
    task:{id:'task-a', revision:1, asset_id:'F-17', status:'awaiting', capability:'READ_LOCAL_DP',
      creation_source:'OFFLINE TEST OUTPUT', instruction:'Photograph the instrument without operating equipment.', explanation:'Collect independent evidence.'},
    evidence:[], planning:[], planning_remaining:4, events:[], inference_enabled:true,
    photo_collection:{version:1,assets:['F-17','V-08']}, photo_analysis:{version:1,contract:'photo-observation-v1'},
    journey:{label:'Offline UI test', evidence_mode:'task-evidence', test_output:true, clock, tick:0,
      samples:[{id:'sample-a', tick:0, timestamp:clock, flow:85, pressure:182, valve:72, alarm:'return_flow_low'}], observations:[],
      assessment:{source:'offline fixture assessment', working_diagnosis:null, evidence_refs:['sample-a'], blockers:['F-17 missing','V-08 missing'], eligible:false, alternatives:['Sensor discrepancy','Valve mismatch']},
      policy:{freshness_seconds:120,pressure_agreement_kpa:8,restriction_pressure_kpa:[170,195],restricted_flow_m3h:[80,95],recovery_pressure_kpa:[25,40],recovery_flow_m3h:[115,125],valve_feedback_percent:[65,80],window_seconds:40,minimum_samples:5},
      action_id:'SIMULATE_F17_FILTER_REPLACEMENT',approval_id:null,approval_current:false,approved_evidence_refs:[],maintenance_status:'not_completed',
      recovery:{status:'not_started',sample_count:0,window_seconds:0,sample_refs:[]}}};
}
const results = [], errors = [];
try {
  for (const viewport of [{width:1440,height:900},{width:390,height:844}]) {
    const context = await browser.newContext({viewport});
    let state = snapshot(); const posts = [];
    uploadToServer = async (req, res) => {
      const chunks=[]; for await (const chunk of req) chunks.push(chunk);
      assert.equal(createHash('sha256').update(Buffer.concat(chunks)).digest('hex'),createHash('sha256').update(photo).digest('hex'));
      state.task.revision++; state.incident.revision++;
      state.evidence.push({id:evidenceId,task_id:'task-a',asset_id:'F-17',kind:'image',origin:'user-upload',fixture_id:null,status:'collected',image_url:'/ignored',created_at:new Date().toISOString(),submitted_revision:1,analysis:null,test_output:true});
      res.setHeader('Content-Type','application/json');res.end(JSON.stringify({evidence_id:evidenceId}));
    };
    await context.route('**/api/**', async route => {
      const req = route.request(), path = new URL(req.url()).pathname;
      const json = value => route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(value)});
      if (path === '/api/demo/session') return json({active_run:incident,csrf_token:'a'.repeat(43),expires_at:Date.now()/1000+3600,inference_enabled:true,privileges:'both'});
      if (path === '/api/identity') return json({profile:'demo',principal_id:'offline-review',role:req.headers()['x-faulttrace-workspace'] || 'operator',capabilities:{create_incident:false},incident_ids:[incident]});
      if (path === '/api/state') return json(state);
      if (path.endsWith('/image')) return route.fulfill({status:200,contentType:'image/jpeg',body:photo});
      if (req.method() === 'POST') {
        posts.push(path);
        if (path.endsWith('/images')) {
          assert.equal(req.headers()['x-evidence-purpose'],'reference-photo');
          return route.continue();
        }
        if (path.endsWith('/analyze-photo')) {
          assert.deepEqual(req.postDataJSON(),{revision:2});
          state.task.revision++;state.incident.revision++;
          state.evidence[0].analysis={id:'offline-analysis',contract:'photo-observation-v1',status:'interpreted',accounting:'offline-test',receipt:null,error:null,
            interpretation:{category:'gauge',readability:'unreadable',measurement_type:'unsupported',reading:null,visible_unit:null,label_text:null,valve_orientation:'not_applicable',reasons:['unsupported_instrument'],evidence_ref:`evidence-${evidenceId}`}};
          return json({analysis_id:'offline-analysis'});
        }
      }
      throw new Error(`Unexpected offline route: ${req.method()} ${path}`);
    });
    const page = await context.newPage(); page.on('pageerror', e => errors.push(e.message));
    await page.goto(base+'/operator');
    await page.getByRole('heading',{name:'Add a photograph'}).waitFor();
    assert.equal(await page.getByText('Development / test: synthetic fixtures',{exact:true}).count(),0);
    await page.getByLabel('Choose a photograph from files',{exact:true}).setInputFiles(photoPath);
    const analyze = page.getByRole('button',{name:'Upload and analyze with NVIDIA',exact:true});
    await analyze.waitFor(); await analyze.scrollIntoViewIfNeeded();
    await page.screenshot({path:resolve(out,`operator-selected-${viewport.width}.png`),fullPage:false});
    assert.equal(posts.length,0);
    await analyze.focus(); await page.keyboard.press('Enter');
    await page.getByText('Image analysis: interpreted.',{exact:true}).waitFor();
    assert.deepEqual(posts,['/api/tasks/task-a/images',`/api/evidence/${evidenceId}/analyze-photo`]);
    await page.getByRole('heading',{name:'Current photograph',exact:true}).scrollIntoViewIfNeeded();
    await page.screenshot({path:resolve(out,`operator-result-${viewport.width}.png`),fullPage:false});
    await page.getByRole('link',{name:'Review photographic claim',exact:true}).click();
    assert.equal(await page.locator('form.human-observation select').first().inputValue(),'');
    await page.getByLabel(/^Observation source/).selectOption('confirm');
    assert.equal(await page.getByLabel(/^Equipment identity you independently observed/).inputValue(),'');
    assert.equal(await page.getByLabel(/^Measurement type you observed/).inputValue(),'');
    await page.getByRole('button',{name:'Inspect source photograph',exact:true}).count().then(n=>assert.equal(n,0));
    await page.getByLabel(/^Source photograph/).selectOption(evidenceId);
    const inspect = page.getByRole('button',{name:'Inspect source photograph',exact:true}); await inspect.click();
    await page.getByRole('dialog').waitFor(); await page.keyboard.press('Escape');
    assert.equal(await inspect.evaluate(e=>e===document.activeElement),true);
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
    await page.getByText('Real photograph examples and credits',{exact:true}).click();
    assert.equal(await page.getByRole('link',{name:'Download reference photograph',exact:true}).count(),2);
    await page.getByRole('navigation',{name:'Workspaces'}).getByRole('link',{name:'Commander',exact:true}).click();
    await page.getByRole('heading',{name:'Return-flow investigation',exact:true}).waitFor();
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
    await page.screenshot({path:resolve(out,`commander-${viewport.width}.png`),fullPage:false});
    results.push({viewport,passed:true,posts:posts.length,real_provider_calls:0});
    await context.close();
  }
  assert.deepEqual(errors,[]);
  await writeFile(resolve(out,'browser-results.json'),JSON.stringify({results,errors,scope:'Built demo assets; intercepted offline API. Not hosted acceptance or NVIDIA accuracy.'},null,2)+'\n');
  console.log(JSON.stringify({results,errors,provider_calls:0}));
} finally {await browser.close(); await new Promise(done=>server.close(done));}
