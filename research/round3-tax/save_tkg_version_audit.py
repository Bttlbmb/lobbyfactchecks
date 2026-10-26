import json,hashlib,datetime
from pathlib import Path
b=Path('research/round3-tax');root=Path('research/round3-root/coverage');records=json.loads((root/'register-window-records.json').read_text());records=records if isinstance(records,list) else records['records'];byid={r['id']:r for r in records}
ids=['SG2610160008','SG2610160007','SG2610160009','SG2610020013','SG2609300304','SG2609300067','SG2609290016','SG2609280023','SG2609240023','SG2608050021','SG2608050022']
notes={
'SG2610160008':('1&1 / United Internet','August2026','Government draft; first-page title, exact timestamp not established','First two author pages; metadata/version context only'),
'SG2610160007':('Deutsche Telekom',None,'Government draft adopted10June2026, explicit first paragraph','First two author pages; metadata/version context only'),
'SG2610160009':('Thomas Fetzer',None,'TKG government draft10June2026, explicit title and footnote1','Cover/contents and physical8–9commission/version section; not all69pages'),
'SG2610020013':('Telefónica Deutschland',None,'TKG2026 proposal; first-page description, exact draft timestamp not established','First-page opening and selected second-page context; not full8pages'),
'SG2609300304':('VATM','2026-09-17','Government draft adopted10June2026, explicit cover','First-page cover/opening; not full58pages'),
'SG2609300067':('SAP',None,'Proposed supplementary §165(3)security amendment; no exact addressed draft timestamp in one-page body','Full one-page formulation aid read'),
'SG2609290016':('Deutsche Telekom',None,'Bundesrat committee recommendations BR439/1/26, explicit title','First-page opening; not full9pages'),
'SG2609280023':('Deutsche Telekom position, transmitted by TKM Consulting',None,'Same government-draft position as SG2610160007','Cover/opening and normalized-full-text equality check; not an additional full read'),
'SG2609240023':('EVVC',None,'TKG2026 proposed §91(1)sentence4and§2(8); registry BR439/26 association','Full two-page response and relevant original government draft clauses read'),
'SG2608050021':('BREKO','2026-07-31','Government draft adopted10June2026, explicit first/second-page description','First two pages; not full33pages'),
'SG2608050022':('BDEW, BREKO and VKU',None,'Expressly proposes replacing planned§22aTKG with a Fairplay agreement; registry associates TKG draft','Full two-page shared paper read; citation access date22July is not its verified author date')}
rows=[]
for id in ids:
 r=byid[id];author,date,stage,extent=notes[id]
 rows.append({'id':id,'registrant_author':r['registered_author'],'authored_document_author':author,'document_date':date,'document_date_basis':'Manually read printed author date/month' if date else 'No own date established; citations and draft dates not substituted','recipient_events':r['recipient_events'],'local_file':str(root/'register-pdfs'/(id+'.pdf')),'url':r['pdf_url'],'addressed_version_observed':stage,'reading_extent':extent,'census_depth':'manual selected header/scope context; full-submission entries are separately recorded in research-log.json','submission_date_independently_receipted':False})
cluster={'id':'tkg2026-telekom-position-different-registrants','record_ids':['SG2610160007','SG2609280023'],'match_basis':'Entire extracted text identical after removal of whitespace; binary PDF hashes differ. Both cover/opening texts manually inspected.','normalized_full_text_sha256':'3622e20209926ebf5ef1cea59b7c64364806120aed45efef57fb355598b6c8af','authored_unit_count_for_this_cluster':1,'recipient_events_preserved':True,'not_merged':['SG2609290016 is a distinct Bundesrat-recommendation comment','SG2610160009 is a separately authored legal opinion by Thomas Fetzer; physical9confirms Telekom commission']}
out={'as_of_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Eleven register-linked autumn TKG records selected from the BMDS crosswalk','records':rows,'duplicate_clusters':[cluster],'primary_draft_sources':[{'id':'bmds-tkg-regierungsentwurf-20260610','url':'https://bmds.bund.de/fileadmin/BMDS/Dokumente/Gesetzesvorhaben/260602_Zuleitungsexemplar_TKG-%C3%84ndG_2026_barrierefrei.pdf','local_file':'research/round3-tax/sources/bmds-tkg-regierungsentwurf-20260610.pdf','use':'Original government publication; relevant clauses selectively read, not full act'},{'id':'br-439-26-tkg2026','url':'https://dserver.bundestag.de/brd/2026/0439-26.pdf','local_file':'research/round3-tax/sources/br-439-26-tkg2026.pdf','printed_date':'2026-08-14','use':'Version context; not automatically substituted for explicitly addressed10Junegovernment draft'},{'id':'br-439-1-26-tkg-recommendations','url':'https://dserver.bundestag.de/brd/2026/0439-1-26.pdf','local_file':'research/round3-tax/sources/br-439-1-26-tkg-recommendations.pdf','printed_date':'2026-09-14','use':'Distinct Bundesrat recommendations addressed by SG2609290016'},{'id':'bt-21-8277-tkg2026','url':'https://dserver.bundestag.de/btd/21/082/2108277.pdf','local_file':'research/round3-tax/sources/bt-21-8277-tkg2026.pdf','printed_date':'2026-09-30','use':'Later Bundestag printing; not automatically substituted for an earlier addressed version'}],'limitations':['A registry draft association is not necessarily the actual document version addressed.','Absence of a printed author date does not exclude a verified register-reported transmittal date.','Metadata/version reading is not a substantive full claim screen.']}
# Targeted narrative spacing; identifiers, paths and URLs remain untouched.
repls={'August2026':'August 2026','adopted10June2026':'adopted 10 June 2026','draft10June2026':'draft 10 June 2026','footnote1':'footnote 1','physical8–9commission':'physical 8–9 commission','all69pages':'all 69 pages','full8pages':'full 8 pages','full58pages':'full 58 pages','full9pages':'full 9 pages','BR439/1/26':'BR 439/1/26','sentence4and§2(8)':'sentence 4 and §2(8)','BR439/26':'BR 439/26','full33pages':'full 33 pages','planned§22aTKG':'planned §22a TKG','date22July':'date 22 July','physical9confirms':'physical 9 confirms','addressed10Junegovernment':'addressed 10 June government','§165(3)security':'§165(3) security'}
def clean(v,k=''):
 if k in ['id','record_ids','normalized_full_text_sha256','url','local_file']:return v
 if isinstance(v,dict):return {x:clean(y,x) for x,y in v.items()}
 if isinstance(v,list):return [clean(x,k) for x in v]
 if isinstance(v,str):
  for x,y in repls.items():v=v.replace(x,y)
 return v
out=clean(out);(b/'coverage-tkg-autumn-version-audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
p=b/'coverage-semantic-copy-clusters.json';old=json.loads(p.read_text());print('clusters existing shape',type(old),list(old)[:4])
# Keep the new cluster in its own explicit audit; do not assume a foreign registry structure.
s=json.loads((b/'sources.json').read_text())
for r in out['primary_draft_sources']:
 z=dict(r,document_kind='draft_primary',retrieved_at='2026-10-25');z['sha256']=hashlib.sha256(Path(z['local_file']).read_bytes()).hexdigest();s=[x for x in s if x['id']!=z['id']]+[z]
(b/'sources.json').write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n')
print('Version records',len(rows))
