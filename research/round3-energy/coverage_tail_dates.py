"""Extract first/last date metadata; does not amount to substantive reading."""
import concurrent.futures
import datetime
import json
import pathlib
import re
import subprocess

BASE = pathlib.Path(__file__).resolve().parents[2]
R = BASE / 'research/round3-energy'
rows = json.loads((R / 'coverage-ministry-date-candidates.json').read_text())
months = {'Januar':1,'Februar':2,'März':3,'April':4,'Mai':5,'Juni':6,'Juli':7,'August':8,'September':9,'Oktober':10,'November':11,'Dezember':12}
pattern = re.compile(r'(?<!\d)(?:(\d{1,2})\.(\d{1,2})\.(20\d{2})|(\d{1,2})\.\s*('+'|'.join(months)+r')\s*(20\d{2}))(?!\d)')

def one(source):
    row = {'id':source['id'],'title':source['title'],'process':source['process'],'source_file':source['local_file'],'depth':'metadata_only','screened_substantively':False,'date_verified':False}
    p = BASE / source['local_file']
    try:
        info = subprocess.run(['pdfinfo',str(p)],capture_output=True,text=True,timeout=15)
        n = int(re.search(r'^Pages:\s+(\d+)',info.stdout,re.M).group(1))
        first = max(1,n-1)
        dest = p.with_suffix('.last2.txt')
        if n<=2:
            text = pathlib.Path(source['metadata_text_file']).read_text()
            dest = pathlib.Path(source['metadata_text_file'])
            first = 1
        else:
            if not dest.exists():
                subprocess.run(['pdftotext','-f',str(first),'-l',str(n),'-layout',str(p),str(dest)],capture_output=True,timeout=30)
            text = dest.read_text(errors='replace')
        row.update(physical_pages=n,metadata_page_start=first,metadata_page_end=n,metadata_text_file=str(dest.relative_to(BASE)) if dest.is_absolute() else str(dest),date_candidates=[])
        for m in pattern.finditer(text):
            try:
                d = datetime.date(int(m[3]),int(m[2]),int(m[1])) if m[3] else datetime.date(int(m[6]),months[m[5]],int(m[4]))
            except ValueError:
                continue
            row['date_candidates'].append({'raw':m.group(),'iso':str(d),'pdf_page':first+text[:m.start()].count('\f'),'context':text[max(0,m.start()-80):m.end()+100].replace('\n',' '),'in_window':datetime.date(2026,7,25)<=d<=datetime.date(2026,10,24)})
        row['window_date_candidate'] = any(x['in_window']for x in row['date_candidates'])
        row['status'] = 'metadata_extracted_not_read'
    except Exception as e:
        row.update(status='failed',error=str(e))
    return row

with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
    out = list(ex.map(one,rows))
(R/'coverage-ministry-tail-date-candidates.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'rows':len(out),'failed':sum(x['status']=='failed'for x in out),'window_date_candidates':sum(x.get('window_date_candidate',False)for x in out),'eligibility_claim':'none; dates require manual attribution'}))
