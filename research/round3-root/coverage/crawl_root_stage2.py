import json,pathlib,hashlib,concurrent.futures,urllib.parse,re
from bs4 import BeautifulSoup
from crawl_public import BASE,fetch
ROOT=BASE.parent.parent.parent
# Archived/completed BMJV processes have to be enumerated separately.
s=BeautifulSoup((BASE/'sources/bmjv-index.html').read_text(),'html.parser')
archive=next(a['href'] for a in s.select('a[href]') if 'Gesetzgebungsverfahren_Archiv' in a['href'])
rr=fetch({'url':archive,'name':'bmjv-archive-first.html'});so=BeautifulSoup((ROOT/rr['local_file']).read_text(),'html.parser')
seed=next((a['href'] for a in so.select('a[href]') if a.get_text(' ',strip=True)=='50 Ergebnisse pro Seite'),archive)
pages=[];seen=set();front=[seed]
while front:
 todo=list(dict.fromkeys(u for u in front if u not in seen));front=[]
 if not todo:break
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:rs=list(ex.map(fetch,[{'url':u,'name':'bmjv-archive-index-'+hashlib.sha256(u.encode()).hexdigest()[:12]+'.html'} for u in todo]))
 for r in rs:
  seen.add(r['url']);pages.append(r);ss=BeautifulSoup((ROOT/r['local_file']).read_text(errors='replace'),'html.parser')
  for a in ss.select('a[href]'):
   if 'gtp=' in a['href'] and 'Gesetzgebungsverfahren_Archiv/' in a['href'] and a['href'] not in seen:front.append(a['href'])
 (BASE/'bmjv-archive-index-fetch-log.json').write_text(json.dumps(pages,ensure_ascii=False,indent=2)+'\n')
process={}
for r in pages:
 ss=BeautifulSoup((ROOT/r['local_file']).read_text(errors='replace'),'html.parser')
 for a in ss.select('a[href]'):
  u=a['href'].split('?')[0];t=a.get_text(' ',strip=True)
  if '/SharedDocs/Gesetzgebungsverfahren/DE/' in u and (u not in process or len(t)>len(process[u]['title'])):process[u]={'url':u,'title':t,'index_source':r['local_file']}
(BASE/'bmjv-archived-processes.json').write_text(json.dumps({'processes':list(process.values())},ensure_ascii=False,indent=2)+'\n')
print('BMJVarchived',len(pages),'indexpages',len(process),'processes',flush=True)
jobs=[dict(x,name='bmjv-archived-process-'+hashlib.sha256(x['url'].encode()).hexdigest()[:12]+'.html') for x in process.values() if '/2026_' in x['url'] or '/2025_' in x['url']]
results=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
 for r in ex.map(fetch,jobs):
  results.append(r);(BASE/'bmjv-archived-current-process-fetch-log.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
# Finish BMLEH older pages; dates remain unadjudicated until the page/response is inspected.
ps=json.load(open(BASE/'bmleh-process-inventory.json'))['processes'];jobs=[dict(x,name='bmleh-process-'+hashlib.sha256(x['url'].encode()).hexdigest()[:12]+'.html') for x in ps]
rs=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
 for r in ex.map(fetch,jobs):
  rs.append(r);(BASE/'bmleh-all-process-fetch-log.json').write_text(json.dumps(rs,ensure_ascii=False,indent=2)+'\n')
print('BMLEHpages',len(rs),flush=True)
# Two root portals added after the first job started.
extra=[]
for slug in ['verteidigung','a23_digitales_staatsmodernisierung']:extra.append(fetch({'url':'https://www.bundestag.de/ausschuesse/'+slug,'name':'bt-committee-'+slug+'.html','committee_slug':slug}))
portals=json.load(open(BASE/'bt-root-portal-fetch-log.json'))+extra
(BASE/'bt-root-portal-fetch-log.json').write_text(json.dumps(portals,ensure_ascii=False,indent=2)+'\n')
idx={}
for r in portals:
 so=BeautifulSoup((ROOT/r['local_file']).read_text(errors='replace'),'html.parser')
 for a in so.select('a[href]'):
  u=urllib.parse.urljoin(r['url'],a['href']);t=a.get_text(' ',strip=True)
  if u.startswith(r['url']+'/') and any(z in u for z in ['/anhoerungen','/sitzungen','/oeffentliche_sitzungen']) and not re.search(r'/\d+-\d+$',u):idx[u]={'url':u,'name':'bt-hearing-index-'+r['committee_slug']+'.html','committee_slug':r['committee_slug'],'label':t}
rs=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
 for r in ex.map(fetch,idx.values()):
  rs.append(r);(BASE/'bt-root-hearing-index-fetch-log.json').write_text(json.dumps(rs,ensure_ascii=False,indent=2)+'\n')
print('BThearingindexes',len(rs),flush=True)
