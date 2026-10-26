import concurrent.futures
import gzip
import hashlib
import json
import pathlib
import re
import subprocess
import urllib.request
from urllib.parse import urlparse

BASE = pathlib.Path(__file__).resolve().parent
pages = json.loads((BASE / 'official-page-jobs-results.json').read_text())
rows = []
for page in pages:
    if not page['id'].startswith('bmds-'):
        continue
    seq = 0
    for link in page.get('links', []):
        if not re.search(r'Stellungnahme', link['text'], re.I):
            continue
        # A Bundesrat entry is an intergovernmental procedural record, not an external response.
        if 'bundesrat' in link['text'].lower():
            continue
        seq += 1
        rows.append(dict(id=page['id']+'-response-'+str(seq).zfill(3), ministry='BMDS', process_id=page['id'], process_url=page['url'], title=link['text'], response_url=link['url'], date=None, date_status='unverified', window_status='date_unverified', depth='inventoried_only'))

def get(row):
    try:
        with urllib.request.urlopen(urllib.request.Request(row['response_url'], headers={'User-Agent':'Mozilla/5.0'}), timeout=40) as response:
            blob=response.read(); row['effective_url']=response.url; row['content_type']=response.headers.get('Content-Type')
        if blob.startswith(b'\x1f\x8b'): blob=gzip.decompress(blob)
        ext='.pdf' if blob.startswith(b'%PDF') else '.docx' if blob.startswith(b'PK') else '.retrieval.html'
        path=BASE/'sources'/(row['id']+ext);path.write_bytes(blob)
        row.update(access='retrieved' if ext in ['.pdf','.docx'] else 'unexpected_response', local_file=str(path.relative_to(BASE.parents[1])), sha256=hashlib.sha256(blob).hexdigest())
        if ext=='.pdf':
            textpath=path.with_suffix('.txt')
            subprocess.run(['pdftotext','-layout',str(path),str(textpath)],capture_output=True,check=True)
            text=textpath.read_text(errors='replace'); row['text_file']=str(textpath.relative_to(BASE.parents[1]));row['physical_pages']=len(text.split('\f'))-1
            # Candidate dates are deliberately not treated as verified submission dates.
            row['date_strings_first_two_pages']=sorted(set(re.findall(r'\b(?:\d{1,2}[.\-/]\d{1,2}[.\-/](?:20)?\d{2}|\d{1,2}\.?\s+(?:Januar|Februar|März|Maerz|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s+20\d{2})\b','\f'.join(text.split('\f')[:2]),re.I)))
    except Exception as exc:
        row.update(access='failed', error=str(exc))
    return row

with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
    output=list(pool.map(get, rows))
(BASE/'coverage-bmds-responses.json').write_text(json.dumps({'scope':'All response links on eight current BMDS process pages; dates pending manual confirmation; not a completeness claim for archived processes.','documents':output},ensure_ascii=False,indent=2)+'\n')
print('Responses',len(output),'retrieved',sum(x.get('access')=='retrieved' for x in output))
for row in output:
    print(row['id'],row.get('access'),row.get('date_strings_first_two_pages',[]),row['title'])
