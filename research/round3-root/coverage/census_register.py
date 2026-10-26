import json,pathlib,re,urllib.parse,concurrent.futures,hashlib,datetime
from bs4 import BeautifulSoup
from crawl_public import fetch,BASE
WINDOW=['2026-07-25','2026-10-24']
path=BASE/'sources/register-window-page-1.html'
soup=BeautifulSoup(path.read_text(),'html.parser')
seed=next(a['href'] for a in soup.select('a[href]') if a.get_text(' ',strip=True)=='Seite 16')
seed=urllib.parse.urljoin('https://www.lobbyregister.bundestag.de/inhalte-der-interessenvertretung/stellungnahmengutachtensuche',seed)
parsed=urllib.parse.urlsplit(seed);qs=urllib.parse.parse_qs(parsed.query)
jobs=[]
for i in range(2,17):
 q=dict(qs);q['page']=[str(i)];u=urllib.parse.urlunsplit((parsed.scheme,parsed.netloc,parsed.path,urllib.parse.urlencode(q,doseq=True),'unused')).removesuffix('#unused')
 jobs.append({'url':u,'name':f'register-window-page-{i}.html'})
fetches=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
 for r in ex.map(fetch,jobs):
  fetches.append(r);(BASE/'register-window-fetch-log.json').write_text(json.dumps(fetches,ensure_ascii=False,indent=2)+'\n')
records=[];counts=[]
for i in range(1,17):
 p=BASE/f'sources/register-window-page-{i}.html';s=BeautifulSoup(p.read_text(errors='replace'),'html.parser')
 header=next((h.get_text(' ',strip=True) for h in s.select('h2') if 'Stellungnahmen/Gutachten (SG)' in h.get_text()),None)
 cards=s.select('.mod-common-search-result-list-item-statement');counts.append({'page':i,'records':len(cards),'header':header,'file':str(p.relative_to(BASE.parent.parent.parent))})
 for c in cards:
  details=c.select_one('a.detailsPageLink');pdf=c.select_one('a.documentLink');iv=c.select_one('.iv-name');ivlink=iv.select_one('a') if iv else None
  recipients=[]
  for li in c.select('ul.circlesOfRecipients > li'):
   date=li.find('p',recursive=False);recipients.append({'date':date.get_text(' ',strip=True) if date else None,'recipients':li.get_text(' ',strip=True),'links':[{'text':a.get_text(' ',strip=True),'url':a['href']} for a in li.select('a[href]')]})
  fields={}
  for li in c.select('.info-block > ul > li'):
   classes=li.get('class',[]);name=' '.join(x for x in classes if x!='info-block-text')
   if name not in ['iv-name','circle-of-recipients']:
    fields[name]={'text':li.get_text(' ',strip=True),'links':[{'text':a.get_text(' ',strip=True),'url':a['href']} for a in li.select('a[href]')]}
  records.append({'id':details.get_text(strip=True),'detail_url':details['href'].split('?')[0],'pdf_url':pdf['href'] if pdf else None,'pdf_label':pdf.get_text(' ',strip=True) if pdf else None,'registered_author':ivlink.get_text(' ',strip=True) if ivlink else None,'author_register_url':ivlink['href'] if ivlink else None,'registration_text':iv.get_text(' ',strip=True) if iv else None,'recipient_events':recipients,'structured_fields':fields,'index_file':str(p.relative_to(BASE.parent.parent.parent)),'collection_status':'metadata_collected','content_screening_status':'not_yet_assessed','eligibility_status':'pending_federal_legislative_process_check','date_basis':'self_reported_date_sent_to_recipient; document_date_not_yet_verified'})
ids=[r['id'] for r in records]
summary={'window_start':WINDOW[0],'window_end':WINDOW[1],'date_basis':'Lobbyregister SG-Abgabe gegenüber Adressaten; not upload date or document creation date','retrieved_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'search_url':'https://www.lobbyregister.bundestag.de/inhalte-der-interessenvertretung/stellungnahmengutachtensuche?pageSize=100&sort=FIRSTPUBLICATION_DESC&filter%5Bcircleofrecipientdates%5D%5B25.07.2026-24.10.2026%5D=true','reported_results':1558,'enumerated_records':len(records),'unique_sg_ids':len(set(ids)),'duplicate_sg_ids':[i for i in set(ids) if ids.count(i)>1],'pages':counts,'scope_limitations':['Register records are not automatically distinct documents: mirrors, joint filings, resubmissions and versions require deduplication.','A record is not automatically an eligible formal federal legislative submission: process/draft links require adjudication.','Date is registrant-reported recipient date; document signature dates and public availability dates can differ.','Current public register retrieved25October2026, not a historical snapshot fixed at24October2026.','Collection is not substantive screening. No negative factual conclusion follows from not-yet-assessed records.']}
(BASE/'register-window-records.json').write_text(json.dumps({'summary':summary,'records':records},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k!='pages'},ensure_ascii=False,indent=2));print('fields',sorted({k for r in records for k in r['structured_fields']}))
