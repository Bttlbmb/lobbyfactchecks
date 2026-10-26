"""Archive enumerated response PDFs, without marking extraction as reading."""
import concurrent.futures
import gzip
import hashlib
import json
import pathlib
import re
import subprocess
import urllib.request
import urllib.parse

BASE=pathlib.Path(__file__).resolve().parent
ROOT=BASE.parents[1]
source=BASE/'coverage-bt-response-links.json'
data=json.loads(source.read_text())
existing={}
registries=[ROOT/'data/source-registry.json',ROOT/'research/round3-energy/coverage-bundestag-submission-metadata.json']
for reg in registries:
    for row in json.loads(reg.read_text()):
        if not row.get('url') or not row.get('local_file'):continue
        p=ROOT/row['local_file']
        if p.is_file() and p.read_bytes()[:4]==b'%PDF':existing[row['url']]=row

def archive(row):
    try:
        prior=existing.get(row['response_url'])
        if prior:
            path=ROOT/prior['local_file'];blob=path.read_bytes()
            row.update(access='reused_existing_archive',local_file=prior['local_file'])
        else:
            req=urllib.request.Request(urllib.parse.quote(row['response_url'],safe=':/%?=&'),headers={'User-Agent':'Mozilla/5.0'})
            with urllib.request.urlopen(req,timeout=40) as response:blob=response.read();row['effective_url']=response.url
            if blob.startswith(b'\x1f\x8b'):blob=gzip.decompress(blob)
            if not blob.startswith(b'%PDF'):raise ValueError('Response was not a PDF; not labelled archived source')
            path=BASE/'sources'/(row['id']+'.pdf');path.write_bytes(blob)
            row.update(access='retrieved',local_file=str(path.relative_to(ROOT)))
        row['sha256']=hashlib.sha256(blob).hexdigest()
        textpath=path.with_suffix('.txt')
        if not textpath.exists():subprocess.run(['pdftotext','-layout',str(path),str(textpath)],capture_output=True,check=True)
        row['text_file']=str(textpath.relative_to(ROOT));text=textpath.read_text(errors='replace');row['physical_pages']=len(text.split('\f'))-1
        first='\f'.join(text.split('\f')[:2]);pattern=r'\b(?:\d{1,2}\.\s*\d{1,2}\.\s*20\d{2}|\d{1,2}\.?\s*(?:Januar|Februar|März|Maerz|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s+20\d{2})\b'
        row['date_candidates_first_two_pages']=[{'match':m.group(),'context':first[max(0,m.start()-65):m.end()+70].replace('\n',' '),'pdf_page':first[:m.start()].count('\f')+1} for m in re.finditer(pattern,first,re.I)]
        row['draft_references_first_two_pages']=sorted(set(re.findall(r'\b(?:20|21)\s*/\s*\d{2,5}\b',first)))
        row['depth']='extracted_only; dates pending manual verification'
    except Exception as exc:
        row.update(access='failed',error=str(exc))
    return row

with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:data['documents']=list(pool.map(archive,data['documents']))
source.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
print('Responses',len(data['documents']))
print('Retrieved',sum(x.get('access')=='retrieved' for x in data['documents']))
print('Reused',sum(x.get('access')=='reused_existing_archive' for x in data['documents']))
print('Failures',[(x['id'],x.get('error')) for x in data['documents'] if x.get('access')=='failed'])
