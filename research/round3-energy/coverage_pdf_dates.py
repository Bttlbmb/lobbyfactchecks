"""Extract first-two-page date candidates; never automatically assert author/sent dates."""
import concurrent.futures,datetime,json,pathlib,re,subprocess
BASE=pathlib.Path(__file__).resolve().parents[2];ROOT=BASE/'research/round3-energy'
queue=json.loads((ROOT/'coverage-ministry-all-observed-pdf-queue.json').read_text())
months={'Januar':1,'Februar':2,'März':3,'April':4,'Mai':5,'Juni':6,'Juli':7,'August':8,'September':9,'Oktober':10,'November':11,'Dezember':12}
pattern=re.compile(r'(?<!\d)(?:(\d{1,2})\.(\d{1,2})\.(20\d{2})|(\d{1,2})\.\s*('+'|'.join(months)+r')\s*(20\d{2}))(?!\d)')
LOW=datetime.date(2026,7,25);HIGH=datetime.date(2026,10,24)
def one(x):
 x=dict(x);p=BASE/x['local_file']
 if not p.is_file():x['archive_state']='not_downloaded_yet';return x
 if not p.read_bytes()[:10].startswith(b'%PDF'):x['archive_state']='not_valid_pdf';return x
 f=p.with_suffix('.first2.txt')
 if not f.exists():subprocess.run(['pdftotext','-f','1','-l','2','-layout',str(p),str(f)],capture_output=True)
 t=f.read_text(errors='replace') if f.exists() else '';x['metadata_text_file']=str(f.relative_to(BASE));x['archive_state']='pdf_archived';x['date_verified']=False;x['date_candidates']=[]
 for m in pattern.finditer(t):
  try:
   d=datetime.date(int(m[3]),int(m[2]),int(m[1])) if m[3] else datetime.date(int(m[6]),months[m[5]],int(m[4]))
  except ValueError:continue
  x['date_candidates'].append({'raw':m.group(0),'iso':str(d),'context':t[max(0,m.start()-60):m.end()+70].replace('\n',' '),'within_requested_window':LOW<=d<=HIGH})
 x['has_window_date_candidate']=any(d['within_requested_window'] for d in x['date_candidates']);x['metadata_text_characters']=len(t.strip());x['metadata_readability']='text_layer_available' if len(t.strip())>150 else 'sparse_text_requires_visual_or_ocr_date_check'
 x['date_basis']='automatically extracted date candidates from first two pages only; no attribution as author/recipient date without further check'
 x['depth']='metadata_only';x['screened_substantively']=False;return x
with concurrent.futures.ThreadPoolExecutor(max_workers=4)as ex:out=list(ex.map(one,queue))
(ROOT/'coverage-ministry-date-candidates.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
(ROOT/'coverage-ministry-window-date-candidates.json').write_text(json.dumps([x for x in out if x.get('has_window_date_candidate')],ensure_ascii=False,indent=2)+'\n')
from collections import Counter
print(json.dumps({'rows':len(out),'archive_states':dict(Counter(x['archive_state']for x in out)),'has_window_date_candidate':sum(x.get('has_window_date_candidate',False)for x in out),'eligibility_claim':'none; candidates require manual attribution'},ensure_ascii=False))
