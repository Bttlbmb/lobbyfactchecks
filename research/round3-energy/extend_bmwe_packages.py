import json,re,pathlib,hashlib
R=pathlib.Path('research/round3-energy'); ROOT=pathlib.Path('research/round3-root/coverage')
def read(p):return json.loads(p.read_text())
o=read(R/'coverage-bmwe-published-responses.json');members=read(R/'coverage-bmwe-bundle-members.json')
register=read(ROOT/'register-window-records.json')['records'];rs={x['id']:x for x in register}
sha={}
for x in read(ROOT/'register-archive-manifest.json')['records']:
 if x.get('sha256'):sha.setdefault(x['sha256'],[]).append(x['id'])
for x in members:
 x['byte_identical_register_ids']=sha.get(x['sha256'],[])
 x['register_delivery_events']=[{'register_id':sid,**e}for sid in x['byte_identical_register_ids'] for e in rs[sid].get('recipient_events',[])]
(R/'coverage-bmwe-bundle-members.json').write_text(json.dumps(members,ensure_ascii=False,indent=2)+'\n')
kl=['Deutsche Carbon Management Initiative (DCMI)','Verband Deutscher Maschinen- und Anlagenbau e. V. (VDMA)','Deutscher Verein des Gas- und Wasserfaches (DVGW)','Freie und Hansestadt Hamburg','Brandenburg','Hessen','Bundesverband der Energie- und Wasserwirtschaft e.V. (BDEW)','Carbon Management Allianz (CMA)','Nordrhein-Westfalen','TÜV-Verband e.V.','VNG AG','Niedersachsen','Sachsen-Anhalt']
wp=['Hessisches Ministerium für Wirtschaft, Energie, Verkehr und Wohnen','IDW Institut der Wirtschaftsprüfer in Deutschland','BVBC Bundesverband der Bilanzbuchhalter und Controller e.V. (joint author WIB on PDF)']
net=['Wirtschaftsvereinigung Stahl','DIE FAMILIENUNTERNEHMER e.V.','Deutsche Industrie- und Handelskammer','VIK – Verband der Industriellen Energie- und Kraftwirtschaft e.V.','Handelsverband Deutschland e.V.','Bundesverband Baustoffe – Steine und Erden e.V.','Bundesverband Neue Energiewirtschaft e.V.','Bundesverband Kooperierender Mittelstand e.V.','Zentralverband des Deutschen Handwerks','Bundesverband der Energieabnehmer e.V.','Verband der Chemischen Industrie e.V.','Deutscher Gewerkschaftsbund','Industriegewerkschaft Bergbau, Chemie, Energie','Verbraucherzentrale Bundesverband e.V.','Bundesverband der Energie- und Wasserwirtschaft e.V.','Verein Deutscher Ingenieure e.V.','50Hertz Transmission GmbH, Amprion GmbH, TenneT Holding B.V., TransnetBW GmbH','Deutscher Naturschutzring e.V. and Germanwatch e.V.','ZVEI e.V.','thyssenkrupp Steel Europe AG','Hessisches Ministerium für Wirtschaft, Energie, Verkehr, Wohnen und ländlichen Raum','Niedersächsisches Ministerium für Umwelt, Energie und Klimaschutz','Deutscher Landkreistag','Ministerium für Umwelt, Energie, Naturschutz und Forsten Thüringen']
for group,names,key in zip(o['other_current_dataset_summaries'],[kl,wp,net],['kltgv','wpexamen','netzkosten']):
 group['date_limit']='Ministry interval is context, not an individual date gate. Filename date and author date remain separate; no late receipt is inferred from a filename.'
 docs=[x for x in members if x['dataset_url']==group['dataset_url']];ps=[]
 for n,name in enumerate(names,1):
  p={'id':f'bmwe-{key}-2026-{n:03d}','author':name,'process':group['process'],'dataset_url':group['dataset_url'],'participant_list_file':group['participant_list_file'],'participant_number':n,'source_components':[],'depth':'metadata_only','screened_substantively':False,'submission_date':None,'submission_date_verified':False,'ministry_reported_interval':group['ministry_reported_interval'],'window_state':'consultation_interval_context_only_individual_delivery_unverified'}
  for d in docs:
   f=d['member_name'];match=False
   if key=='kltgv':
    patterns={1:'DCMI',2:'VDMA',3:'DVGW',4:'HH_',5:'Anschreiben',6:'Hessen',7:'BDEW',8:'CMA_',9:'NRW_',10:'TÜV-',11:'VNG'};match=n in patterns and patterns[n] in f
   elif key=='wpexamen':match=f.startswith(f'{n:03d}_')
   else:
    dn=int(re.match(r'(\d+)\.',f)[1]);island='c2bd1277f8c9d225' in d['archive_file'];match=(n==dn+20 if island else n==dn)
   if match:p['source_components'].append({'kind':'pdf_response','file':d['local_file'],'member_name':f,'sha256':d['sha256'],'date_candidates':d['date_candidates'],'byte_identical_register_ids':d['byte_identical_register_ids'],'register_delivery_events':d['register_delivery_events']})
  p['ministry_publication_status']='public_pdf_archived' if p['source_components'] else 'withheld_by_author_in_this_dataset';ps.append(p)
 group['participant_packages']=ps
 assert sum(bool(p['source_components']) for p in ps)==group['public_pdf_files']
# Explicit author-date qualifications, preserving contradictory filename years/dates.
for g in o['other_current_dataset_summaries']:
 if g['process']=='Wirtschaftsprüferexamen':
  for p,d in zip(g['participant_packages'],['2026-09-29','2026-10-14','2026-10-13']):p['author_date']=d;p['author_date_verified']=True;p['author_date_basis']='Dated author cover read in first-two-page extraction; filename date is not substituted.'
 if g['process']=='KLtgV':
  g['participant_packages'][0]['author_date_precision']='month';g['participant_packages'][0]['author_date']='2026-08'
  g['participant_packages'][3]['date_conflict']='PDF author header says10August2025, while filename says20260810 and ministry dataset describes2026 consultation. No silent correction or verified individual receipt date.'
o['register_byte_cross_references']={'member_occurrences':sum(bool(x['byte_identical_register_ids'])for x in members),'distinct_register_ids':sorted({s for x in members for s in x['byte_identical_register_ids']}),'limits':'Byte identity links versions only. All recipient events retained; the root register date gate decides which particular delivery is within the window.'}
# Two separately published KrWaff consultation submissions.
q=read(R/'coverage-bmwe-dataset-download-queue-results.json')
o['krwaff_direct_responses']=[{**{k:x[k]for k in ['id','title','url','local_file','dataset_url'] if k in x},'depth':'metadata_only','screened_substantively':False,'author_date':'2026-08-05' if 'c0a28ced6823ac6a' in x['local_file'] else None,'submission_date_verified':False}for x in q if 'KrWaff' in x.get('dataset_url','') or 'krwaff' in x.get('dataset_url','').lower()]
o['counts']['other_named_participant_packages']=40
(R/'coverage-bmwe-published-responses.json').write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n')
print('packages',sum(len(g['participant_packages']) for g in o['other_current_dataset_summaries']),'register matches',o['register_byte_cross_references'],'KrWaff',len(o['krwaff_direct_responses']))
# Full Hamburg supplement explicitly links two listed authorities to one joint package.
for p in o['windsee_packages']:
 if p['participant_number'] in [5,6]:
  p['response_package_id']='bmwe-windsee-hamburg-joint-202608'
  p['package_relation']='BWAI PDF14August explicitly supplements preceding joint BWAI+BUKEA online response; keep both components and labels within one multipart package.'
 if p['participant_number']==22:
  p['supplement_sent_date']='2026-08-19';p['supplement_sent_date_verified']=True
  p['supplement_date_basis']='Published email Gesendet header and BMWE addressee; main structured response17August separate.'
o['counts']['windsee_public_named_participant_rows']=38
o['counts']['windsee_public_multipart_packages_after_explicit_hamburg_link']=37
limit='The list has38public named rows, but Hamburg BWAI and BUKEA explicitly share a joint online response plus PDF supplement;37multipart public packages under that grouping is not a distinct-document count.'
if limit not in o['publication_limits']:o['publication_limits'].append(limit)
(R/'coverage-bmwe-published-responses.json').write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n')
# External written submissions are the denominator; government replies are separate.
for p in o['windsee_packages']:
 government=p['participant_number'] in {5,6,22,23,24,26,27}
 p['contributor_kind']='Land_government' if government else 'external_stakeholder'
 p['in_external_submission_denominator']=not government
for g in o['other_current_dataset_summaries']:
 for p in g['participant_packages']:
  n=p['participant_number'];government=(n in {4,5,6,9,12,13} if g['process']=='KLtgV' else n==1 if g['process']=='Wirtschaftsprüferexamen' else n in {21,22,24})
  p['contributor_kind']='Land_government' if government else 'municipal_umbrella_association' if g['process'].startswith('Übertragungs') and n==23 else 'external_stakeholder'
  p['in_external_submission_denominator']=not government
for p in o.get('krwaff_direct_responses',[]):
 government='c0a28ced6823ac6a' in p['local_file'];p['contributor_kind']='Land_government' if government else 'external_stakeholder';p['in_external_submission_denominator']=not government
external=[p for p in o['windsee_packages'] if p['in_external_submission_denominator']]
o['counts']['windsee_external_named_contributors']=len(external)
o['counts']['windsee_external_public_contributors']=sum(p['ministry_publication_status']=='publicly_represented' for p in external)
o['counts']['windsee_external_withheld_contributors']=sum(p['ministry_publication_status']=='withheld_by_author' for p in external)
o['publication_limits'].append('User-confirmed denominator is all external written submissions, including NGOs/academics; Land government replies remain separately tagged and excluded. Municipal umbrella associations are separately typed rather than silently equated with a ministry reply.')
(R/'coverage-bmwe-published-responses.json').write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n')
