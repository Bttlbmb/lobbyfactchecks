"""Enumerate public index fragments and observed resources; no content-screening claims."""
import json,pathlib,hashlib,concurrent.futures,urllib.parse,re
from bs4 import BeautifulSoup
from crawl_public import BASE,fetch
ROOT=BASE.parent.parent.parent
def save(name,obj):
 (BASE/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def soup(r):return BeautifulSoup((ROOT/r['local_file']).read_bytes(),'html.parser')
def batch(jobs):
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:return list(ex.map(fetch,jobs))

# Parse already archived BMJV archive pages using their actual observed path.
process={}
for r in json.load(open(BASE/'bmjv-archive-index-fetch-log.json')):
 for a in soup(r).select('a[href]'):
  u=urllib.parse.urljoin(r['url'],a['href']).split('?')[0];t=a.get_text(' ',strip=True)
  if '/SharedDocs/Gesetzgebungsarchiv/' in u and u.endswith('.html'):
   if u not in process or len(t)>len(process[u]['title']):process[u]={'url':u,'title':t,'index_source':r['local_file']}
save('bmjv-archived-processes.json',{'processes':list(process.values()),'stage':'index_enumerated_not_screened'})
jobs=[dict(x,name='bmjv-archived-process-'+hashlib.sha256(x['url'].encode()).hexdigest()[:12]+'.html') for x in process.values() if re.search(r'/202[56][_-]',x['url'])]
rs=batch(jobs);save('bmjv-archived-current-process-fetch-log.json',rs)
print('BMJV archive',len(process),'processes; recent pages',len(rs),flush=True)

# Prefer the actual page heading to repeated index "Mehr" link labels.
ps=json.load(open(BASE/'bmleh-process-inventory.json'))
lookup={r['url']:r for r in json.load(open(BASE/'bmleh-all-process-fetch-log.json'))}
for p in ps['processes']:
 r=lookup.get(p['url'])
 if r:
  ss=soup(r);h=ss.select_one('main h1, h1.c-intro__headline')
  if h:p['title']=h.get_text(' ',strip=True)
save('bmleh-process-inventory.json',ps)

# Exhaust each hearing index using its exposed data-loader and declared hit count.
fragments=[];hearings={};closure=[]
for r in json.load(open(BASE/'bt-root-hearing-index-fetch-log.json')):
 for node in soup(r).select('[data-dataloader-url]'):
  endpoint=urllib.parse.urljoin(r['url'],node['data-dataloader-url'])
  first=fetch({'url':endpoint,'committee_slug':r['committee_slug']})
  ss=soup(first);nav=ss.select_one('[data-hits]');total=int(nav['data-hits']) if nav else None
  limit=int(node.get('data-limit','10'));rows=[first]
  if total is not None:
   rows+=batch([{'url':endpoint+'?'+urllib.parse.urlencode({'offset':off,'limit':limit}),'committee_slug':r['committee_slug']} for off in range(limit,total,limit)])
  urls=set()
  for x in rows:
   ls=[]
   for a in soup(x).select('a[href]'):
    u=urllib.parse.urljoin(x['url'],a['href'])
    if re.search(r'/[^/?]*-\d+$',u) and '/ausschuesse/' in u:
     ls.append(u);urls.add(u)
     hearings[u]={'url':u,'title':a.get_text(' ',strip=True),'committee_slug':r['committee_slug'],'index_source':x['local_file']}
   x['hearing_links']=list(dict.fromkeys(ls))
  fragments+=rows
  closure.append({'committee_slug':r['committee_slug'],'endpoint':endpoint,'declared_hits':total,'unique_hearings':len(urls),'fragments':len(rows),'enumeration_closed':total is not None and len(urls)==total,'index_source':r['local_file']})
save('bt-root-hearing-fragments.json',fragments);save('bt-root-hearing-index-closure.json',closure);save('bt-root-hearings.json',list(hearings.values()))
print('BT hearing indices',len(closure),'closed',sum(x['enumeration_closed'] for x in closure),'hearings',len(hearings),flush=True)
rs=batch([dict(x,name='bt-hearing-'+hashlib.sha256(x['url'].encode()).hexdigest()[:14]+'.html') for x in hearings.values()]);save('bt-root-hearing-page-fetch-log.json',rs)
resources={}
for r in rs:
 for a in soup(r).select('a[href]'):
  u=urllib.parse.urljoin(r['url'],a['href']);t=a.get_text(' ',strip=True)
  if '.pdf' in u.lower() or '/resource/blob/' in u:
   key=(u,r['url']);resources[key]={'url':u,'label':t,'hearing_url':r['url'],'committee_slug':r['committee_slug'],'page_archive':r['local_file'],'kind':'statement_candidate' if re.search(r'Stellungnahme|Gutachten|Positionspapier|[Ss]tellungnahme',t) else 'other_resource_unadjudicated','screening_status':'not_screened'}
save('bt-root-hearing-resources.json',list(resources.values()))
print('BT observed resources',len(resources),flush=True)
