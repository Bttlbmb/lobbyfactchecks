import json,pathlib,hashlib,re,urllib.parse
from bs4 import BeautifulSoup
BASE=pathlib.Path(__file__).resolve().parent;ROOT=BASE.parent.parent.parent
def save(n,x):(BASE/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
resources=[]
for source in ['bmjv-process-fetch-log.json','bmjv-all-archived-process-fetch-log.json','bmleh-all-process-fetch-log.json']:
 for r in json.load(open(BASE/source)):
  s=BeautifulSoup((ROOT/r['local_file']).read_bytes(),'html.parser');h=s.select_one('main h1, h1.c-intro__headline') or s.find('h1');title=h.get_text(' ',strip=True) if h else ''
  for a in s.select('a[href]'):
   u=urllib.parse.urljoin(r['url'],a['href']);t=a.get_text(' ',strip=True)
   if not (re.search(r'\.(pdf|zip|docx?)(\?|$)',u,re.I) or 'publicationFile' in u):continue
   kind='statement_candidate' if re.search(r'stellungnahme|gutachten|stellungn\.|\bstn\b',t+' '+u,re.I) else 'other_resource_unadjudicated'
   resources.append({'url':u,'label':t,'process_url':r['url'],'process_title':title,'channel':'BMJV' if 'bmjv' in source else 'BMLEH','page_archive':r['local_file'],'kind':kind,'screening_status':'not_screened'})
for r in json.load(open(BASE/'bt-root-hearing-resources.json')):resources.append(dict(r,channel='Bundestag'))
for table in json.load(open(BASE/'bt-root-document-publication-index.json'))['tables']:
 for r in table['records']:
  resources.append(dict(r,channel='Bundestag_document_publication',page_archive=r['source_archive'],process_title=r['committee'],kind='statement_candidate' if re.search(r'stellungnahme|gutachten',r['document_type']+' '+r['title'],re.I) else 'other_resource_unadjudicated'))
resources.extend(json.load(open(BASE/'bkm-resource-inventory.json')))
for r in json.load(open(BASE/'bmi-browser-process-records.json')):
 for a in r['resource_links']:
  u=a['url'];t=a['text']
  if re.search(r'\.(pdf|zip|docx?)(\?|$)',u,re.I) or 'publicationFile' in u:
   resources.append({'url':u,'label':t,'process_url':r['url'],'process_title':r['page_title'],'channel':'BMI','page_archive':r['local_file'],'kind':'statement_candidate' if re.search(r'stellungnahme|gutachten|stellungn\.|\bstn\b',t+' '+u,re.I) else 'other_resource_unadjudicated','screening_status':'not_screened'})
save('root-all-observed-resources.json',resources)
queue={}
for r in resources:
 if r['kind']=='statement_candidate':
  u=r['url'];queue.setdefault(u,dict(r,occurrences=[]))['occurrences'].append({k:r.get(k) for k in ['process_url','hearing_url','page_archive','label']})
save('root-statement-resource-queue.json',list(queue.values()))
print('resource occurrences',len(resources),'statement resource URLs',len(queue))
