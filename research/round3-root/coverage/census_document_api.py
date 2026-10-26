"""Collect observed committee document tables, not their separate news sliders."""
import json,re,urllib.parse,concurrent.futures,pathlib
from bs4 import BeautifulSoup
from crawl_public import BASE,fetch
ROOT=BASE.parent.parent.parent
jobs=[];absent=[]
for r in json.load(open(BASE/'bt-root-portal-fetch-log.json')):
 s=BeautifulSoup((ROOT/r['local_file']).read_bytes(),'html.parser');nodes=[n for n in s.select('[x-data]') if n['x-data'].startswith('documents(')]
 if not nodes:absent.append({'committee':r['committee_slug'],'portal':r['local_file'],'status':'no_embedded_document_table_located'})
 for n in nodes:
  m=re.search(r'"endpoint"\s*:\s*"([^"]+)"',n['x-data'])
  if m:jobs.append({'committee':r['committee_slug'],'url':urllib.parse.urljoin(r['url'],m[1]),'portal':r['local_file']})
months={'Januar':1,'Februar':2,'März':3,'April':4,'Mai':5,'Juni':6,'Juli':7,'August':8,'September':9,'Oktober':10,'November':11,'Dezember':12}
def parsed(s):
 m=re.fullmatch(r'(\d+)\. (\w+) (\d{4})',s)
 return f'{int(m[3]):04}-{months[m[2]]:02}-{int(m[1]):02}' if m and m[2] in months else None
def collect(j):
 rows=[];pages=[];seen=set();stop='safety_limit_not_closed'
 for offset in range(0,5000,10):
  r=fetch({'url':j['url']+f'?offset={offset}&limit=10','committee':j['committee']});s=BeautifulSoup((ROOT/r['local_file']).read_bytes(),'html.parser');table=s.select_one('template[data-js-document-results="table"]');trs=table.find_all('tr') if table else []
  r['parsed_rows']=sum(bool(tr.find('a',href=True)) and len(tr.find_all('td'))>=4 for tr in trs);pages.append(r)
  list_view=s.select_one('template[data-js-document-results="list"]')
  if list_view and 'Leider keine Ergebnisse gefunden!' in list_view.get_text(' ',strip=True,types=None):
   r['published_no_results_state']=True
   stop='published_no_results_state'
   break
  if not trs:stop='empty_document_table';break
  signature=[]
  for i,tr in enumerate(trs,1):
   cells=[c.get_text(' ',strip=True,types=None) for c in tr.find_all('td')];a=tr.find('a',href=True)
   if len(cells)<4 or not a:continue
   u=urllib.parse.urljoin(r['url'],a['href']);signature.append(u);title=a.find('span').get_text(' ',strip=True,types=None) if a.find('span') else a.get_text(' ',strip=True,types=None)
   rows.append({'committee':j['committee'],'publication_date':parsed(cells[0]),'publication_date_label':cells[0],'title':title,'document_type':cells[3],'url':u,'source_archive':r['local_file'],'row':i,'date_basis':'index publication date, not verified submission date','screening_status':'metadata_only'})
  sig=tuple(signature)
  if sig in seen:stop='repeated_result_page_not_closed';break
  seen.add(sig)
 print(j['committee'],len(rows),'rows',len(pages),'pages',stop,flush=True)
 return {'job':j,'records':rows,'pages':pages,'stop_reason':stop,'enumeration_closed':stop in ['empty_document_table','published_no_results_state'],'limits':'All publicly returned document rows before the published no-results state. The end page contains a no-results table row, not another document. Official agendas, protocols and government correspondence are not external submissions; scope, delivery and authored versions remain unadjudicated.'}
results=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
 for d in ex.map(collect,jobs):
  results.append(d);(BASE/'bt-root-document-publication-index.json').write_text(json.dumps({'tables':results,'no_embedded_table':absent,'global_limit':'These are document-table records, not checked submissions.'},ensure_ascii=False,indent=2)+'\n')
