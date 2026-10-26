import json,pathlib,hashlib,requests,subprocess,concurrent.futures,re,time,sys
BASE=pathlib.Path('research/round3-social');OUT=BASE/'coverage-pdfs';OUT.mkdir(exist_ok=True)
HEAD={'User-Agent':'Mozilla/5.0 (compatible; public-legislative-research/1.0)'}
def one(x):
 d=dict(x);key=hashlib.sha256(x['url'].encode()).hexdigest()[:18];p=OUT/(key+'.pdf');t=OUT/(key+'.txt');meta=OUT/(key+'.json')
 if meta.exists():return {**d,**json.load(open(meta))}
 rmeta={'url':x['url'],'collected_at':'2026-10-25','content_screening_status':'not_reviewed','reading_depth':'extracted_only_not_read'}
 try:
  r=requests.get(x['url'],headers=HEAD,timeout=35);rmeta.update(http_status=r.status_code,resolved_url=r.url,content_type=r.headers.get('Content-Type'))
  if not r.ok:raise Exception('HTTP '+str(r.status_code))
  if not r.content.startswith(b'%PDF'):raise Exception('Response is not PDF')
  p.write_bytes(r.content);rmeta.update(local_pdf=str(p),sha256=hashlib.sha256(r.content).hexdigest(),bytes=len(r.content))
  out=subprocess.run(['pdftotext','-layout',str(p),str(t)],capture_output=True,text=True,timeout=25)
  if out.returncode:raise Exception('PDF text extraction failed: '+out.stderr[:200])
  text=t.read_text(errors='replace');pages=text.split('\f');rmeta.update(local_text=str(t),pdf_pages=len(pages)-1 if not pages[-1].strip() else len(pages),extracted_characters=len(text),collection_status='archived_and_text_extracted',date_candidates=[])
  for pi in list(range(min(2,len(pages))))+([len(pages)-2] if len(pages)>3 else []):
   for line in pages[pi].splitlines():
    if re.search(r'(?<!\d)(?:\d{1,2}[.]\s*\d{1,2}[.]\s*20\d\d|\d{1,2}[.]?\s+(?:Januar|Februar|März|Maerz|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s+20\d\d)(?!\d)',line):rmeta['date_candidates'].append({'pdf_page':pi+1,'line':line.strip()[:400]})
  if not rmeta['date_candidates']:rmeta['date_status']='date_unverified_no_cover_date_extracted'
  else:rmeta['date_status']='date_candidates_require_human_verification'
 except Exception as e:rmeta.update(collection_status='retrieval_or_extraction_failed',error=str(e))
 meta.write_text(json.dumps(rmeta,ensure_ascii=False,indent=2)+'\n');return {**d,**rmeta}
if __name__=='__main__':
 src=BASE/'coverage-window-candidates.json';d=json.load(open(src));rows=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
  for i,x in enumerate(ex.map(one,d['documents'])):
   rows.append(x)
   if (i+1)%25==0:print('PDFs',i+1,flush=True)
 out={**d,'documents':rows,'collection_summary':{'attempted':len(rows),'archived':sum(x.get('collection_status')=='archived_and_text_extracted' for x in rows),'failed':sum(x.get('collection_status')=='retrieval_or_extraction_failed' for x in rows),'not_substantively_reviewed':sum(x.get('content_screening_status')=='not_reviewed' for x in rows)}}
 (BASE/'coverage-window-collected.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(out['collection_summary'])
