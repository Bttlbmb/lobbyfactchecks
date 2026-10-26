import json,re,concurrent.futures,urllib.parse
from bs4 import BeautifulSoup
from crawl_coverage import fetch,BASE,absu
from coverage_processes import process
INDEXES={'health':'https://www.bundestag.de/ausschuesse/gesundheit/anhoerungen','labour':'https://www.bundestag.de/ausschuesse/a11_arbeit_soziales/anhoerungen','family':'https://www.bundestag.de/ausschuesse/a13_Bildung-Familie-Senioren-Frauen-und-Jugend/OeffentlicheSitzungen','research':'https://www.bundestag.de/ausschuesse/forschung/sitzungen'}
allout=[]
for name,u in INDEXES.items():
 html,meta=fetch(u);s=BeautifulSoup(html,'html.parser');section=s.find(attrs={'data-dataloader-url':True});urls=[];pages=[];entries={}
 if not section:allout.append({'committee':name,'url':u,'error':'No data-loader found','meta':meta});continue
 endpoint=absu(u,section['data-dataloader-url']);frag,fmeta=fetch(endpoint);fs=BeautifulSoup(frag,'html.parser');p=fs.select_one('[data-hits]');total=int(p['data-hits']) if p else len(fs.select('a[href]'));limit=int(section.get('data-limit','10'))
 urls=[endpoint]+[endpoint+'?offset='+str(i)+'&limit='+str(limit) for i in range(limit,total,limit)]
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
  for pu,(h,pm) in zip(urls,ex.map(fetch,urls)):
   so=BeautifulSoup(h,'html.parser');links=[]
   for a in so.select('.bt-listenteaser a[href]'):
    href=absu(u,a['href']);par=a.find_parent(class_='bt-listenteaser');date=par.find('h4');entries[href]={'url':href,'title':a.get_text(' ',strip=True),'hearing_date_label':date.get_text(' ',strip=True) if date else None,'index_page':pu,'committee':name};links.append(href)
   pm['hearing_links']=links;pages.append(pm)
 objs=list(entries.values());print(name,'expected',total,'entries',len(objs),flush=True)
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:ps=list(ex.map(process,objs))
 allout.append({'committee':name,'index_url':u,'index_meta':meta,'index_fragments':pages,'index_claimed_count':total,'distinct_hearing_entries':len(objs),'index_complete':len(objs)==total,'hearing_pages':ps})
 (BASE/'coverage-bundestag.json').write_text(json.dumps({'retrieved_at':'2026-10-25','time_window':{'submission_date_from':'2026-07-25','submission_date_through':'2026-10-24'},'committees':allout,'limits':'All current21st-legislature hearing-index entries collected, including futurehearings. Hearingdates/publicationdates are not submissiondates. Links and nearestheading classification only; bundle authors and documentdates requireverification. No substantive review claimed.'},ensure_ascii=False,indent=2)+'\n')
