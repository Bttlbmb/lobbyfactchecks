from pathlib import Path
import json,re
p=Path(__file__).parent/'coverage-bt-response-links.json';d=json.loads(p.read_text())
# Author page2 covers read manually; these are not committee page1 dates.
known={
'1217466':{1:('2026-10-06','06.10.2026'),2:('2026-10-08','Berlin, den 08. Oktober2026'),4:('2026-09-24','Stand: 24. September 2026'),5:('2026-10-12','Stand der Stellungnahme12. Oktober2026'),6:('2026-10-12','Berlin, den12. Oktober2026'),9:('2026-10-12','12. Oktober2026')},
'1221614':{1:('2026-06-30','Datum/Date30.06.2026'),2:('2026-04-22','Berlin,22.04.2026'),3:('2026-10-13','Stand:13.10.2026')},
'1217464':{1:('2026-10-06','Berlin,6. Oktober2026'),2:('2026-10-06','Berlin,06.10.2026'),3:('2026-10-07','7. Oktober2026'),5:('2026-10-07','Berlin,7. Oktober2026')},
'1217454':{2:('2026-09-30','Berlin,30. September2026'),3:('2026-08','August2026'),8:('2026-10-05','Berlin,05.10.2026, Anhörung am07.10.2026')},
'1217440':{1:('2026-09-22','Berlin,22.09.2026'),2:('2026-10-01','1.10.2026'),3:('2026-10-01','Berlin,den01.10.2026'),4:('2026-10-01','München,1.10.2026'),5:('2026-09-30','Bochum,30. September2026'),6:('2026-10-02','02.10.2026'),7:('2026-10-05','Stellungnahme05.10.2026'),8:('2026-10','Oktober2026'),9:('2026-10-05','Berlin,5. Oktober2026')},
'1217432':{1:('2026-10-05','Berlin,5. Oktober2026'),2:('2026-10-01','Stand:1.10.26'),3:('2026-10-01','Stand:01.10.2026'),4:('2026-09-30','Berlin,30 September2026'),6:('2026-10-02','02.10.2026/pu'),7:('2026-10-05','05.10.2026'),8:('2026-08','August2026')},
'1205008':{1:('2026-08-31','Berlin,31. August2026'),2:('2026-09-01','Berlin,1. September2026'),3:('2026-09-02','Stand:02.09.2026'),4:('2026-09-03','03.09.2026'),5:('2026-09-04','04.09.2026')}}
n=0
for r in d['documents']:
 _,hid,_,seq=r['id'].split('-');item=known.get(hid,{}).get(int(seq))
 if item is None:continue
 date,fragment=item
 # Context locator page2 points to author cover after committee cover.
 r.update(date=date,date_status='author_document_date_verified' if len(date)==10 else 'author_document_month_verified',date_locator={'pdf_page':2},date_evidence={'fragment':fragment,'method':'Author cover/header read separately from committee cover'},author_date_window_status='outside_window' if date<'2026-07-25' else 'in_window',window_status='in_window' if date>='2026-07-25' else 'potentially_in_window_committee_version_author_earlier',depth='date_and_selected_passages');n+=1
 if r['id']=='hearing-1221614-response-002':r['author_verified_from_original']='Bundesverband der Deutschen Industrie(BDI) and Bundesvereinigung der Deutschen Arbeitgeberverbände(BDA)';r['metadata_qualification']='Official committee cover mislabelsBDI as Bauindustrie; original author page2 says Industrie. Publisher metadata only; no allegation against authors.'
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');print(n,'author dates annotated')
