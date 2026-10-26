"""Archive public disclosed PDFs for census/deduplication. Extraction is not screening."""
import pathlib,json,hashlib,subprocess,concurrent.futures,datetime,re,os,sys
BASE=pathlib.Path(__file__).resolve().parent;ROOT=BASE.parent.parent.parent
OUT=BASE/'register-pdfs';OUT.mkdir(exist_ok=True)
records=json.load(open(BASE/'register-window-records.json'))['records']
if '--preflight' in sys.argv:records=records[:5]
known={}
for s in json.load(open(ROOT/'data/source-registry.json')):
 if s.get('url') and s.get('local_file') and str(s['local_file']).lower().endswith('.pdf') and (ROOT/s['local_file']).is_file():known[s['url']]=s['local_file']
def job(r):
 sid=r['id'];u=r['pdf_url'];p=OUT/(sid+'.pdf');item={'id':sid,'url':u,'purpose':'census_archive_and_date_candidates_only','content_screening_status':'not_yet_assessed'}
 if u in known:p=ROOT/known[u];item['reused_existing_archive']=True
 elif not (p.is_file() and p.read_bytes()[:5]==b'%PDF-'):
  tmp=OUT/(sid+'.download');z=subprocess.run(['curl','-sS','-L','--cookie',str(BASE/'register-public-notice.cookies'),'--header','Accept: application/pdf','--referer','https://www.lobbyregister.bundestag.de/informationen-und-hilfe/hinweise-zum-urheberrecht','--retry','1','--max-time','55','--write-out','%{http_code}','--output',str(tmp),u],capture_output=True,text=True)
  item.update(http_status=z.stdout[-3:],returncode=z.returncode)
  if not tmp.is_file() or tmp.read_bytes()[:5]!=b'%PDF-':
   item['status']='pdf_unavailable_or_not_pdf';item['access_error']=z.stderr[-200:];return item
  tmp.replace(p)
 b=p.read_bytes();item.update(status='archived_not_screened',local_file=str(p.relative_to(ROOT)),bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),retrieved_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
 textpath=OUT/(sid+'.txt')
 if not textpath.exists():subprocess.run(['pdftotext','-layout',str(p),str(textpath)],capture_output=True)
 if textpath.exists():
  tx=textpath.read_text(errors='replace');pages=tx.split('\f');covers='\n'.join(pages[:3]+pages[-3:]);item.update(text_file=str(textpath.relative_to(ROOT)),extracted_pages=max(0,len(pages)-1),cover_and_end_date_candidates=sorted(set(re.findall(r'\b\d{1,2}\.\s*\d{1,2}\.\s*20\d{2}\b',covers))),date_candidate_limit='Automatic date strings on first3/last2pages are not verified submission dates.',readability='text_extracted_not_read' if len(tx.strip())>100 else 'ocr_or_visual_read_required')
 return item
results=[];manifest=BASE/('register-preflight-manifest.json' if '--preflight' in sys.argv else 'register-archive-manifest.json')
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
 for n,r in enumerate(ex.map(job,records),1):
  results.append(r)
  if n%20==0 or n==len(records):
   tmp=manifest.with_suffix('.json.tmp');tmp.write_text(json.dumps({'expected_records':len(records),'processed':len(results),'records':results,'not_screening':'Download and extraction do not constitute a screen.'},ensure_ascii=False,indent=2)+'\n');tmp.replace(manifest)
  if n==5 and all(x['status']!='archived_not_screened' for x in results):raise RuntimeError('First5publicPDFsfailed; stopforaccessdiagnosisratherthanbulkfetchnotices.')
  if n%100==0:print('processed',n,'/',len(records),flush=True)
print('done',len(results),'archived',sum(x['status']=='archived_not_screened' for x in results),flush=True)
