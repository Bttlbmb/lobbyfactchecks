from pathlib import Path
import json,re,collections
p=Path(__file__).parent/'coverage-bmvg-all-response-links.json';d=json.loads(p.read_text())
choices={'5988276':{1:0},'6004892':{1:0,7:1,8:0,9:0,14:0,18:0,19:0,21:0,22:0,23:0},'5920940':{1:0},'5872562':{1:0},'5861484':{1:0},'5850996':{1:0},'5833710':{1:0,2:0,3:0,4:0,5:0,6:0},'5826528':{1:0,2:0},'5826516':{1:0,2:0},'5826508':{1:0,2:0},'5826480':{1:0,2:0},'5785704':{1:0},'5697648':{2:0,4:0},'5522412':{1:0},'5217928':{1:0},'5061242':{1:0},'5022518':{1:0,2:0},'3769266':{5:0,6:0,7:0},'3779054':{1:0,2:0,3:0,5:0},'5090548':{1:0,2:0},'5090778':{1:0,2:1},'3904486':{5:0},'3812988':{1:0,2:0},'3810978':{1:0,3:0,4:0,6:0,7:0,8:0,10:1,11:2},'3810416':{1:1,2:0}}
months={'januar':1,'februar':2,'märz':3,'maerz':3,'april':4,'mai':5,'juni':6,'juli':7,'august':8,'september':9,'oktober':10,'november':11,'dezember':12}
def parse(t):
 t=' '.join(t.split());m=re.fullmatch(r'(\d{1,2})\.\s*(\d{1,2})\.\s*(\d{4})',t)
 if m:day,mon,year=map(int,m.groups())
 else:
  m=re.fullmatch(r'(\d{1,2})\.?\s*([A-Za-zÄÖÜäöü]+)\s+(\d{4})',t);assert m,t
  day,word,year=m.groups();day=int(day);year=int(year);mon=months[word.lower()]
 return f'{year:04d}-{mon:02d}-{day:02d}'
n=0
for r in d['documents']:
 _,_,_,hid,_,seq=r['id'].split('-');idx=choices.get(hid,{}).get(int(seq))
 if idx is not None:
  c=r['date_candidates_first_two_pages'][idx];date=parse(c['match']);assert date<'2026-07-25'
  r.update(date=date,date_status='document_date_verified_from_header_or_closing_context',window_status='outside_window',date_locator={'pdf_page':c['pdf_page']},date_evidence={'fragment':c['match'],'context':c['context'],'method':'Manually read author date context in extracted original PDF; not request, citation or deadline'},depth='date_and_selected_passages');n+=1
 if hid=='6004892' and int(seq)==17:r.update(date='2025-08-14',date_status='document_date_verified_from_footer',window_status='outside_window',date_locator={'pdf_page':1},date_evidence={'fragment':'14.08.25','method':'Author footer read; not30July draft date'},depth='date_and_selected_passages')
 if hid=='5988276' and int(seq)==2:r.update(date='2025-08',date_status='document_month_verified',window_status='outside_window',date_locator={'pdf_page':1},date_evidence={'fragment':'August2025','method':'Cover heading month, after statement number39; not parsed as day39'},depth='date_and_selected_passages')
 if hid=='6004892' and int(seq)==11:r.update(date_status='inconsistent_literal_year',date_evidence={'fragment':'Datum14.08.2028','context':'Literal future year on a response published on official2025page; date not silently corrected.'},depth='date_and_selected_passages')
# Mark byte-identical mirror links as one canonical document, while preserving process associations.
by=collections.defaultdict(list)
for r in d['documents']:by[r.get('sha256')].append(r)
for rs in by.values():
 for r in rs:
  r['canonical_document_id']=rs[0]['id'];r['byte_identical_link_ids']=[z['id'] for z in rs if z['id']!=r['id']]
d['distinct_sha256_count']=len(by);d['published_pdf_link_count']=len(d['documents'])
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
print(n,'manual dates; states',collections.Counter(r['window_status'] for r in d['documents']),'canonical',len(by))
