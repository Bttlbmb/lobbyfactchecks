import json,re
from pathlib import Path
p=Path(__file__).parent/'coverage-bt-response-links.json';d=json.loads(p.read_text())
# Candidate indices selected only after manual reading of header/closing contexts.
selections={
'1191806':{1:0,2:1,4:1},'1183612':{1:0,3:0,5:0},
'1174334':{2:2,3:1,4:0,5:0,9:0,10:1},
'1165588':{1:2,3:1,4:1,5:0,6:0,7:1,8:0},
'1161138':{1:0,3:0,4:0,5:0,7:0,8:1},
'1151338':{1:0,2:0,3:0,4:0,7:1,8:1},
'1136910':{2:0,3:0,5:0},'1133892':{1:0,2:0,3:0,4:1,5:1},
'1127034':{4:0,5:0,6:0,8:0,9:0},
'1113288':{2:1,3:0,4:0,5:1,6:0,7:0,8:0,9:0},
'1113286':{1:0,2:0,3:0,4:0,5:0,7:0},
'1113284':{1:0,3:0,4:1},'1113244':{1:0,2:0,4:1},
'1113238':{1:0,2:2,3:0,4:0,5:0,6:0},
'1086482':{1:0,2:0,3:0,4:0,5:0,6:0,8:0,9:1,10:0}}
months={'januar':1,'februar':2,'märz':3,'maerz':3,'april':4,'mai':5,'juni':6,'juli':7,'august':8,'september':9,'oktober':10,'november':11,'dezember':12}
def parse(t):
 t=' '.join(t.split());m=re.fullmatch(r'(\d{1,2})\.\s*(\d{1,2})\.\s*(\d{4})',t)
 if m:day,mon,year=map(int,m.groups())
 else:
  m=re.fullmatch(r'(\d{1,2})\.?\s+([A-Za-zÄÖÜäöü]+)\s+(\d{4})',t);assert m,t
  day,word,year=m.groups();day=int(day);year=int(year);mon=months[word.lower()]
 return f'{year:04d}-{mon:02d}-{day:02d}'
n=0
for r in d['documents']:
 _,hid,_,seq=r['id'].split('-');idx=selections.get(hid,{}).get(int(seq))
 if idx is None:continue
 c=r['date_candidates_first_two_pages'][idx];date=parse(c['match']);assert date<'2026-07-25'
 r.update(date=date,date_status='document_date_verified_from_header_or_closing_context',window_status='outside_window',date_locator={'pdf_page':c['pdf_page']},date_evidence={'fragment':c['match'],'context':c['context'],'method':'Manually reviewed author date context in extracted original PDF; hearing/draft/citation dates excluded'},depth='date_and_selected_passages');n+=1
 if hid=='1113288' and int(seq)==9:r['date_evidence']['qualification']='Literal cover says10August2025 for10November2025 hearing; both dates precede this2026window. No error allegation made.'
d.setdefault('limitations',[]).append('Outside-window printed document dates are not proof against a later in-window retransmittal; reconcile with the separate Lobbyregister recipient-event census.')
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');print(n,'earlier document dates annotated')
