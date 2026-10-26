import json,hashlib,collections,pathlib,urllib.parse
BASE=pathlib.Path(__file__).resolve().parents[1]
def read(p):return json.loads((BASE/p).read_text())
def arr(v):return v if isinstance(v,list) else [v] if v else []
rows=[]
for branch in ['root','energy','tax','social']:
 for x in read('research/pool-audit-'+branch+'.json')['documents']:
  y=dict(x);y['branch']=branch;y['title']=x.get('title',x.get('author/title',x['id']));y['local_files']=arr(x.get('local_files',x.get('local_file(s)')));y['urls']=arr(x.get('urls',x.get('url(s)')));y['related_issue_document_ids']=arr(x.get('related_issue_document_ids'))
  y['included']=x.get('included_in_documented_pool',x.get('count_in_screened_pool',True))
  if branch=='tax' and y['depth']=='extracted_only':y['depth']='full_text_ocr';y['included']=True
  rows.append(y)
# Admission to the actual-reading pool is separate from the coverage census.
# These reviewed branch ledgers contain reading evidence, never download batches.
for round_number in [3,4,6]:
 for branch in ['root','energy','tax','social']:
  path='research/round'+str(round_number)+'-'+branch+'/pool-audit.json'
  if not (BASE/path).exists():continue
  for x in read(path)['documents']:
   y=dict(x);y['branch']='round'+str(round_number)+'_'+branch
   y['title']=x.get('title',x.get('author_title',x.get('author',x['id'])))
   y['local_files']=arr(x.get('local_files'));y['urls']=arr(x.get('urls'))
   y['related_issue_document_ids']=arr(x.get('related_issue_document_ids'))
   y['included']=x.get('included_in_documented_pool',x.get('count_in_screened_pool',y['depth']!='extracted_only'))
   y['reported_document_kind']=y.get('document_kind')
   if y.get('document_kind') in ['external_written_submission','external_written_response']:y['document_kind']='written_submission'
   if y.get('document_kind')=='external_consultation_reply_declining_formal_statement':y['document_kind']='consultation_reply_declining_formal_statement'
   if 'government' in str(y.get('document_kind','')).lower():y['document_kind']='government_consultation_response';y['external_submission']=False
   rows.append(y)
issues=sum([read('data/'+f+'.json') for f in ['findings','unresolved-leads','rejected-candidates']],[])
sources={s['id']:s for s in read('data/source-registry.json')}
for did in sorted({x['document_id'] for x in issues}):
 cases=[x for x in issues if x['document_id']==did];srcs=[sources[x['submission_source_id']] for x in cases if x.get('submission_source_id') in sources]
 rows.append(dict(id=did,branch='case_index',title=srcs[0].get('title',did) if srcs else did,process=cases[0]['law_id'],depth='selected_passages',included=True,related_issue_document_ids=[did],local_files=[s['local_file'] for s in srcs if s.get('local_file')],urls=[s['url'] for s in srcs if s.get('url')],evidence_log=[x.get('research_record') for x in cases],document_kind='oral_contribution' if 'oral' in did else 'written_submission'))
# Shared containers may hold multiple authored responses. Never use them as identity keys.
fileuses=collections.defaultdict(lambda:collections.defaultdict(set))
for x in rows:
 for f in x['local_files']:fileuses[f][x['branch']].add(x['id'])
containers={f for f,b in fileuses.items() if any(len(ids)>1 for ids in b.values())}
containers|={f for f in fileuses if any(k in f.lower() for k in ['materialzusammen','suizidhilfe-2022-bt-submissions','tariftreue-2025-bt-submissions','protocol','protokoll'])}
hashes={}
# Eviction of a reproducible download does not erase its recorded identity or
# create a new reading unit. Use the audited cache hash without restoring it.
cache_manifest=BASE/'research/cache-manifest.json'
historical_hashes={x['path']:x['sha256'] for x in read('research/cache-manifest.json')['files']} if cache_manifest.exists() else {}
for f in fileuses:
 p=BASE/f
 if f not in containers and p.suffix.lower()=='.pdf':
  if p.is_file():hashes[f]=hashlib.sha256(p.read_bytes()).hexdigest()
  elif f in historical_hashes:hashes[f]=historical_hashes[f]
container_urls=set()
for x in rows:
 if any(f in containers for f in x['local_files']):container_urls.update(x['urls'])
def keys(x):
 k=[('issue',i) for i in x['related_issue_document_ids']]
 for f in x['local_files']:
  if f in hashes:k.extend([('file',f),('sha',hashes[f])])
 for u in x['urls']:
  if u in container_urls:continue
  q=urllib.parse.urlsplit(u)
  if '.pdf' in q.path.lower():k.append(('url',urllib.parse.urlunsplit((q.scheme,q.netloc,q.path,'',''))))
 return k
parents=list(range(len(rows)))
def find(i):
 while parents[i]!=i:parents[i]=parents[parents[i]];i=parents[i]
 return i
def union(a,b):parents[find(b)]=find(a)
seen={}
for i,x in enumerate(rows):
 for k in keys(x):
  if k in seen:union(i,seen[k])
  else:seen[k]=i
# Manual aliases are reviewed and documented alongside the inventory.
manual=read('research/screening-pool-aliases.json') if (BASE/'research/screening-pool-aliases.json').exists() else []
byid={x['id']:i for i,x in enumerate(rows)}
for alias in manual:
 for aid in alias['ids'][1:]:union(byid[alias['ids'][0]],byid[aid])
groups=collections.defaultdict(list)
for i,x in enumerate(rows):groups[find(i)].append(x)
rank={'extracted_only':0,'keyword_triage':1,'selected_passages':2,'full_text_ocr':3,'full_submission':4}
out=[]
for g in groups.values():
 chosen=max(g,key=lambda x:rank[x['depth']]);included=any(x['included'] for x in g)
 out.append(dict(id=chosen['id'],title=chosen['title'],process=chosen.get('process'),depth=chosen['depth'],included_in_documented_pool=included,document_kind=next((x['document_kind'] for x in g if x.get('document_kind')), 'written_submission'),scope_status=sorted({scope for x in g for scope in arr(x.get('scope_status'))} or {'federal_process'}),related_issue_document_ids=sorted({i for x in g for i in x['related_issue_document_ids']}),source_inventory_ids=[x['id'] for x in g],branches=sorted({x['branch'] for x in g}),local_files=sorted({f for x in g for f in x['local_files']}),urls=sorted({u for x in g for u in x['urls']}),screening_evidence=[{k:v for k,v in x.items() if k in ['branch','id','depth','evidence_log','log_locator','notes','depth_or_identity_note','window','window_status','window_qualifiers','date_or_version','date_precision','registered_ids','reading_extent','read_extent','screening_protocol','independent_review','reported_document_kind','result']} for x in g]))
out.sort(key=lambda x:x['id']);included=[x for x in out if x['included_in_documented_pool']]
# Preserve explicit actor-role decisions. Unknown baseline roles are not silently
# turned into registered lobbyists or government responses.
for output in out:
 g=[x for x in rows if x['id'] in output['source_inventory_ids']]
 decisions={x['external_submission'] for x in g if isinstance(x.get('external_submission'),bool)}
 output['external_submission']=next(iter(decisions)) if len(decisions)==1 else None
 output['actor_role_evidence']=[{k:x[k] for k in ['id','branch','author_role','external_submission','document_kind'] if k in x} for x in g if 'external_submission' in x or 'author_role' in x]
 if output['external_submission'] is False:output['document_kind']='government_consultation_response'
summary=dict(unit='Distinct authored response/version; jointly authored responses count once. Oral contribution separately labelled. Mirrors and repeat checks merged. This is a targeted pool, not a representative sample.',individually_identified_screened_units=len(included),by_depth=dict(collections.Counter(x['depth'] for x in included)),by_document_kind=dict(collections.Counter(x['document_kind'] for x in included)),excluded_extracted_only_units=sum(not x['included_in_documented_pool'] for x in out),issue_associated_documents=len({x['document_id'] for x in issues}),documents_with_provisional_findings=len({x['document_id'] for x in read('data/findings.json')}), provisional_findings=len(read('data/findings.json')), unresolved_leads=len(read('data/unresolved-leads.json')), rejected_candidates=len(read('data/rejected-candidates.json')), major_findings=sum(x['severity']=='major' for x in read('data/findings.json')),documents_with_major_findings=len({x['document_id'] for x in read('data/findings.json') if x['severity']=='major'}),case_index_only_rows=[x['id'] for x in out if x['branches']==['case_index']],ambiguous_batches=read('research/pool-audit-root.json')['ambiguous_batches'],manual_aliases=manual)
summary['explicit_actor_status_counts']=dict(collections.Counter('external' if x['external_submission'] is True else 'government' if x['external_submission'] is False else 'not_reconciled_in_actor_ledger' for x in included))
# Compute minimum extra members of the 25-of-26 logged rental consultation batch.
rental_files={f for x in rows if x['branch']=='root' and x['process']=='MietrechtII2026 consultation' for f in x['local_files']}
known_rental=[x for x in included if rental_files.intersection(x['local_files'])]
summary['rental_batch_individually_screened_members']=len(known_rental)
summary['rental_batch_additional_unidentified_screened_minimum']=max(0,25-len(known_rental))
if len(known_rental)==26 and (BASE/'research/round3-root/rental-reconciliation-proof.json').exists():
 for batch in summary['ambiguous_batches']:
  if batch['process']=='MietrechtII2026 consultation':
   batch['current_state']='resolved_by_fresh_named_triage_2026-10-25'
   batch['current_individually_screened_members']=26
   batch['current_unidentified_additional_minimum']=0
   batch['current_proof']='research/round3-root/rental-reconciliation-proof.json'
summary['screened_pool_minimum_including_batch_bound']=len(included)+summary['rental_batch_additional_unidentified_screened_minimum']
summary['tool_history_only_additional_screens_excluded']=3
summary['minimum_by_depth_including_batch_bound']=dict(summary['by_depth'])
summary['minimum_by_depth_including_batch_bound']['keyword_triage']+=summary['rental_batch_additional_unidentified_screened_minimum']
summary['scope_qualifications']=[{'id':x['id'],'scope_status':x['scope_status']} for x in included if x['scope_status']!=['federal_process']]
summary['limitations']=['Three additional tool-history-only screens excluded; archive-only and primary-evidence-only files excluded.', 'The rental consultation archive has26 PDFs, but the log records25 triaged. Seven are individually documented; at least18 others screened, with exact membership unresolved.', 'One original/corrected GAÄD response is counted as two versions, not two response families.', 'The depth categories describe recorded reading extent, not complete factual verification of every assertion.', 'The pool is deliberately targeted and unevenly examined; findings divided by this denominator do not estimate error prevalence.', 'Public statements and oral contributions are labelled separately in by_document_kind; some public statements lack a verified formal submission channel.', 'Counts include one BStBK submitted package with a joint appendix; the appendix is not counted separately.']
if len(known_rental)==26:
 summary['limitations'][1]='The original rental25-versus26log ambiguity is preserved historically. Fresh named keyword triage of19remaining members now documents all26 individually, so no anonymous batch bound is added to this snapshot. This does not upgrade keyword triage to full reading.'
summary['independent_audits']=[str(p.relative_to(BASE)) for p in sorted((BASE/'research').glob('pool-merged-audit-*.json'))]
summary['audit_note']='Branch inventories independently reconciled by multiple AI agents. See audit files for actual dispositions; no human specialist review implied.'
summary['active_round_reading_ledgers']=['research/round6-'+b+'/pool-audit.json' for b in ['root','energy','tax','social'] if (BASE/('research/round6-'+b+'/pool-audit.json')).exists()]
summary['prior_round4_reading_ledgers']=['research/round4-'+b+'/pool-audit.json' for b in ['root','energy','tax','social'] if (BASE/('research/round4-'+b+'/pool-audit.json')).exists()]
summary['previous_round_reading_ledgers']=['research/round3-'+b+'/pool-audit.json' for b in ['root','energy','tax','social']]
summary['active_round_scope_limit']='These additional actual reads include earlier historical versions and depth upgrades. They are not a completed three-month cohort; see data/coverage-progress.json. The prior independent merged audits cover the baseline. Active-round audits identify their exact snapshot counts and hashes; later additions are not silently certified by an earlier snapshot review.'
# Deeper claim checks annotate existing reading units; they never add another copy.
pilot_index_path = BASE/'data/factual-check-pilots.json'
if pilot_index_path.is_file():
 for entry in read('data/factual-check-pilots.json')['pilots']:
  if entry['status'] != 'complete':continue
  pilot = read(entry['ledger'])
  if pilot['summary']['status'] != 'complete':continue
  # The reading ledger can use a canonical ID different from the batch ID.
  # Match the already archived original as well; never create a new reading unit.
  batch_to_pool = {}
  for document in pilot['documents']:
   matches = [output['id'] for output in out
              if document['id'] == output['id']
              or document['id'] in output['source_inventory_ids']
              or document['local_file'] in output['local_files']]
   if len(matches) != 1:
    raise ValueError(f"Factual batch document must match exactly one existing reading unit: {document['id']} -> {matches}")
   batch_to_pool[document['id']] = matches[0]
  for output in out:
   checked = [c for c in pilot['claims'] if batch_to_pool[c['document_id']] == output['id']]
   if checked:
    output.setdefault('factual_check_pilots', []).append({'id':pilot['summary']['id'], 'ledger':entry['ledger'], 'claim_ids':[c['id'] for c in checked], 'outcomes':dict(collections.Counter(c['result'] for c in checked)), 'repeat_read_adds_unit':False})
  summary.setdefault('factual_check_pilots', []).append({'id':pilot['summary']['id'], 'summary':entry['summary'], 'documents':pilot['summary']['documents'], 'claims':pilot['summary']['claims'], 'new_reading_units':0})
(BASE/'data/screening-pool.json').write_text(json.dumps({'method':summary['unit'],'documents':out},ensure_ascii=False,indent=2)+'\n')
(BASE/'data/screening-pool-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(summary,ensure_ascii=False,indent=2))
print('MULTIBRANCH GROUPS')
for x in out:
 if len(set(x['branches'])-{'case_index'})>1:print(x['source_inventory_ids'])
print('COUNTAINERS',sorted(containers))

summary['previous_round_independent_audits']=[str(p.relative_to(BASE)) for p in sorted((BASE/'research/round3-reviews').glob('*merged*pool*.json'))]
summary['prior_round4_independent_audits']=[str(p.relative_to(BASE)) for p in sorted((BASE/'research/round4-reviews').glob('*merged*pool*.json'))]
summary['active_round_independent_audits']=[str(p.relative_to(BASE)) for p in sorted((BASE/'research/round6-reviews').glob('*merged*.json'))]
(BASE/'data/screening-pool-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
