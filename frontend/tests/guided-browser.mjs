// Actual localhost API/SQLite continuation. No API mocks, provider sockets or images.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve,join} from 'node:path';
const {chromium}=await import(process.env.FAULTTRACE_PLAYWRIGHT_MODULE || 'playwright');
const config=JSON.parse(readFileSync('../.local/continuation-browser/current.json','utf8'));
const origin=`http://127.0.0.1:${config.port}`, output=join(config.root,'browser');mkdirSync(output,{recursive:true});
const browser=await chromium.launch({headless:true,executablePath:process.env.FAULTTRACE_CHROMIUM_PATH || process.env.FAULTTRACE_CHROMIUM_EXECUTABLE,args:['--no-sandbox']});
const context=await browser.newContext({viewport:{width:1440,height:900}});
const requests=[],errors=[];
await context.route('**/*',r=>new URL(r.request().url()).origin===origin?r.continue():r.abort());
context.on('response',r=>{const path=new URL(r.url()).pathname;if(path.startsWith('/api/'))requests.push({path,method:r.request().method(),status:r.status()});});
context.on('page',p=>p.on('pageerror',e=>errors.push(e.message)));
const operator=await context.newPage();let commander=await context.newPage();
const state=p=>p.evaluate(async()=> (await fetch('/api/state')).json());
async function wait(p,predicate){const end=Date.now()+30000;while(Date.now()<end){const s=await state(p);if(predicate(s))return s;await new Promise(r=>setTimeout(r,100));}throw new Error('Expected continuation transition was not reached');}
async function open(p,role){await p.goto(origin+'/'+role);await p.getByRole('button',{name:'Verify local server',exact:true}).click();await p.locator('.workspace-masthead').waitFor();}
async function human(asset,type,value){const form=operator.locator('.human-observation');await form.waitFor();
 for(const s of await form.locator('select').all())assert.equal(await s.inputValue(),'');
 await form.getByLabel(/^Observation source/).selectOption('independent');
 await form.getByLabel(/^Equipment identity/).selectOption(asset);
 await form.getByLabel(/^Measurement type/).selectOption(type);
 if(type==='position')await form.getByLabel(/^Your position observation/).selectOption(value);
 else{await form.getByLabel('Your reading',{exact:true}).fill(String(value));await form.getByLabel(/^Your observed unit/).selectOption('kPa');}
 await form.getByLabel(/^I entered my own observation/).check();await form.getByRole('button',{name:'Record human observation',exact:true}).click();}
try{
 await open(commander,'commander');await commander.getByRole('button',{name:'Start restriction-to-recovery simulation',exact:true}).click();
 await commander.getByRole('button',{name:'Start guided investigation',exact:true}).waitFor();
 await commander.getByRole('button',{name:'Start guided investigation',exact:true}).focus();await commander.keyboard.press('Enter');
 await wait(commander,s=>s.task?.asset_id==='F-17');await open(operator,'operator');
 await commander.close(); // Continuation must have no dependency on a Commander tab.
 await human('F-17','differential_pressure',180);
 await wait(operator,s=>s.task?.asset_id==='V-08');
 await operator.getByRole('heading',{name:'Observe valve position only',exact:true}).waitFor();
 await human('V-08','position','intermediate');
 await wait(operator,s=>s.continuation?.phase==='awaiting_approval');
 commander=await context.newPage();await open(commander,'commander');
 await commander.getByRole('heading',{name:'Evidence is ready. Commander must approve the simulated correction.',exact:true}).waitFor();
 await commander.screenshot({path:join(output,'01-automatic-replanning-awaiting-approval.png'),fullPage:true});
 let s=await state(commander);assert.equal(s.planning.length,2);assert.equal(s.journey.approval_id,null);
 const pressure=s.evidence.find(e=>e.human_observation?.measurement_type==='differential_pressure');
 assert.ok(s.planning[1].proposal.evidence_refs.includes('evidence-'+pressure.id));
 await commander.getByLabel(/^I approve only this simulated replacement/).check();
 await commander.getByRole('button',{name:'Approve simulated correction',exact:true}).click();
 await wait(operator,s=>s.journey.approval_current);
 await operator.getByRole('button',{name:'Complete simulated filter replacement',exact:true}).click();
 s=await wait(operator,s=>s.journey.maintenance_status==='simulated_replacement_completed');assert.notEqual(s.journey.recovery.status,'verified');
 await wait(commander,s=>s.continuation?.phase==='verifying_recovery');
 await commander.getByRole('heading',{name:'Collecting independent post-action measurements',exact:true}).waitFor();
 await commander.screenshot({path:join(output,'02-automatic-independent-monitoring.png'),fullPage:true});
 s=await wait(commander,s=>s.continuation?.phase==='complete');
 assert.equal(s.journey.recovery.status,'verified');assert.ok(s.journey.recovery.sample_count>=5);assert.ok(s.journey.recovery.window_seconds>=40);
 assert.equal(requests.filter(r=>r.method==='POST'&&['/api/planning','/api/simulation/monitor'].includes(r.path)).length,0);
 await commander.getByRole('heading',{name:'Simulated recovery verified',exact:true}).waitFor();
 await commander.screenshot({path:join(output,'03-guided-recovery-complete.png'),fullPage:true});
 await commander.setViewportSize({width:390,height:844});
 assert.equal(await commander.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
 await commander.screenshot({path:join(output,'04-mobile-commander-guided-outcome.png'),fullPage:true});
 await operator.setViewportSize({width:390,height:844});await operator.reload();await operator.getByRole('button',{name:'Verify local server',exact:true}).click();
 await operator.locator('.investigation-activity').waitFor();assert.equal((await state(operator)).journey.recovery.status,'verified');
 assert.equal(await operator.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
 await operator.screenshot({path:join(output,'04-mobile-persisted-recovery.png'),fullPage:true});
 assert.deepEqual(errors,[]);assert.ok(requests.every(r=>r.status<400));
 writeFileSync(join(output,'result.json'),JSON.stringify({result:'PASS',label:'OFFLINE TEST OUTPUT / scripted planner and independent simulated human reports',
  browser_manual_planning_requests:0,browser_manual_monitor_requests:0,external_provider_calls:0,requests,
  outcome:{phase:s.continuation.phase,planning_count:s.planning.length,samples:s.journey.recovery.sample_count,window_seconds:s.journey.recovery.window_seconds}},null,2));
 console.log('PASS: durable guided investigation with closed Commander tab, automatic replanning, human approval/action and automatic independent recovery; zero provider sockets');
}catch(e){await operator.screenshot({path:join(output,'failure-operator.png'),fullPage:true}).catch(()=>{});if(!commander.isClosed())await commander.screenshot({path:join(output,'failure-commander.png'),fullPage:true});throw e;}
finally{await context.close();await browser.close();}
