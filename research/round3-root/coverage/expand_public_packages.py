"""Enumerate and safely archive PDF members of public consultation ZIPs."""
import json,pathlib,hashlib,zipfile,subprocess,concurrent.futures
BASE=pathlib.Path(__file__).resolve().parent;ROOT=BASE.parent.parent.parent;OUT=BASE/'package-members';OUT.mkdir(exist_ok=True)
parents=[r for r in json.load(open(BASE/'root-statement-resource-archive.json'))['records'] if r.get('format')=='zip' and r.get('archive_status')=='archived_not_screened']
jobs=[];other=[]
for r in parents:
 with zipfile.ZipFile(ROOT/r['local_file']) as z:
  for m in z.infolist():
   if m.is_dir():continue
   d={'parent_url':r['url'],'parent_archive':r['local_file'],'parent_sha256':r['sha256'],'member_name':m.filename,'member_bytes_declared':m.file_size,'channel':r['channel'],'process_url':r.get('process_url'),'process_title':r.get('process_title'),'screening_status':'not_screened'}
   if not m.filename.lower().endswith('.pdf') or m.file_size>100_000_000:d['status']='non_pdf_or_size_limit';other.append(d);continue
   key=hashlib.sha256((r['sha256']+'\n'+m.filename).encode()).hexdigest()[:20];p=OUT/(key+'.pdf')
   if not p.exists():p.write_bytes(z.read(m))
   jobs.append((d,p))
def process(job):
 d,p=job;b=p.read_bytes();d.update(local_file=str(p.relative_to(ROOT)),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
 if not b.startswith(b'%PDF-'):d['status']='not_valid_pdf';return d
 d['status']='archived_not_screened';tx=p.with_suffix('.txt')
 if not tx.exists():subprocess.run(['pdftotext','-layout',str(p),str(tx)],capture_output=True)
 if tx.exists():d.update(text_file=str(tx.relative_to(ROOT)),extracted_pages=tx.read_text(errors='replace').count('\f'))
 return d
rows=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
 for i,r in enumerate(ex.map(process,jobs),1):
  rows.append(r)
  if i%100==0:print(i,'/',len(jobs),flush=True)
out={'parent_ZIP_urls':len(parents),'PDF_member_occurrences':len(rows),'records':rows,'other_members':other,'limits':'Members are resources, not necessarily distinct authored submissions. Annexes, official replies, copies and versions remain unadjudicated. No member extraction is a content screen.'}
(BASE/'root-package-members.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print('done',len(parents),'ZIPs',len(rows),'PDFmembers',flush=True)
