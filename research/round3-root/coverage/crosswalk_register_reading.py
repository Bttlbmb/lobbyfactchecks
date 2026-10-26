"""Positive byte-identity links to actual reading records; no negative inference."""
import pathlib,json,hashlib,collections,datetime
ROOT=pathlib.Path(__file__).resolve().parents[3];BASE=pathlib.Path(__file__).resolve().parent
pool=json.loads((ROOT/'data/screening-pool.json').read_text())['documents'];reg=json.loads((BASE/'register-archive-manifest.json').read_text())['records']
uses=collections.defaultdict(set)
for r in pool:
 if r['included_in_documented_pool']:
  for f in r['local_files']:uses[f].add(r['id'])
byhash=collections.defaultdict(list)
for r in pool:
 if not r['included_in_documented_pool']:continue
 for f in r['local_files']:
  p=ROOT/f
  if len(uses[f])>1 or not p.is_file() or p.suffix.lower()!='.pdf':continue
  b=p.read_bytes()
  if not b.startswith(b'%PDF-'):continue
  byhash[hashlib.sha256(b).hexdigest()].append({'reading_unit_id':r['id'],'depth':r['depth'],'document_kind':r['document_kind'],'external_submission':r.get('external_submission'),'local_file':f,'evidence':r['screening_evidence']})
rows=[]
for r in reg:
 matches=byhash.get(r.get('sha256'),[])
 if matches:rows.append({'register_id':r['id'],'register_sha256':r['sha256'],'reading_matches':matches})
out={'id':'register-positive-reading-links','as_of_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'register_records_considered':len(reg),'records_with_positive_byte_identity_link':len(rows),'records_with_full_author_reading_unit_link':sum(any(m['depth'] in ['full_submission','full_text_ocr'] for m in r['reading_matches']) for r in rows),'records':rows,'limits':['Positive byte-identical links only; failure to match does not establish a record unread because covers, scans and PDF metadata can differ.','Reading depths retain their original meaning: full author text, selected passages or keyword triage; an attached draft annex may not have been read.','Shared multi-author containers are excluded as automatic links. Authored packages can have multiple files and delivery events.','These are SG disclosure records, not distinct eligible external submission versions. Government/decline/public-role qualifications remain attached.','No national coverage or prevalence percentage is calculated.']}
(BASE/'register-positive-reading-links.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print({k:v for k,v in out.items() if isinstance(v,int)})
