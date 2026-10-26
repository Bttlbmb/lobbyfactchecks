import gzip
import hashlib
import json
import pathlib
import re
import urllib.request
from bs4 import BeautifulSoup

BASE=pathlib.Path(__file__).resolve().parent
jobs=json.loads((BASE/'document-api-jobs.json').read_text())
all_rows=[]
pages=[]
months={'Januar':1,'Februar':2,'März':3,'April':4,'Mai':5,'Juni':6,'Juli':7,'August':8,'September':9,'Oktober':10,'November':11,'Dezember':12}
def parsed(s):
    m=re.fullmatch(r'(\d+)\. (\w+) (\d{4})',s)
    return f'{int(m[3]):04}-{months[m[2]]:02}-{int(m[1]):02}' if m else None

for job in jobs:
    endpoint=job['url'].split('?')[0]
    for offset in range(0,1000,10):
        url=endpoint+f'?offset={offset}&limit=10'
        row={'url':url,'committee':job['ministry'],'offset':offset}
        file=BASE/'sources'/f"{job['id'].rsplit('-',1)[0]}-{offset:04}.html"
        try:
            with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=35) as response:blob=response.read()
            if blob.startswith(b'\x1f\x8b'):blob=gzip.decompress(blob)
            file.write_bytes(blob)
            row.update(local_file=str(file.relative_to(BASE.parents[1])),sha256=hashlib.sha256(blob).hexdigest(),access='retrieved')
            soup=BeautifulSoup(blob,'html.parser')
            table=soup.select_one('template[data-js-document-results="table"]')
            trs=table.find_all('tr') if table else soup.find_all('tr')
            row['rows']=len(trs)
            dates=[]
            for n,tr in enumerate(trs,1):
                cells=[c.get_text(' ',strip=True,types=None) for c in tr.find_all('td')]
                a=tr.find('a',href=True)
                if len(cells)<4 or not a:continue
                date=parsed(cells[0]);dates.append(date)
                title=a.find('span').get_text(' ',strip=True,types=None) if a.find('span') else a.get_text(' ',strip=True,types=None)
                all_rows.append(dict(committee=job['ministry'],publication_date=date,publication_date_label=cells[0],title=title,document_type=cells[3],url=a['href'],source_archive=row['local_file'],row=n,date_basis='index publication date only; not verified submission date',depth='metadata_only'))
            row['dates']=dates;pages.append(row)
            print(job['ministry'],offset,len(trs),dates[0] if dates else None,dates[-1] if dates else None,flush=True)
            if not trs or any(d and d<'2026-07-25' for d in dates):
                row['stop_reason']='reached first page crossing below publication-window start; dates are not submission dates'
                break
        except Exception as exc:
            row.update(access='failed',error=str(exc));pages.append(row);break
(BASE/'coverage-bt-document-publication-index.json').write_text(json.dumps({'window':{'from':'2026-07-25','through':'2026-10-24'},'pages':pages,'records':all_rows,'limitations':['Publication-date census complements hearing-page census; it is not by itself a submission-date population.','Some hearing response PDFs are absent from the general committee document feed.','Pagination stops at the first publication page crossing below 25 July; older-posted documents separately captured from all 50 hearing pages remain available for date checks.']},ensure_ascii=False,indent=2)+'\n')
