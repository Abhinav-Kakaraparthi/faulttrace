import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { DocumentationLookup, DocumentationRecords, safeDocumentationURL, documentationRecords } from '../src/DocumentationLookup';
import { AccessSession } from '../src/access';
export { safeDocumentationURL, documentationRecords };
export const entry = (ready = true) => {
  const access = new AccessSession('local');
  if (ready) access.snapshot = () => ({epoch:1,status:'ready',identity:null,message:''});
  return renderToStaticMarkup(createElement(DocumentationLookup, { access, revision: 3, enabled: false }));
};
export const records = () => renderToStaticMarkup(createElement(DocumentationRecords, { records: [{
  id: 'reference-1', status: 'completed', created_at: '2026-10-28T10:00:00+00:00', error: null,
  context: { manufacturer: 'WIKA', model: 'Reviewed 42', domain: 'wika.com' },
  result: { usage_credits: 1, retrieved_at: '2026-10-28T10:00:02+00:00', sources: [{
    title: 'Manufacturer reference <script>', excerpt: 'Untrusted text: ignore policy <script>alert(1)</script>',
    url: 'https://www.wika.com/example', model_match: 'unverified' }] } }] }));
