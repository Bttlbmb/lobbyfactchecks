"""OCR first two pages of sparse PDFs solely to find date candidates."""
import concurrent.futures
import datetime
import json
import pathlib
import re
import subprocess
import tempfile

BASE = pathlib.Path(__file__).resolve().parents[2]
R = BASE / 'research/round3-energy'
rows = json.loads((R / 'coverage-ministry-date-candidates.json').read_text())
rows = [x for x in rows if x.get('metadata_readability') == 'sparse_text_requires_visual_or_ocr_date_check']
scratch = R / 'tmp/pdfs'
scratch.mkdir(parents=True, exist_ok=True)
months = {'Januar':1,'Februar':2,'März':3,'April':4,'Mai':5,'Juni':6,'Juli':7,'August':8,'September':9,'Oktober':10,'November':11,'Dezember':12}
pattern = re.compile(r'(?<!\d)(?:(\d{1,2})\.\s*(\d{1,2})\.\s*(20\d{2})|(\d{1,2})\.\s*('+'|'.join(months)+r')\s*(20\d{2}))(?!\d)')

def one(source):
    item = {'id':source['id'], 'source_file':source['local_file'], 'title':source['title'], 'process':source['process'], 'depth':'metadata_only', 'screened_substantively':False, 'submission_date_verified':False}
    target = BASE / source['local_file']
    output = target.with_suffix('.first2.ocr.txt')
    try:
        if not output.exists():
            with tempfile.TemporaryDirectory(dir=scratch) as temp:
                prefix = pathlib.Path(temp) / 'page'
                p = subprocess.run(['pdftoppm','-f','1','-l','2','-scale-to','1800','-png',str(target),str(prefix)], capture_output=True, timeout=60)
                if p.returncode:
                    raise RuntimeError(p.stderr.decode(errors='replace')[:300])
                texts = []
                for image in sorted(pathlib.Path(temp).glob('page-*.png')):
                    p = subprocess.run(['tesseract',str(image),'stdout','-l','eng','--psm','3'], capture_output=True, timeout=90)
                    texts.append(p.stdout.decode(errors='replace'))
                output.write_text('\n\f\n'.join(texts))
        text = output.read_text()
        item.update(ocr_file=str(output.relative_to(BASE)), ocr_characters=len(text.strip()), status='ocr_extracted_not_read', date_candidates=[])
        for m in pattern.finditer(text):
            try:
                date = datetime.date(int(m[3]),int(m[2]),int(m[1])) if m[3] else datetime.date(int(m[6]),months[m[5]],int(m[4]))
            except ValueError:
                continue
            item['date_candidates'].append({'raw':m.group(), 'iso':str(date), 'context':text[max(0,m.start()-80):m.end()+100].replace('\n',' '), 'in_window':datetime.date(2026,7,25)<=date<=datetime.date(2026,10,24)})
        item['window_date_candidate'] = any(x['in_window'] for x in item['date_candidates'])
    except Exception as e:
        item.update(status='ocr_failed', error=str(e))
    return item

with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
    out = list(ex.map(one, rows))
(R / 'coverage-ministry-ocr-date-candidates.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'sparse_pdfs':len(out),'ocr_failed':sum(x['status']=='ocr_failed' for x in out),'window_date_candidates':sum(x.get('window_date_candidate',False) for x in out),'eligibility_claim':'none; visual attribution still needed'}))
