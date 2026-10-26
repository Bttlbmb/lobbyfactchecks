import json,re
from pathlib import Path
p=Path(__file__).parent/'coverage-bmds-responses.json';data=json.loads(p.read_text())
verified={
'frequenzverordnung-response-002':('2026-04-13','13. April 2026',1,'cover visually checked; OCR-assisted'),
'digitale-identitaetengesetz-response-022':('2026-04-14','Bremen, 14. April 2026',1,'cover visually checked; OCR-assisted'),
'digitale-identitaetengesetz-response-026':('2026-04-13','13.04.2026',1,'cover visually checked; OCR-assisted'),
'digitale-identitaetengesetz-response-002':('2026-04-15','Düsseldorf / Berlin, 15.04.2026',None,'dated closing read'),
'digitale-identitaetengesetz-response-004':('2026-04','April 2026',1,'dated cover read; day unspecified'),
'digitale-identitaetengesetz-response-008':('2026-04','April 2026',1,'dated cover read; day unspecified'),
'digitale-identitaetengesetz-response-024':('2026-04-15','Berlin, den 15.04.2026',None,'dated closing read'),
 'tkg-aenderungsgesetz-2026-response-031':('2025-08-27','Datum: 27.08.2025',1,'cover visually checked; OCR-assisted'),
 'tkg-aenderungsgesetz-2026-response-069':('2026-03-27','Karlsruhe, 27. März 2026',1,'cover visually checked; OCR-assisted'),
 'tkg-aenderungsgesetz-2026-response-091':('2026-03-30','Datum: 30.03.2026',1,'cover visually checked; OCR-assisted'),
 'tkg-aenderungsgesetz-2026-response-001':('2025-08','August 2025',1,'dated cover read; day unspecified'),
 'tkg-aenderungsgesetz-2026-response-002':('2025-08-22','Berlin/Köln, den 22. August 2025',None,'dated closing read'),
 'tkg-aenderungsgesetz-2026-response-005':('2025-07','Juli 2025',None,'dated closing read; day unspecified'),
 'tkg-aenderungsgesetz-2026-response-044':('2026-04-02','Berlin/Köln, den 2. April 2026',None,'dated closing read'),
 'tkg-aenderungsgesetz-2026-response-049':('2026-03','März 2026',1,'dated cover read; attachment to Berlin response048'),
 'tkg-aenderungsgesetz-2026-response-054':('2026-03-27','27.März 2026',1,'dated cover read'),
 'tkg-aenderungsgesetz-2026-response-060':('2026-03-27','Stuttgart, 27.3.2026',None,'dated closing read'),
 'tkg-aenderungsgesetz-2026-response-075':('2026-03','März 2026',None,'dated footer read; day unspecified'),
 'tkg-aenderungsgesetz-2026-response-083':('2026-03-26','Köln, 26.03.2026',None,'dated closing read'),
 'tkg-aenderungsgesetz-2026-response-089':('2026-03-24','Düsseldorf, den 24.03.2026',None,'dated closing read'),
 'tkg-aenderungsgesetz-2026-response-112':('2026-03-26','Datum: 26.März 2026',None,'dated closing read'),
}
for row in data['documents']:
 key=row['id'].removeprefix('bmds-')
 if key not in verified:continue
 date,fragment,page,method=verified[key]
 text=Path(row['text_file']).read_text(errors='replace')
 if page is None:
  match=re.search(re.escape(fragment).replace(r'\ ',r'\s*'),text)
  if match:page=text[:match.start()].count('\f')+1
 row.update(date=date,date_status='document_date_verified' if len(date)==10 else 'document_month_verified',window_status='outside_window',date_locator={'pdf_page':page},date_evidence={'fragment':fragment,'method':method},depth='date_and_selected_passages')
 if 'visually' in method:row['date_evidence']['rendered_cover']='research/round3-tax/sources/date-covers/'+row['id']+'.png'
 if key.endswith('response-049') and key.startswith('tkg-'):row['package_parent_id']='bmds-tkg-aenderungsgesetz-2026-response-048'
# A literal inconsistent cover year is not silently corrected.
for row in data['documents']:
 if row['id']=='bmds-digitale-identitaetengesetz-response-042':
  row['date_evidence']={'fragment':'Berlin, 15.04.2024','context':'Cover says2024 but footers2026 and addressed2026 draft. Literal year not silently corrected; still unverified.'};row['date_status']='inconsistent_literal_year';row['depth']='date_and_selected_passages'
p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
from collections import Counter
print(Counter(r['window_status'] for r in data['documents']))
