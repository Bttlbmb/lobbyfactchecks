import concurrent.futures,datetime,json,pathlib,re,urllib.parse,urllib.request
from bs4 import BeautifulSoup
BASE=pathlib.Path(__file__).resolve().parents[2];ROOT=BASE/'research/round3-energy';TARGET=ROOT/'sources/committee-pages';TARGET.mkdir(exist_ok=True)
months={'Januar':1,'Februar':2,'März':3,'April':4,'Mai':5,'Juni':6,'Juli':7,'August':8,'September':9,'Oktober':10,'November':11,'Dezember':12}
def date(s):
 m=re.search(r'(\d{1,2})\.\s*('+'|'.join(months)+r')\s*(\d{4})',s)
 return datetime.date(int(m[3]),months[m[2]],int(m[1]))if m else None
lower=datetime.date(2026,7,25);upper=datetime.date(2026,10,24)
def committee(k):
 home=ROOT/'sources/indexes'/f'{k}.html';s=BeautifulSoup(home.read_bytes(),'html.parser')
 endpoints=[]
 for q in s.select('[x-data]'):
  x=q.get('x-data','')
  if 'documents('in x:
   m=re.search(r'"endpoint"\s*:\s*"([^"]+)"',x)
   if m:endpoints.append(m[1])
 result={'committee':k,'home':str(home.relative_to(BASE)),'endpoints':endpoints,'pages':[],'submissions':[],'other_documents':[],'errors':[]}
 for ep in endpoints:
  for off in range(0,1000,10):
   url='https://www.bundestag.de'+ep+f'?offset={off}&limit=10';p=TARGET/f'{k}-{off:04}.html'
   try:
    if not p.exists():p.write_bytes(urllib.request.urlopen(url,timeout=30).read())
    parsed=BeautifulSoup(p.read_bytes(),'html.parser');trs=parsed.find_all('tr');dates=[]
    page={'url':url,'local_file':str(p.relative_to(BASE)),'offset':off,'rows':len(trs)};result['pages'].append(page)
    for i,tr in enumerate(trs):
     cols=tr.find_all('td');txt=[c.get_text(' ',strip=True,types=None)for c in cols];a=tr.find('a',href=True)
     if not a or len(txt)<4:continue
     d=date(txt[0]);dates.append(d) if d else None
     row={'index_publication_date_raw':txt[0],'index_publication_date':str(d)if d else None,'title':a.get_text(' ',strip=True,types=None),'url':a['href'],'document_type':txt[-1],'index_source':str(p.relative_to(BASE)),'index_row':i+1,'date_basis':'index_publication_date_only; author document date not yet verified','depth':'metadata_only','screened_substantively':False}
     if d and d>upper:row['window_state']='published_after_window'
     elif d and d<lower:row['window_state']='publication_before_window'
     else:row['window_state']='publication_in_window_author_date_unverified'
     if 'Stellungnahme'in txt[-1]:result['submissions'].append(row)
     else:result['other_documents'].append(row)
    page['earliest_date']=str(min(dates))if dates else None
    if not trs or(dates and min(dates)<lower):
     result['pagination_stop']='Firstpage whose earliest publication precedes25July2026,or emptyresponse';break
   except Exception as e:result['errors'].append({'url':url,'error':str(e)});break
 return result
with concurrent.futures.ThreadPoolExecutor(max_workers=4)as ex:out=list(ex.map(committee,['bt-energy','bt-environment','bt-transport','bt-housing']))
(ROOT/'coverage-bundestag-index-census.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps([{'committee':x['committee'],'pages':len(x['pages']),'submissions':len(x['submissions']),'errors':x['errors']}for x in out]))
