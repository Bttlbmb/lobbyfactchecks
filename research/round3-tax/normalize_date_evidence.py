"""Keep date evidence verbatim from archived text, without changing dates or IDs."""
from pathlib import Path
import json,re
BASE=Path(__file__).parent
months={'januar':1,'februar':2,'märz':3,'maerz':3,'april':4,'mai':5,'juni':6,'juli':7,'august':8,'september':9,'oktober':10,'november':11,'dezember':12}
pat=re.compile(r'\b(\d{1,2})\.\s*(?:(\d{1,2})\s*\.\s*(\d{2,4})|([A-Za-zÄÖÜäöü]+)\s*(20\d{2}))\b')
def iso(m):
 day,mon,year,word,year2=m.groups()
 if mon:year=int(year);year=year+2000 if year<100 else year;mon=int(mon)
 else:year=int(year2);mon=months.get(word.lower(),0)
 return f'{year:04d}-{mon:02d}-{int(day):02d}'
for name in ['coverage-bt-response-links.json','coverage-bmds-responses.json','coverage-bmvg-all-response-links.json','coverage-bmvg-responses.json']:
 p=BASE/name;d=json.loads(p.read_text())
 for r in d['documents']:
  if not r.get('date') or not r.get('date_evidence') or not r.get('text_file'):continue
  page=r.get('date_locator',{}).get('pdf_page')
  if not page:continue
  pages=Path(r['text_file']).read_text(errors='replace').split('\f');text=pages[page-1]
  if len(r['date'])==10:
   matches=[m for m in pat.finditer(text) if iso(m)==r['date']]
   if matches:r['date_evidence']['fragment']=matches[0].group()
  else:
   mon=int(r['date'][5:7]);year=r['date'][:4];words=[w for w,n in months.items() if n==mon]
   matches=list(re.finditer(r'\b(?:'+'|'.join(words)+r')\s*'+year+r'\b',text,re.I))
   if matches:r['date_evidence']['fragment']=matches[0].group()
 p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
