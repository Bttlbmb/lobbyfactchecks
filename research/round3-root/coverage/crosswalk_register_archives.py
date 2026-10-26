"""Exact-file crosswalk only. It never admits an eligible or screened submission."""
import pathlib,json,collections,hashlib,re,datetime
ROOT=pathlib.Path(__file__).resolve().parents[3];BASE=pathlib.Path(__file__).resolve().parent
records=json.loads((BASE/'register-archive-manifest.json').read_text())['records']
reg={r['id']:r for r in records if r.get('status')=='archived_not_screened'}
reg_hashes={r['sha256'] for r in reg.values()};byhash=collections.defaultdict(dict)
inputs=[];parse_failures=[]
paths=[ROOT/'data/source-registry.json']
for branch in ['root','energy','tax','social']:
 paths.extend((ROOT/('research/round3-'+branch)).rglob('*.json'))
paths=[p for p in paths if not any(t in p.name for t in ['register-archive','register-window','register-public','crosswalk-register-archives','global-register-archive-crosswalk'])]
fields=['id','url','urls','parent_url','process_url','process','process_id','process_ids','process_title','process_titles','authority','ministry','channel','source_kind','kind','title','author','author_labels','member_name']
def visit(d,source,pointer=''):
 if isinstance(d,list):
  for i,v in enumerate(d):visit(v,source,pointer+'/'+str(i))
 elif isinstance(d,dict):
  sha=d.get('sha256');files=d.get('local_files',[])
  if d.get('local_file'):files=[d['local_file']]
  elif d.get('local_pdf'):files=[d['local_pdf']]
  elif d.get('archive') and isinstance(d['archive'],str) and d['archive'].lower().endswith('.pdf'):files=[d['archive']]
  if isinstance(files,str):files=[files]
  if isinstance(sha,str) and sha in reg_hashes:
   for f in files:
    if not isinstance(f,str) or not f.lower().endswith('.pdf') or '/register-pdfs/' in f:continue
    p=ROOT/f
    if not p.is_file():continue
    key=str(p.relative_to(ROOT))
    obs={'metadata_file':source,'json_pointer':pointer,**{k:d[k] for k in fields if k in d}}
    byhash[sha].setdefault(key,[]).append(obs)
  for k,v in d.items():
   if isinstance(v,(list,dict)):visit(v,source,pointer+'/'+str(k))
for p in sorted(set(paths)):
 try:d=json.loads(p.read_text())
 except Exception as e:parse_failures.append({'file':str(p.relative_to(ROOT)),'error':type(e).__name__});continue
 source=str(p.relative_to(ROOT));inputs.append({'file':source,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()});visit(d,source)
# Verify candidate counterpart bytes, rather than treating recorded metadata as proof.
verified={};failures=[]
for sha,fs in byhash.items():
 for f,obs in fs.items():
  blob=(ROOT/f).read_bytes();actual=hashlib.sha256(blob).hexdigest()
  if blob.startswith(b'%PDF-') and actual==sha:verified.setdefault(sha,[]).append({'local_file':f,'sha256':actual,'observations':obs})
  else:failures.append({'local_file':f,'recorded_sha256':sha,'actual_sha256':actual,'actual_PDF':blob.startswith(b'%PDF-')})
rows=[{'register_id':sid,'register_local_file':r['local_file'],'sha256':r['sha256'],'other_archive_copies':verified[r['sha256']],'stage':'exact_binary_copy_only_not_eligibility_or_full_review'} for sid,r in reg.items() if r['sha256'] in verified]
out={'id':'global-register-archive-exact-copy-crosswalk','as_of_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'register_records_considered':len(reg),'matched_register_records':len(rows),'matched_register_binary_hashes':len({r['sha256'] for r in rows}),'verified_nonregister_archive_paths':sum(map(len,verified.values())),'input_metadata_files':inputs,'parse_failures':parse_failures,'candidate_hash_validation_failures':failures,'records':rows,'limits':['Only byte-identical files match. Different cover pages, redactions, scans and metadata can obscure the same authored text.','Other archived PDFs can be primary evidence, official drafts or government responses rather than external submissions. Source kind, authorship, process scope and dates require separate adjudication.','No new reading or eligibility credit, no response-version denominator, no prevalence estimate.','An absent match does not establish absence from a channel or legislative process.']}
(BASE/'global-register-archive-crosswalk.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:out[k] for k in ['register_records_considered','matched_register_records','matched_register_binary_hashes','verified_nonregister_archive_paths','parse_failures','candidate_hash_validation_failures']}))
