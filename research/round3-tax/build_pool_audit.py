import json,datetime,hashlib
from pathlib import Path
base=Path('research/round3-tax');p=base/'research-log.json';log=json.loads(p.read_text())
registry=json.loads(Path('research/round3-root/coverage/register-window-records.json').read_text());registry=registry if isinstance(registry,list) else registry['records']
r=next(x for x in registry if x['id']=='SG2610200009')
selected={'id':'dstv-jstg2026-20261020','author':'Deutscher Steuerberaterverband e.V.','document':'S08/26, government JStG2026 response, 20 October 2026','process':'JStG2026, BT 21/8283 plus Bundesrat BR 447/26(B)','date':'2026-10-20','date_basis':'Author cover and self-reported register transmittal 20 October 2026 agree; independent recipient receipt not established','submission_url':r['pdf_url'],'local_file':'research/round3-root/coverage/register-pdfs/SG2610200009.pdf','depth':'full_submission','extent':'All 50 physical author pages read. Exact government bill BT 21/8283 selected provisions and explanation, including the 0.3% monthly interest rate and its stated basis, checked. The Bundesrat statement is separately addressed by the author; not every cited court holding or recommendation independently validated.','result':'No issue promoted. Government bill explicitly identified despite stale register RefE association. The proposed 3.6% annual interest rate matches the exact bill. Supplementary proposals and legal or administrative assessments are not treated as factual errors. The 2010-2022 construction-price comparison has repeated secondary attribution but its original statistical release was not independently retrieved; no error inferred from that access gap.','registered_ids':['SG2610200009']}
log['screened']=[z for z in log['screened'] if z['id']!=selected['id']]+[selected]
p.write_text(json.dumps(log,ensure_ascii=False,indent=2)+'\n')
sources=json.loads((base/'sources.json').read_text());byid={s['id']:s for s in sources}
issues={}
for f in base.glob('*tax-r3-*.json'):
 x=json.loads(f.read_text());issues.setdefault(x['document_id'],[]).append(x['id'])
proofs=json.loads((base/'coverage-bounded-ggv-itkv-proofs.json').read_text())['proofs']
roles={r['id']:r for p in proofs for r in p['documents']}
rows=[]
for i,r in enumerate(log['screened']):
 local=[]
 if r.get('local_file'):local.append(r['local_file'])
 local.extend(q for q in r.get('additional_local_files',[]) if q not in local)
 s=byid.get(r['id'],{})
 if s.get('local_file') and s['local_file'] not in local:local.append(s['local_file'])
 if r['id']=='dstv-estref2027-20261021':
  x='research/round3-root/coverage/register-pdfs/SG2610210010.pdf'
  if Path(x).exists():local.append(x)
 row={'id':r['id'],'title':r.get('document'),'author':r.get('author'),'process':r.get('process'),'depth':r['depth'],'reading_extent':r.get('extent'),'local_files':local,'urls':[r['submission_url']] if r.get('submission_url') else [],'evidence_log':'research/round3-tax/research-log.json','log_locator':f'/screened/{i}','related_issue_document_ids':[r['id']] if r['id'] in issues else [],'related_issue_ids':issues.get(r['id'],[]),'document_kind':'external_consultation_reply_declining_formal_statement' if r['id']=='bmds-it-komponentenverordnung-itkv-response-002' else 'external_written_response','window':{'from':'2026-07-25','through':'2026-10-24','date':r.get('date'),'date_status':r.get('date_status','not separately adjudicated here'),'qualifications':[r[k] for k in ['date_basis','date_qualification','eligibility_evidence'] if r.get(k)],'recipient_receipt_independently_verified':False},'registered_ids':r.get('registered_ids',[]),'result':r.get('result')}
 role=roles.get(r['id'])
 if role:
  row['external_submission']=role['external_submission']
  row['author_role']=role['response_kind']
  if not role['external_submission']:row['document_kind']='government_consultation_response'
  row['formal_statement']=role['formal_statement']
 else:
  row['external_submission']=True
  if r.get('author_role'):row['author_role']=r['author_role']
 row['sha256s']=[hashlib.sha256(Path(x).read_bytes()).hexdigest() for x in local if Path(x).exists() and Path(x).suffix=='.pdf']
 rows.append(row)
out={'id':'round3-tax-actual-screening-pool','as_of_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'documents':rows,'counts':{'full_submission':sum(r['depth']=='full_submission' for r in rows),'selected_passages':sum(r['depth']=='selected_passages' for r in rows),'keyword_triage':sum(r['depth']=='keyword_triage' for r in rows),'external_full_submissions':sum(r['depth']=='full_submission' and r['external_submission'] and r.get('formal_statement',True) for r in rows),'government_full_replies':sum(r['depth']=='full_submission' and not r['external_submission'] for r in rows),'external_full_declining_replies':sum(r['depth']=='full_submission' and r['external_submission'] and not r.get('formal_statement',True) for r in rows)},'exclusions':['Primary laws, drafts, studies and judgments are not submission documents.','Extraction-only collection and automated cover-date candidates are excluded.','Covers read solely for date/scope inventory are retained in coverage ledgers, not added as substantive screens.','Mirrors and repeated register transmittals of the same authored version are not additional full reads.'],'metadata_date_scope_ledgers':['research/round3-tax/coverage-bt-response-links.json','research/round3-tax/coverage-bmds-responses.json','research/round3-tax/coverage-bmvg-all-response-links.json','research/round3-tax/coverage-register-cover-metadata.json']}
(base/'pool-audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(out['counts'])
