import json,hashlib,concurrent.futures,urllib.parse,re
from bs4 import BeautifulSoup
from crawl_public import BASE,fetch
ROOT=BASE.parent.parent.parent
jobs=[]
# BMLEH: follow the 50-result link exposed by its actual form.
s=BeautifulSoup((BASE/'sources/bmleh-process-search.html').read_text(),'html.parser')
seed=next(a['href'] for a in s.select('a[href]') if 'resultsPerPage=50' in a['href'])
r=fetch({'url':seed,'name':'bmleh-process-50-page-1.html'});pages=[r]
s=BeautifulSoup((ROOT/r['local_file']).read_text(),'html.parser')
pg={a['href'] for a in s.select('a[href]') if 'gtp=' in a['href']}
# Enumerate every observed page number by following next pages, rather than guessing a last page.
seen={seed};front=list(pg)
while front:
 todo=[u for u in front if u not in seen];front=[]
 if not todo:break
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
  rs=list(ex.map(fetch,[{'url':u,'name':'bmleh-index-'+hashlib.sha256(u.encode()).hexdigest()[:12]+'.html'} for u in todo]))
 for r in rs:
  seen.add(r['url']);pages.append(r)
  ss=BeautifulSoup((ROOT/r['local_file']).read_text(errors='replace'),'html.parser')
  for a in ss.select('a[href]'):
   if 'gtp=' in a['href'] and a['href'] not in seen:front.append(a['href'])
 (BASE/'bmleh-index-fetch-log.json').write_text(json.dumps(pages,ensure_ascii=False,indent=2)+'\n')
process={}
for r in pages:
 s=BeautifulSoup((ROOT/r['local_file']).read_text(errors='replace'),'html.parser')
 for a in s.select('a[href]'):
  u=a['href'].split('?')[0];t=a.get_text(' ',strip=True)
  if '/SharedDocs/Gesetzestexte/' in u:process[u]={'url':u,'title':t,'index_source':r['local_file'],'local_file':None,'status':'indexed_not_yet_inspected'}
(BASE/'bmleh-process-inventory.json').write_text(json.dumps({'index_pages':len(pages),'processes':list(process.values())},ensure_ascii=False,indent=2)+'\n')
jobs=[dict(x,name='bmleh-process-'+hashlib.sha256(x['url'].encode()).hexdigest()[:12]+'.html') for x in process.values() if '/21-WP/' in x['url']]
results=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
 for r in ex.map(fetch,jobs):
  results.append(r);(BASE/'bmleh-current-process-fetch-log.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
print('BMLEH indexpages/processes/21WPinspected',len(pages),len(process),len(results),flush=True)
# Root-owned parliamentary committee portals; peers handle the other assigned committees.
s=BeautifulSoup((BASE/'sources/bundestag-committees.html').read_text(),'html.parser')
root_slugs=['inneres','recht-verbraucherschutz','Landwirtschaft','a22_kultur','a20_tourismus','sport_und_ehrenamt','europa','a17_menschenrechte','a02_Petitionsausschuss','a03_auswaertiges','entwicklung','geschaeftsordnung','verteidigung','a23_digitales_staatsmodernisierung']
portals=[]
for slug in root_slugs:
 u='https://www.bundestag.de/ausschuesse/'+slug
 if any(a.get('href')=='/ausschuesse/'+slug for a in s.select('a[href]')):portals.append({'url':u,'name':'bt-committee-'+slug+'.html','committee_slug':slug})
results=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
 for r in ex.map(fetch,portals):
  results.append(r);(BASE/'bt-root-portal-fetch-log.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
print('BT rootportals',len(results),flush=True)
