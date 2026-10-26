import concurrent.futures,gzip,hashlib,json,pathlib,re,subprocess,urllib.request,urllib.parse
from bs4 import BeautifulSoup
BASE=pathlib.Path(__file__).resolve().parent;ROOT=BASE.parents[1]
page=BASE/'sources/bmvg-reserve-statements.html';s=BeautifulSoup(page.read_text(),'html.parser')
rows=[]
for a in s.select('main a[href]'):
 if '.pdf' not in a['href'].lower():continue
 container=a.parent.parent;title=container.find('p') or container.find('h3')
 rows.append({'id':'bmvg-reserve-response-%03d'%(len(rows)+1),'ministry':'BMVg','process':'Reserveverstärkungsgesetz','process_type':'bill','source_index':'https://www.bmvg.de/de/service/gesetze-und-verordnungen/stellungnahme-gesetzentwurf-reserveverstaerkungsgesetz-6137756','source_index_archive':str(page.relative_to(ROOT)),'title':title.get_text(' ',strip=True) if title else a.get_text(' ',strip=True),'response_url':a['href'],'date':None,'date_status':'unverified','window_status':'date_unverified','depth':'inventoried_only'})
def retrieve(row):
 try:
  with urllib.request.urlopen(urllib.request.Request(urllib.parse.quote(row['response_url'],safe=':/%?=&'),headers={'User-Agent':'Mozilla/5.0'}),timeout=40) as resp:b=resp.read();row['effective_url']=resp.url
  if b.startswith(b'\x1f\x8b'):b=gzip.decompress(b)
  if not b.startswith(b'%PDF'):raise ValueError('Not a PDF; not labelled archived PDF')
  p=BASE/'sources'/(row['id']+'.pdf');p.write_bytes(b);tp=p.with_suffix('.txt');subprocess.run(['pdftotext','-layout',str(p),str(tp)],capture_output=True,check=True)
  text=tp.read_text();first='\f'.join(text.split('\f')[:2]);pattern=r'\b(?:\d{1,2}\.\s*\d{1,2}\.\s*20\d{2}|\d{1,2}\.?\s*(?:Januar|Februar|März|Maerz|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s+20\d{2})\b'
  row.update(access='retrieved',local_file=str(p.relative_to(ROOT)),text_file=str(tp.relative_to(ROOT)),sha256=hashlib.sha256(b).hexdigest(),physical_pages=len(text.split('\f'))-1,depth='extracted_only_for_date_triage',date_candidates_first_two_pages=[{'match':m.group(),'context':first[max(0,m.start()-70):m.end()+60].replace('\n',' '),'pdf_page':first[:m.start()].count('\f')+1} for m in re.finditer(pattern,first,re.I)])
 except Exception as e:row.update(access='failed',error=str(e))
 return row
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:rows=list(pool.map(retrieve,rows))
(BASE/'coverage-bmvg-responses.json').write_text(json.dumps({'window':{'from':'2026-07-25','through':'2026-10-24'},'documents':rows,'unpublished_responses':[{'author':'Deutscher Bundeswehrverband','evidence':'Official page states author did not consent to publication; content/date unavailable.'}],'limitations':['Master page publication23July2026 is not assumed to be the date of every response or its current version.','Live legislation master omits an October2026 infrastructure-acceleration process visible on homepage. Additional processes may be missing; no ministrywide completeness assertion.']},ensure_ascii=False,indent=2)+'\n')
print(len(rows),'responses',sum(r.get('access')=='retrieved' for r in rows),'retrieved')
