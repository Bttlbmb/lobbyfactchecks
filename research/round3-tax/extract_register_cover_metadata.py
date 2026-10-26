import json,re,collections,datetime
from pathlib import Path
base=Path('research/round3-tax');src=Path('research/round3-root/coverage/register-pdfs')
a=json.loads((base/'coverage-register-scope-metadata.json').read_text())
rows=[];groups=collections.defaultdict(list)
for r in a['records']:
 p=src/(r['id']+'.txt');full=p.read_text(errors='replace') if p.exists() else '';head='\f'.join(full.split('\f')[:2])
 dates=[]
 patterns=[r'\b(?:0?[1-9]|[12]\d|3[01])\s*\.\s*(?:0?[1-9]|1[012])\s*\.\s*20\d{2}\b',r'\b(?:0?[1-9]|[12]\d|3[01])\s*\.?\s*(?:Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s+20\d{2}\b',r'\b20\d{2}-\d{2}-\d{2}\b']
 for pat in patterns:
  for m in re.finditer(pat,head,re.I):
   d=m.group(0);loc=head[:m.start()].count('\f')+1
   if not any(x['text']==d and x['pdf_page']==loc for x in dates):dates.append({'text':d,'pdf_page':loc,'context':re.sub(r'\s+',' ',head[max(0,m.start()-60):m.end()+60]).strip()})
 refs=[]
 for m in re.finditer(r'(?:BT|BR)[\s-]*(?:Drs\.?|Drucksache)?[\s.:\-]*(?:\d{1,2}/\d{2,6}|\d{2,6}/\d{2})(?:\s*\([^)]{1,15}\))?',head):
  z=m.group(0)
  if z not in refs:refs.append(z)
 title=r['regulatory_project']['links'][0]['text'] if r['regulatory_project']['links'] else r['regulatory_project']['text'][:160]
 z={'id':r['id'],'registrant_author':r['author'],'matched_ministries':r['matched_ministries'],'recipient_events':r['recipient_events'],'regulatory_project_title':title,'registry_draft_field':r['draft_field'],'local_file':str(src/(r['id']+'.pdf')),'text_file':str(p),'cover_date_candidates':dates,'cover_draft_reference_candidates':refs,'extraction_extent':'first two physical PDF text pages only','verification':'machine-extracted candidate dates and references; not manually verified author dates, recipient dates or addressed versions','content_screening_status':'not added to substantive screening pool by this extraction'}
 rows.append(z);groups[title].append(r['id'])
out={'as_of_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_file':'research/round3-tax/coverage-register-scope-metadata.json','records':rows,'limitations':['Dates in a document can refer to a hearing, draft, cited source or an earlier incorporated statement. No candidate is automatically selected as the document date.','Registry draft associations may differ from the version actually addressed in the response.','First two pages do not settle later qualifications, annexes or older incorporated versions.']}
(base/'coverage-register-cover-metadata.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
(base/'coverage-register-process-groups.json').write_text(json.dumps({'grouping_unit':'exact registered regulatory-project title; not necessarily one legislative process or unique authored response','groups':[{'title':k,'record_ids':v,'records':len(v)} for k,v in groups.items()]},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'records':len(rows),'project_title_groups':len(groups),'no_cover_date_candidate':sum(not r['cover_date_candidates'] for r in rows)},ensure_ascii=False))
