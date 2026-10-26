import json,re,pathlib,datetime,collections,urllib.parse
from bs4 import BeautifulSoup
BASE=pathlib.Path('research/round3-social');lo=datetime.date(2026,7,25);hi=datetime.date(2026,10,24)
def hints(txt):
 out=[]
 for pat,order in [(r'(?<!\d)(20\d\d)[-_.]?(\d\d)[-_.]?(\d\d)(?!\d)','ymd'),(r'(?<!\d)(\d{1,2})[.](\d{1,2})[.](20\d\d)(?!\d)','dmy')]:
  for m in re.finditer(pat,txt or ''):
   a,b,c=map(int,m.groups());y,mo,day=(a,b,c) if order=='ymd' else(c,b,a)
   try:out.append({'text':m.group(),'date':datetime.date(y,mo,day).isoformat()})
   except ValueError:pass
 return out
rows=[];rounds=[]
def add(doc,p,authority,reason):
 y=dict(doc);y.update(authority=authority,process=p['title'],process_url=p['url'],process_archive=p.get('archive'),selection_reason=reason,submission_date=None,submission_date_status='date_unverified',collection_status='link_collected',content_screening_status='not_reviewed',norm_type=p.get('norm_type'),document_kind='written_submission',eligibility_status='pending_actual_date_and_external_author_verification');
 if authority=='BMAS' and p['title']=='Tariftreuegesetz' and 'tariff-implementationordinance' in reason:
  y['parent_norm_type']=y['norm_type'];y['norm_type']='ordinance';y['addressed_stage']='September2026implementingordinanceconsultation,notparentTariftreuebill'
 if authority.startswith('Bundestag'):
  path=p['url']
  if any(v in path for v in ['1205988','1221656']):y['norm_type']='law'
  if '1221930' in path:
   y['norm_type']='law_amendments';y['legislative_vehicle']='Notfallversorgung governmentbillBT21/6808;hearingconcernsGKV-BStabGfollow-upamendments'
  if '1205990' in path:
   y['norm_type']='policy_motion';y['addressed_printed_matter']='BT21/6343'
 y['date_hints']=hints(' '.join(str(doc.get(k,'')) for k in ['context','url','link_title','structured_document_date']));rows.append(y)
for n in ['bmg','bmas','family']:
 d=json.load(open(BASE/('coverage-processes-'+n+'.json')))
 for i,p in enumerate(d['process_pages']):
  for doc in p['documents']:
   if doc['inferred_kind']!='submission':continue
   reason=None
   if n=='family' and i<3:reason='Recent/undated consultation round on current process page; document date requires check.'
   elif n=='bmg' and '/RSV_1_AendVO/' in doc['url']:reason='Consultation for20August2026RSVamendmentdraft; documentdateunverified.'
   elif n=='bmg' and '/Stellungnahmen_WP21/SuizidPraevG/' in doc['url']:reason='3July2026draft consultation; author-published BÄK28July2026 response proves potential window. Entire21LPchapterdatechecked rather than excluded by process last-standdate.'
   elif n=='bmas' and i in [2,5,6]:reason='Recent2026consultation process; individualdocumentdateunverified.'
   elif n=='bmas' and i==0:
    s=BeautifulSoup(open(p['archive']).read(),'html.parser');a=s.find(attrs={'href':lambda h:h and urllib.parse.urlsplit(doc['url']).path in h});sect=a.find_parent('pp-accordion-item') if a else None
    st=sect.get_text(' ',strip=True) if sect else ''
    if 'Stellungnahmen zu den Verordnungsentwürfen' in st:reason='September2026tariff-implementationordinance consultation; parentlawpagecontainsmultiplerounds.'
   dh=hints(' '.join(str(doc.get(k,'')) for k in ['context','url','link_title','structured_document_date']))
   if any(lo.isoformat()<=v['date']<=hi.isoformat() for v in dh):reason=(reason+' ' if reason else '')+'Explicit date hint in link/context inside window; not yet verified as authored/submitteddate.'
   if reason:add(doc,p,d['authority'],reason)
# Committee entries include upcominghearings; no hearingdate treatedas submissiondate.
d=json.load(open(BASE/'coverage-bundestag.json'))
for c in d['committees']:
 for p in c.get('hearing_pages',[]):
  hdate=p['index_evidence'].get('hearing_date_label') or ''
  if not any(w in hdate for w in ['September 2026','Oktober 2026','November 2026','Dezember 2026']):continue
  for doc in p['documents']:
   t=doc['link_title'];u=doc['url']
   if not '/resource/blob/' in u or not u.lower().endswith('.pdf'):continue
   if re.match(r'21/\d',t):continue
   if any(w in t.lower() for w in ['sitzung','tagesordnung','liste der','protokoll','änderungsantr','aenderungsantr']):continue
   if doc['inferred_kind'] not in ['submission','other_document']:continue
   add(doc,p,'Bundestag '+c['committee'],'Recent/forthcoming hearing; actual submissiondate mustbe checked.');rows[-1]['hearing_date_label']=hdate
   if 'Materialzusammenstellung' in u or 'zusammenstellung' in t.lower():rows[-1]['document_kind']='bundle_container_requires_authored_unit_enumeration'
byurl={}
for x in rows:
 if x['url'] not in byurl:byurl[x['url']]=x
 else:byurl[x['url']].setdefault('duplicate_collections',[]).append({'authority':x['authority'],'process_url':x['process_url']})
rows=list(byurl.values())
out={'retrieved_at':'2026-10-25','date_window':{'from':'2026-07-25','through':'2026-10-24'},'method':'Candidatecollectionfor dateandidentityverification, NOTallfactsreviewed. Recentorundatedpotentialwindowrounds plus explicitlinkdatehints; historical linkinventories retained separately. No collectioncount asserted as exhaustiveeligible submissions.','documents':rows,'summary':{'unique_document_links':len(rows),'by_authority':dict(collections.Counter(x['authority'] for x in rows))},'gaps':['Actual document/submissiondates requireverification.','BMFTRofficialindexunavailable403/reset; registerandotherofficialsourcespending.','Possiblelatefilingsonolderconsultationroundsnotindependentlyexhausted; fullhistoricalministrylinkinventoriesandregistercrosscheckretained.','Bundestag-onlyrecipientregisterrecordsnot capturedbyministryrecipientselection.','Bundlesandattachmentsmustbe deduplicatedat authoredresponse/versionlevel.']}
(BASE/'coverage-window-candidates.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(out['summary'])
