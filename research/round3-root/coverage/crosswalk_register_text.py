"""Candidate full-extraction text equality, never an automatic authored-version merge."""
import pathlib,json,hashlib,collections,concurrent.futures,subprocess,datetime
ROOT=pathlib.Path(__file__).resolve().parents[3];BASE=pathlib.Path(__file__).resolve().parent;OUT=BASE/'text-fingerprints';OUT.mkdir(exist_ok=True)
paths=[ROOT/'data/source-registry.json']
for branch in ['root','energy','tax','social']:paths.extend((ROOT/('research/round3-'+branch)).rglob('*.json'))
paths=[p for p in paths if 'global-register' not in p.name and '/text-fingerprints/' not in str(p)]
files={}
def visit(d,source):
 if isinstance(d,list):
  for v in d:visit(v,source)
 elif isinstance(d,dict):
  sha=d.get('sha256');fs=[d['local_file']] if d.get('local_file') else [d['local_pdf']] if d.get('local_pdf') else [d['archive']] if isinstance(d.get('archive'),str) and d['archive'].lower().endswith('.pdf') else d.get('local_files',[])
  if isinstance(fs,str):fs=[fs]
  if isinstance(sha,str) and len(sha)==64:
   for f in fs:
    if isinstance(f,str) and f.lower().endswith('.pdf') and (ROOT/f).is_file():files.setdefault(f,{'local_file':f,'recorded_sha256':sha,'metadata_files':[]})['metadata_files'].append(source)
  for v in d.values():
   if isinstance(v,(list,dict)):visit(v,source)
for p in sorted(set(paths)):
 try:visit(json.loads(p.read_text()),str(p.relative_to(ROOT)))
 except (ValueError,UnicodeError):pass
# Register manifest has actual hash, file and full text for all1558records.
reg=json.loads((BASE/'register-archive-manifest.json').read_text())['records'];reg_by_path=collections.defaultdict(list)
for r in reg:reg_by_path[r['local_file']].append(r['id'])
def job(r):
 p=ROOT/r['local_file'];sha=hashlib.sha256(p.read_bytes()).hexdigest();d=dict(r,sha256=sha,recorded_hash_matches=sha==r['recorded_sha256'])
 if not p.read_bytes()[:5]==b'%PDF-':return dict(d,state='not_PDF')
 tx=p.with_suffix('.txt')
 if not tx.exists():
  tx=OUT/(sha+'.txt')
  if not tx.exists():subprocess.run(['pdftotext','-layout',str(p),str(tx)],capture_output=True,timeout=60)
 if not tx.exists():return dict(d,state='no_extracted_text')
 raw=tx.read_text(errors='replace');norm=''.join(raw.split());pages=raw.split('\f');d.update(text_file=str(tx.relative_to(ROOT)),normalized_text_sha256=hashlib.sha256(norm.encode()).hexdigest(),normalized_characters=len(norm),extracted_pages=raw.count('\f'),low_text_pages=sum(len(''.join(x.split()))<30 for x in pages[:raw.count('\f')]),state='full_extraction_fingerprinted_not_read')
 return d
rows=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
 for i,r in enumerate(ex.map(job,files.values()),1):
  rows.append(r)
  if i%1000==0:print('fingerprinted',i,'/',len(files),flush=True)
bytext=collections.defaultdict(list)
for r in rows:
 if r.get('normalized_characters',0)>=500:bytext[r['normalized_text_sha256']].append(r)
matches=[]
for txhash,group in bytext.items():
 registered=[r for r in group if r['local_file'] in reg_by_path];other=[r for r in group if r['local_file'] not in reg_by_path]
 if registered and other:matches.append({'normalized_text_sha256':txhash,'registered_records':sorted({sid for r in registered for sid in reg_by_path[r['local_file']]}),'register_paths':[r['local_file'] for r in registered],'other_archive_paths':[r['local_file'] for r in other],'all_extracted_page_counts':sorted({r['extracted_pages'] for r in group}),'low_text_page_counts':sorted({r['low_text_pages'] for r in group}),'state':'mirror_candidate_requires_authorship_version_visual_check'})
out={'id':'global-register-fulltext-mirror-candidates','as_of_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'archived_PDF_paths_fingerprinted':len(rows),'full_text_candidate_groups':len(matches),'register_records_in_candidate_groups':len({s for g in matches for s in g['registered_records']}),'minimum_normalized_characters':500,'groups':matches,'fingerprints':rows,'limits':['Equality after whitespace removal is only a candidate mirror relation; scans, omitted covers, redactions, repeated templates and partial text layers require visual/authorship checks.','Full extraction is not a full read or factual screen. No admission or auto-merge is made to the reading pool.','Archive metadata can represent drafts, government replies and primary evidence rather than external submissions.','No absent-match inference, no final submission denominator or prevalence estimate.']}
(BASE/'global-register-text-mirror-candidates.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print({k:out[k] for k in ['archived_PDF_paths_fingerprinted','full_text_candidate_groups','register_records_in_candidate_groups']})
