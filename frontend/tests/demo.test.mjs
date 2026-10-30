import { test } from 'node:test';
import assert from 'node:assert/strict';
import { initial, reduceDemo } from '../src/demo.ts';
import { escalatedWithoutTask, planningBlocker } from '../src/planningPolicy.ts';
import { httpDiagnosticSummary } from '../src/api.ts';

test('HTTP diagnostics display safe status categories and retain historical unknowns', () => {
  assert.equal(httpDiagnosticSummary({ error: 'provider_network_error' }), null);
  assert.match(httpDiagnosticSummary({ error: 'provider_http_error' }), /HTTP status: unknown.*Category: unknown/);
  assert.match(httpDiagnosticSummary({ error: 'provider_http_error', http_status: null, http_error_category: null }), /HTTP status: unknown.*Category: unknown/);
  assert.match(httpDiagnosticSummary({ error: 'provider_http_error', http_status: 401, http_error_category: 'http_unauthorized' }), /HTTP status: 401.*Category: http_unauthorized.*cause is not established/);
});

const planningReady = { task: null, planning: [], incident: { revision: 2 }, planning_remaining: 4, inference_enabled: true };

test('initial human escalation explains no assignment without reopening an unchanged context', () => {
  const state = { ...planningReady, planning_remaining: 3,
    planning: [{ status: 'escalated', context_revision: 2 }] };
  assert.equal(escalatedWithoutTask(state), true);
  assert.match(planningBlocker(state), /Human review requested.*No Operator task.*will not be retried/);
  assert.equal(escalatedWithoutTask({ ...state, incident: { revision: 3 } }), false);
  assert.equal(planningBlocker({ ...state, incident: { revision: 3 } }), null);
  assert.equal(escalatedWithoutTask({ ...state, task: { status: 'awaiting' } }), false);
  assert.match(planningBlocker({ ...state, task: { status: 'awaiting' } }), /Finish or report/);
});
test('connected planner is available only after explicit incident creation and no blocking task', () => {
  assert.equal(planningBlocker(planningReady), null);
  for (const status of ['awaiting', 'submitted', 'analyzing']) {
    assert.match(planningBlocker({ ...planningReady, task: { status } }), /Finish or report/);
  }
  for (const status of ['observed', 'needs_evidence']) {
    assert.equal(planningBlocker({ ...planningReady, task: { status } }), null);
  }
});
test('disabled inference, pending reservation, spent budget and duplicate context explain disabled actions', () => {
  assert.match(planningBlocker({ ...planningReady, inference_enabled: false }), /Inference disabled/);
  assert.match(planningBlocker({ ...planningReady, planning: [{ status: 'pending', context_revision: 1 }] }), /pending/);
  assert.match(planningBlocker({ ...planningReady, planning_remaining: 0 }), /Budget exhausted/);
  assert.match(planningBlocker({ ...planningReady, planning: [{ status: 'rejected', context_revision: 2 }] }), /already has an attempt/);
});

test('a rejected attempted context stays blocked with three turns remaining; a different revision alone cannot override a blocking task', () => {
  const attempted = { ...planningReady, incident: { revision: 1 }, planning_remaining: 3,
    planning: [{ status: 'rejected', context_revision: 1 }] };
  assert.match(planningBlocker(attempted), /already has an attempt/);
  assert.match(planningBlocker({ ...attempted, incident: { revision: 2 }, task: { status: 'awaiting' } }), /Finish or report/);
  assert.equal(planningBlocker({ ...attempted, incident: { revision: 3 }, task: { status: 'needs_evidence' } }), null);
});

test('incident starts with an observation request and no completed evidence', () => {
  const state = reduceDemo(initial, { type: 'start' });
  assert.equal(state.started, true);
  assert.equal(state.waiting, true);
  assert.equal(state.evidence.length, 0);
  assert.deepEqual(state.activity.map(event => event.title), ['Sample incident started', 'Local observation requested']);
  assert.deepEqual(initial.activity, []);
});

for (const outcome of ['readable', 'unreadable', 'cannot-access', 'wrong-equipment']) {
  test(`${outcome} records a distinct observation, never a recovery`, () => {
    const start = reduceDemo(initial, { type: 'start' });
    const state = reduceDemo(start, { type: 'submit', outcome, fixture: outcome === 'readable' ? 'a' : undefined, note: ' field context ' });
    assert.equal(state.waiting, false);
    assert.equal(state.started, true);
    assert.equal(state.evidence[0].outcome, outcome);
    assert.equal(state.evidence[0].note, 'field context');
    assert.equal(state.activity.at(-1).evidence, 1);
    const message = state.activity.at(-1).detail;
    if (outcome === 'readable') assert.match(message, /180 kPa.*not a diagnosis/);
    if (outcome === 'unreadable') assert.match(message, /No numeric reading recorded/);
    if (outcome === 'cannot-access') assert.match(message, /No equipment observation/);
    if (outcome === 'wrong-equipment') assert.match(message, /Asset identity disputed/);
    assert.equal('recovery' in state, false);
    assert.equal(reduceDemo(state, { type: 'submit', outcome: 'readable', note: '' }), state);
  });
}

test('reset removes the sample journey; repeat observation preserves earlier evidence', () => {
  const observed = reduceDemo(reduceDemo(initial, { type: 'start' }), { type: 'submit', outcome: 'unreadable', fixture: 'b', note: '' });
  const reopened = reduceDemo(observed, { type: 'reopen' });
  assert.equal(reopened.waiting, true);
  assert.equal(reopened.evidence[0].outcome, 'unreadable');
  const second = reduceDemo(reopened, { type: 'submit', outcome: 'readable', fixture: 'a', note: '' });
  assert.deepEqual(second.evidence.map(item => item.id), [1, 2]);
  assert.equal(second.activity.length, 5);
  assert.deepEqual(reduceDemo(second, { type: 'reset' }), initial);
  assert.equal(reduceDemo(initial, { type: 'submit', outcome: 'readable', note: '' }), initial);
});


// Policy examples use independently stated expected outcomes; no provider or backend.
const { canApprove, canExecute, recoveryLabel } = await import('../src/journeyState.ts');
const readyJourney = { maintenance_status: 'not_completed', approval_id: 'assigned-approval', approval_current: false,
  assessment: { eligible: true }, recovery: { status: 'not_started' } };
test('simulated correction requires explicit consent for the exact displayed revision', () => {
  assert.equal(canApprove(readyJourney, 7, null), false);
  assert.equal(canApprove(readyJourney, 7, 6), false);
  assert.equal(canApprove(readyJourney, 7, 7), true);
  assert.equal(canApprove({ ...readyJourney, assessment: { eligible: false } }, 7, 7), false);
  assert.equal(canApprove({ ...readyJourney, approval_current: true }, 7, 7), false);
  assert.equal(canApprove({ ...readyJourney, maintenance_status: 'simulated_replacement_completed' }, 7, 7), false);
});
test('operator execution requires current approval and corroborated evidence; completion cannot imply recovery', () => {
  assert.equal(canExecute(readyJourney), false);
  assert.equal(canExecute({ ...readyJourney, approval_current: true }), true);
  assert.equal(canExecute({ ...readyJourney, approval_current: true, approval_id: undefined }), false);
  assert.equal(canExecute({ ...readyJourney, approval_current: true, assessment: { eligible: false } }), false);
  assert.equal(canExecute({ ...readyJourney, approval_current: true, maintenance_status: 'simulated_replacement_completed' }), false);
  assert.equal(recoveryLabel('observing'), 'Observing post-correction samples');
  assert.equal(recoveryLabel('failed'), 'Recovery verification failed');
  assert.equal(recoveryLabel('verified'), 'Simulated operating recovery verified');
});


const { resolveRoute } = await import('../src/routing.ts');
test('dedicated routes override obsolete query controls; legacy connected URLs keep unrelated query and fragment', () => {
  for (const [path, workspace, canonical] of [
    ['/commander', 'commander', '/commander'], ['/operator', 'operator', '/operator'],
    ['/?mode=connected&view=operator', 'operator', '/operator'],
    ['/?mode=connected', 'commander', '/commander'],
    ['/?view=operator&source=bookmark#task', 'operator', '/operator?source=bookmark#task'],
    ['/operator/?mode=sample&view=commander', 'operator', '/operator'],
    ['/commander?view=operator', 'commander', '/commander'],
  ]) {
    assert.deepEqual(resolveRoute(new URL(path, 'http://localhost:5180')), {kind: 'connected', workspace, canonical});
  }
  assert.equal(resolveRoute(new URL('http://localhost:5180/?mode=sample')).kind, 'sample');
  assert.equal(resolveRoute(new URL('http://localhost:5180/missing')).kind, 'not-found');
});


const { photoFileError, photoDimensionsError, localPhotoURL, uploadBlob } = await import('../src/photoUpload.ts');
const { apiResponse } = await import('../src/api.ts');
test('photo selection preserves server limits and releases local preview URLs exactly once', () => {
  assert.equal(photoFileError({type:'image/jpeg',size:1024}), null);
  assert.match(photoFileError({type:'image/heic',size:100}), /PNG or JPEG/);
  for (const size of [0,2097153]) assert.match(photoFileError({type:'image/png',size}), /2 MiB/);
  assert.equal(photoDimensionsError(1024,1024), null);
  for(const size of [[15,16],[2049,16],[2048,1024]]) assert.match(photoDimensionsError(...size), /pixels/);
  const revoked=[];
  const preview=localPhotoURL(new Blob(['private-image']), {createObjectURL:()=> 'blob:local-only',revokeObjectURL:url=>revoked.push(url)});
  assert.equal(preview.url,'blob:local-only'); preview.release(); preview.release();
  assert.deepEqual(revoked,['blob:local-only']);
});
function fakeUpload() {
  return { upload:{onprogress:null},status:200,responseText:'{"evidence_id":"saved-photo"}',calls:0,headers:{},
    open(method,path) { this.method=method; this.path=path; },
    setRequestHeader(name,value) { this.headers[name]=value; },
    send(blob) { this.calls++; this.blob=blob; }, abort() { this.onabort?.(); } };
}
test('upload progress is measured, transfer completion is not storage confirmation, and upload uses one POST', async () => {
  const xhr=fakeUpload(),progress=[],blob=new Blob(['image'],{type:'image/jpeg'});
  let settled=false;
  const result=uploadBlob('/api/tasks/task/images',blob,{'Idempotency-Key':'one-key','X-Task-Revision':'3','X-Evidence-Purpose':'reference-photo'},new AbortController().signal,p=>progress.push(p),()=>xhr);
  result.then(()=>{settled=true;});
  xhr.upload.onprogress({lengthComputable:true,loaded:25,total:100});
  xhr.upload.onprogress({lengthComputable:false,loaded:50,total:0});
  xhr.upload.onprogress({lengthComputable:true,loaded:100,total:100});
  await Promise.resolve(); assert.equal(settled,false);
  assert.deepEqual(progress,[0,25,null,100]); assert.equal(xhr.calls,1);
  assert.equal(xhr.method,'POST'); assert.equal(xhr.blob,blob);
  assert.equal(xhr.headers['X-Evidence-Purpose'],'reference-photo');
  assert.equal(xhr.headers['Idempotency-Key'],'one-key');
  xhr.onload(); assert.deepEqual(await apiResponse(await result),{evidence_id:'saved-photo'});
});
test('upload failures and server validation errors stay sanitized with no retry', async () => {
  for(const event of ['onerror','ontimeout','onabort']) {
    const xhr=fakeUpload();
    const request=uploadBlob('/api/tasks/task/images',new Blob(['x']),{},new AbortController().signal,()=>{},()=>xhr);
    xhr[event]({message:'CREDENTIAL_SENTINEL'});
    await assert.rejects(request,error=>!error.message.includes('CREDENTIAL_SENTINEL') && /refresh/i.test(error.message));
    assert.equal(xhr.calls,1);
  }
  const xhr=fakeUpload();
  const request=uploadBlob('/api/tasks/task/images',new Blob(['x']),{},new AbortController().signal,()=>{},()=>xhr);
  xhr.status=413; xhr.responseText='{"error":"image_size_invalid","detail":"CREDENTIAL_SENTINEL"}'; xhr.onload();
  await assert.rejects(apiResponse(await request),error=>/2 MiB/.test(error.message)&&!error.message.includes('CREDENTIAL_SENTINEL'));
  const malformed=fakeUpload();
  const bad=uploadBlob('/api/tasks/task/images',new Blob(['x']),{},new AbortController().signal,()=>{},()=>malformed);
  malformed.responseText='CREDENTIAL_SENTINEL';malformed.onload();
  await assert.rejects(apiResponse(await bad),error=>/refresh/i.test(error.message)&&!error.message.includes('CREDENTIAL_SENTINEL'));
  const controller=new AbortController();controller.abort();const stopped=fakeUpload();
  await assert.rejects(uploadBlob('/api/tasks/task/images',new Blob(['x']),{},controller.signal,()=>{},()=>stopped));
  assert.equal(stopped.calls,0);
});
