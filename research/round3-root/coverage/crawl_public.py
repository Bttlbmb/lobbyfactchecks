"""Read-only public-page census. Only follows links actually exposed by source HTML."""
import pathlib,json,subprocess,hashlib,datetime,concurrent.futures,urllib.parse,re,time
from html.parser import HTMLParser
BASE=pathlib.Path(__file__).resolve().parent
class Links(HTMLParser):
 def __init__(self):super().__init__();self.out=[];self.url=None;self.text=[]
 def handle_starttag(self,t,a):
  if t=='a':self.url=dict(a).get('href');self.text=[]
 def handle_data(self,s):
  if self.url:self.text.append(s)
 def handle_endtag(self,t):
  if t=='a' and self.url:self.out.append({'url':self.url,'text':' '.join(' '.join(self.text).split())});self.url=None

def links(path,base=''):
 p=Links();p.feed(path.read_text(errors='replace'));return [dict(x,url=urllib.parse.urljoin(base,x['url'])) for x in p.out]
def fetch(item):
 url=item['url'];name=item.get('name',hashlib.sha256(url.encode()).hexdigest()[:18]+'.html');path=BASE/'sources'/name
 if path.exists() and path.stat().st_size>0:return dict(item,local_file=str(path.relative_to(BASE.parent.parent.parent)),cached=True,bytes=path.stat().st_size)
 r=subprocess.run(['curl','-sS','-L','--max-time','45','--retry','1','--write-out','%{http_code}','--output',str(path),url],capture_output=True,text=True)
 out=dict(item,local_file=str(path.relative_to(BASE.parent.parent.parent)),http_status=r.stdout[-3:],returncode=r.returncode,bytes=path.stat().st_size if path.exists() else 0,retrieved_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
 if path.exists():out['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
 return out

def main():
 master=BASE/'sources/bmjv-index.html';current=BASE/'sources/bmjv-process-search.html'
 seed=next(x for x in links(current) if x['text']=='50 Ergebnisse pro Seite');seed['name']='bmjv-current-50-1.html'
 a=fetch(seed)
 first=links(BASE/'sources'/seed['name'],seed['url'])
 pages={x['url']:x for x in first if 'gtp=' in x['url'] and (x['text'].isdigit() or not x['text'])}
 pages={u:dict(x,name='bmjv-current-page-'+str(i)+'.html') for i,(u,x) in enumerate(pages.items(),2)}
 records=[a]
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:records+=list(ex.map(fetch,pages.values()))
 process={}
 for r in records:
  for x in links(BASE.parent.parent.parent/r['local_file'],r['url']):
   if '/SharedDocs/Gesetzgebungsverfahren/DE/' in x['url']:
    u=x['url'].split('?')[0]
    if u not in process or len(x['text'])>len(process[u]['text']):process[u]=dict(x,url=u,index_source=r['local_file'])
 (BASE/'bmjv-current-processes.json').write_text(json.dumps(list(process.values()),ensure_ascii=False,indent=2)+'\n')
 (BASE/'bmjv-index-fetch-log.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
 print('processes',len(process),flush=True)
 jobs=[dict(x,name='bmjv-process-'+hashlib.sha256(x['url'].encode()).hexdigest()[:14]+'.html') for x in process.values()]
 results=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
  for r in ex.map(fetch,jobs):
   results.append(r)
   (BASE/'bmjv-process-fetch-log.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
 print('retrieved',len(results),flush=True)
if __name__=='__main__':main()
