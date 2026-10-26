"""Automatic date/readability diagnostics. These are neither eligibility nor screens."""
import json,pathlib,re,collections
BASE=pathlib.Path(__file__).resolve().parent;ROOT=BASE.parent.parent.parent
rows=json.load(open(BASE/'root-statement-resource-archive.json'))['records']+json.load(open(BASE/'root-package-members.json'))['records']
months={'januar':1,'februar':2,'märz':3,'april':4,'mai':5,'juni':6,'juli':7,'august':8,'september':9,'oktober':10,'november':11,'dezember':12}
def candidates(t):
 out=[]
 for m in re.finditer(r'\b(\d{1,2})\.\s*(\d{1,2})\.\s*(20\d{2})\b|\b(\d{1,2})\.\s*('+'|'.join(months)+r')\s*(20\d{2})\b',t,re.I):
  day,month,year=(int(m[1]),int(m[2]),int(m[3])) if m[1] else (int(m[4]),months[m[5].lower()],int(m[6]))
  if 1<=day<=31 and 1<=month<=12:out.append({'candidate':f'{year:04}-{month:02}-{day:02}','verbatim':m.group(0)})
 return out
out=[]
for r in rows:
 if not r.get('text_file'):continue
 p=ROOT/r['text_file']
 if not p.exists():continue
 pages=p.read_text(errors='replace').split('\f');pages=pages[:-1] if pages and not pages[-1].strip() else pages
 take=sorted(set(list(range(min(2,len(pages))))+list(range(max(0,len(pages)-2),len(pages)))))
 ds=[dict(x,pdf_page=i+1) for i in take for x in candidates(pages[i])]
 out.append({'url':r.get('url',r.get('parent_url')),'member_name':r.get('member_name'),'channel':r['channel'],'local_file':r['local_file'],'sha256':r['sha256'],'text_file':r['text_file'],'physical_pages_from_extraction':len(pages),'selected_pages_for_metadata':[i+1 for i in take],'date_candidates':ds,'contains_window_date_candidate':any('2026-07-25'<=x['candidate']<='2026-10-24' for x in ds),'low_text_pages':[i+1 for i,t in enumerate(pages) if len(t.strip())<100],'screening_status':'not_screened_by_this_operation','eligibility_status':'pending_manual_scope_delivery_version_check','date_limit':'A date string may refer to a law, court decision, deadline or hearing. Absence of a window date is not an exclusion.'})
(BASE/'root-automatic-date-candidates.json').write_text(json.dumps({'records':out,'summary':{'resource_occurrences':len(out),'with_window_date_string':sum(x['contains_window_date_candidate'] for x in out),'with_at_least_one_low_text_page':sum(bool(x['low_text_pages']) for x in out)},'limits':'No automatic date is treated as verified authorship, dispatch or scope. Text extraction does not prove all PDF pages readable.'},ensure_ascii=False,indent=2)+'\n')
print('resource occurrences',len(out),'with window date strings',sum(x['contains_window_date_candidate'] for x in out))

# The same page-level diagnostics for the central registry archive retain every SGID.
sg=json.load(open(BASE/'register-archive-manifest.json'))['records'];diagnostics=[]
for r in sg:
 if not r.get('text_file'):continue
 ps=(ROOT/r['text_file']).read_text(errors='replace').split('\f');ps=ps[:-1] if ps and not ps[-1].strip() else ps
 diagnostics.append({'id':r['id'],'sha256':r['sha256'],'extracted_pages':len(ps),'text_chars_per_page':[len(t.strip()) for t in ps],'low_text_pages':[i+1 for i,t in enumerate(ps) if len(t.strip())<100],'limit':'Low text can be a blank, cover, scan or extraction issue; this is a visual/OCR prioritisation diagnostic, not proof of incompleteness or reading.'})
(BASE/'register-page-text-diagnostics.json').write_text(json.dumps({'records':diagnostics,'records_with_a_low_text_page':sum(bool(x['low_text_pages']) for x in diagnostics)},ensure_ascii=False,indent=2)+'\n')
