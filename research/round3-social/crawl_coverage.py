import requests,json,pathlib,re,time,hashlib,concurrent.futures,urllib.parse,sys
from bs4 import BeautifulSoup
BASE=pathlib.Path('research/round3-social');CACHE=BASE/'coverage-html';CACHE.mkdir(exist_ok=True)
HEAD={'User-Agent':'Mozilla/5.0 (compatible; public-legislative-research/1.0)'}
def fetch(url):
 key=hashlib.sha256(url.encode()).hexdigest()[:16];p=CACHE/(key+'.html');mp=CACHE/(key+'.json')
 if p.exists() and mp.exists():return p.read_text(),json.loads(mp.read_text())
 try:
  r=requests.get(url,timeout=25,headers=HEAD);meta={'url':url,'resolved_url':r.url,'status':r.status_code,'retrieved_at':'2026-10-25','archive':str(p),'content_type':r.headers.get('Content-Type')};p.write_text(r.text);mp.write_text(json.dumps(meta));return r.text,meta
 except Exception as e:return '',{'url':url,'error':str(e),'retrieved_at':'2026-10-25'}
def absu(url,h):return urllib.parse.urljoin(url,h)
def bmg():
 url='https://www.bundesgesundheitsministerium.de/service/gesetze-und-verordnungen';pages=[];procs={};visited=set()
 while url and url not in visited:
  visited.add(url);html,meta=fetch(url);s=BeautifulSoup(html,'html.parser');links=[]
  for a in s.select('a[href]'):
   if '/service/gesetze-und-verordnungen/detail/' in a['href']:
    u=absu(url,a['href']);item=a.find_parent('li') or a.find_parent('article') or a.parent.parent.parent
    procs[u]={'url':u,'title':a.get_text(' ',strip=True),'index_text':item.get_text(' ',strip=True),'index_page':url};links.append(u)
  meta['process_links']=links;pages.append(meta)
  nxt=next((a for a in s.select('a[href]') if a.get_text(' ',strip=True)=='Nächste Seite'),None);url=absu(url,nxt['href']) if nxt else None
  if len(pages)>30:break
 return {'authority':'BMG','index_pages':pages,'processes':list(procs.values()),'index_complete':not bool(url),'index_limits':'Index last-stand dates are not submission dates.'}
def bmas():
 start='https://www.bmas.de/DE/Service/Gesetze-und-Gesetzesvorhaben/gesetze-und-gesetzesvorhaben.html';html,meta=fetch(start);s=BeautifulSoup(html,'html.parser');nexttag=s.select_one('pp-pagination-item[data-slot="pp-pagination-item-next"][href]');last=s.select_one('pp-pagination-item[data-slot="pp-pagination-item-skip-end"][href]');lastn=40
 uris=[start]
 if nexttag:
  u=absu(start,nexttag['href']);uris +=[re.sub(r'%253D2(?:$|&)',lambda m:'%253D'+str(n)+('&' if m.group(0).endswith('&') else ''),u) for n in range(2,lastn+1)]
 pages=[];procs={}
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
  for url,(html,meta) in zip(uris,ex.map(fetch,uris)):
   so=BeautifulSoup(html,'html.parser');links=[]
   for a in so.select('pp-link[href]'):
    h=a['href']
    if 'https://www.bmas.de/DE/Service/Gesetze-und-Gesetzesvorhaben/' in h:
     item=a.find_parent('pp-teaser') or a.parent
     title=(str(a.find('h3').string).strip() if a.find('h3') and a.find('h3').string else None) or a.get('link-aria-label') or a.get('title') or item.get_text(' ',strip=True)[:250]
     procs[h]={'url':h,'title':title,'index_text':item.get_text(' ',strip=True),'index_page':url};links.append(h)
   meta['process_links']=links;pages.append(meta)
 return {'authority':'BMAS','index_pages':pages,'processes':list(procs.values()),'index_complete':len(pages)==40 and all(x.get('status')==200 for x in pages),'index_limits':'All40 indexed pages fetched using observed pagination parameter; duplicate page content and total must be checked.'}
def family():
 start='https://www.bmbfsfj.bund.de/bmbfsfj/ministerium/gesetze';html,meta=fetch(start);s=BeautifulSoup(html,'html.parser');f=next(f for f in s.select('form') if '72646!search' in f.get('action',''));state=f.find('input',attrs={'name':'state'})['value'];uris=[absu(start,f['action']).split('#')[0]+'?'+urllib.parse.urlencode({'state':state,'hitsPerPage':'20','pageNum':str(i)}) for i in range(4)];procs={};pages=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
  for u,(html,meta) in zip(uris,ex.map(fetch,uris)):
   so=BeautifulSoup(html,'html.parser');links=[]
   for h3 in so.select('h3'):
    for a in h3.select('a[href]'):
     if 'search' not in a['href']:
      h=absu(start,a['href']);item=a.find_parent('li') or a.parent;procs[h]={'url':h,'title':a.get_text(' ',strip=True),'index_text':item.get_text(' ',strip=True),'index_page':u};links.append(h)
   meta['process_links']=links;pages.append(meta)
 return {'authority':'BMBFSFJ','index_pages':pages,'processes':list(procs.values()),'index_complete':len(procs)==65,'index_limits':'Four20-result pages from observedsearch form, compared with65 index total.'}
if __name__=='__main__':
 methods={'bmg':bmg,'bmas':bmas,'family':family};name=sys.argv[1];d=methods[name]();out=BASE/('coverage-index-'+name+'.json');out.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');print(name,'pages',len(d['index_pages']),'processes',len(d['processes']),'complete',d['index_complete'])
