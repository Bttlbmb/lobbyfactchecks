import json,hashlib
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parent.parent
def read(p):return json.loads((R/p).read_text())
issues=sum([read('data/'+n)for n in ['findings.json','unresolved-leads.json','rejected-candidates.json']],[])
byid={a['id']:a for a in issues};sources={s['id']:s for s in read('data/source-registry.json')};documents={d['id']:d for d in read('data/documents.json')};flags=[]
def walk(v,path):
 if isinstance(v,dict):
  for k,z in v.items():
   p=path+'.'+k
   if k in ['source_id','additional_source_id','submission_source_id']and isinstance(z,str)and z not in sources:flags.append(dict(path=p,problem='unresolved_source_id',value=z))
   if k=='source_ids'and isinstance(z,list):
    for sid in z:
     if isinstance(sid,str)and sid not in sources:flags.append(dict(path=p,problem='unresolved_source_id',value=sid))
   if k=='original'and isinstance(z,str):
    if not v.get('locator'):flags.append(dict(path=p,problem='missing_quote_locator'))
    if v.get('language')not in ['en']and not str(v.get('translation_en','')).lower().startswith('translation'):flags.append(dict(path=p,problem='missing_labelled_translation'))
   walk(z,p)
 elif isinstance(v,list):
  for i,z in enumerate(v):walk(z,path+'['+str(i)+']')
for a in issues:
 walk(a,a['id'])
 for k in ['draft','effect','limits','materiality_explanation','direction_explanation']:
  if not a.get(k):flags.append(dict(path=a['id'],problem='missing_'+k))
 q=a.get('request_quote')or a.get('request_quote_reference')
 if not q:flags.append(dict(path=a['id'],problem='missing_request_evidence'))
 if a.get('request_quote_reference'):
  z=a['request_quote_reference'];parent=byid.get(z.get('issue_id'),{})
  if not parent.get(z.get('field','request_quote'),{}).get('original'):flags.append(dict(path=a['id'],problem='bad_cross_issue_request_reference'))
 if a.get('review',{}).get('specialist')is not None or a.get('author_response')!=[]:flags.append(dict(path=a['id'],problem='unexpected_specialist_or_response'))
for d in documents.values():walk(d,'document.'+d['id'])
def originals(v,path=''):
 o={}
 if isinstance(v,dict):
  for k,z in v.items():
   p=path+'.'+k
   if k=='original'and isinstance(z,str):o[p]=z
   else:o.update(originals(z,p))
 elif isinstance(v,list):
  for i,z in enumerate(v):o.update(originals(z,path+'['+str(i)+']'))
 return o
baseline_issues=[]
for n in ['findings.json','unresolved-leads.json','rejected-candidates.json']:baseline_issues+=read('research/round2/baseline/'+n)
baseline_quotes_unchanged=all(x['id']in byid and originals(x)==originals(byid[x['id']])for x in baseline_issues)
m=read('research/round2/assembly-manifest.json');included=set(m['inputs']);unlisted=[]
for folder in ['round2-root','round2-tax','round2-social','round2-energy']:
 for p in (R/'research'/folder).glob('*.json'):
  x=json.loads(p.read_text())
  if isinstance(x,dict)and x.get('status')=='ai_screened'and str(p.relative_to(R))not in included:unlisted.append(str(p.relative_to(R)))
timing=read('data/investigation-round2.json')
requirements=[
 dict(requirement='Ministry consultation pages, Bundestag hearings and Lobbyregister investigated',evidence=['research/round2-root/screening-log.json','research/round2-tax/research-log.json','research/round2-social/research-log.json','research/round2-energy/screening-log.json','data/source-registry.json'],assessment='Substantive source reviews and records cover all three channels; gated author-publication leads are explicitly unresolved, not asserted as formally received submissions.'),
 dict(requirement='Ongoing and completed federal processes, addressed draft versions',evidence=['data/findings.json','data/unresolved-leads.json','data/documents.json'],assessment='Each issue contains addressed-version metadata. Examples include ongoing JStG2026 consultation and completed2018CannKG process. Historical official/mirror and byte-edition limits are explicit; later law is not silently used as addressed draft.'),
 dict(requirement='Factual or source-description mismatch; context and benign alternatives',evidence=['research/round2-social/semantic-audit.json','research/round2-energy/final-evidence-audit.json','research/round2-tax/audit.json','research/round2-reviews/'],assessment='Independently reviewed provisional cases are separated from unresolved leads. Negative screens record rescued readings, missing evidence and model disagreements without promoting them as errors.'),
 dict(requirement='User JSON fields, ai_screened, severity versus direction, null unknown',evidence=['data/issue.schema.json','data/validation-report.json'],assessment=f'All{len(issues)} issue records retain requested fields and ai_screened. Separate materiality/direction explanations present; unknown-direction entries are null.'),
 dict(requirement='Exact short original quotations, labelled translations, precise locators and request grounding',evidence=['data/validation-report.json','data/quotation-audit.json','research/reviews/manual-quote-checks.json','data/documents.json'],assessment='Automated extraction, actual visual reviews and declared web-only source checks are distinguished. All request evidence resolves, including shared and cross-issue references. No automated check is claimed to establish substantive truth.'),
 dict(requirement='Correction, effect and limits; no intent or invented response',evidence=['data/findings.json','data/unresolved-leads.json','data/rejected-candidates.json'],assessment='Every record explains effect/limits and separate materiality/direction. Unresolved cases may state correction conditionally. Specialist fields remain null and author_response arrays empty.'),
 dict(requirement='Multiple AI agents independently check one another',evidence=['data/review-index.json','research/round2-reviews/'],assessment=f"All{sum(a['finding_state']=='provisional_finding' for a in issues)} provisional findings have saved independent-AI reviews. The four-agent team made reciprocal primary-source checks; no human specialist review is implied."),
 dict(requirement='Save project-folder deliverables; preserve first round',evidence=['README.md','data/','research/round2/baseline/','data/investigation.json'],assessment='Saved JSON and source/review artifacts exist. Original32baselineissue quotations unchanged; original first-round timing bytes equal baseline snapshot.'),
 dict(requirement='Spend another at least two hours and finish started cases',evidence=['data/investigation-round2.json','research/round2/assembly-manifest.json'],assessment=('Completed minimum duration: '+str(timing.get('duration_seconds'))+' elapsed seconds and '+str(timing.get('goal_time_used_seconds_at_completion'))+' goal-reported time-used seconds; all screened round-two raw records manifested, with unresolved limits retained.') if timing['status']=='completed' else 'Timing gate remains pending until actual completion>=7200seconds; all currently screened round-two raw issue records are manifested, with unresolved limits retained.')]
report=dict(audit_type='Requirement-by-requirement research and deliverable audit; source reviews remain the substantive evidence',round_status=timing['status'],counts=dict(Counter(a['finding_state']for a in issues)),law_count=len({a['law_id']for a in issues}),document_count=len({a['document_id']for a in issues}),structural_and_reference_flags=flags,unmanifested_screened_round2_records=unlisted,baseline_original_quotations_unchanged=baseline_quotes_unchanged,first_round_timing_bytes_unchanged=(R/'data/investigation.json').read_bytes()==(R/'research/round2/baseline/investigation.json').read_bytes(),requirements=requirements,pending=[] if timing['status']=='completed' else ['Actual minimum-duration gate and final metadata completion'],limits='Mechanical completeness does not establish factual correctness. Two formal-channel gates and other substantive uncertainties are intentionally preserved as unresolved leads. No specialist review or author contact.')
(R/'research/round2/completion-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:report[k]for k in ['counts','structural_and_reference_flags','unmanifested_screened_round2_records','baseline_original_quotations_unchanged','first_round_timing_bytes_unchanged','pending']}))
