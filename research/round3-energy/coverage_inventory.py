"""Reconcile observed ministry attachments without calling collection substantive screening."""
import collections,hashlib,json,pathlib
BASE=pathlib.Path(__file__).resolve().parents[2];R=BASE/'research/round3-energy'
def read(p,default):
 try:return json.loads((BASE/p).read_text())
 except FileNotFoundError:return default
cat=read('research/round3-energy/coverage-ministry-process-catalogue.json',{})
rows=read('research/round3-energy/coverage-ministry-all-observed-pdf-queue.json',[])
archives={}
for name in ['coverage-ministry-pdf-queue-results.json','coverage-ministry-historical-pdf-queue-results.json']:
 for x in read('research/round3-energy/'+name,[]):
  if not x.get('access_error'):archives[x['id']]=x
# If a download job is still live, actual PDF magic/hash supplies archive state only.
for x in rows:
 if x['id'] in archives:continue
 p=BASE/x['local_file']
 if p.is_file():
  b=p.read_bytes()
  if b.startswith(b'%PDF'):archives[x['id']]={'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b),'status':'pdf_archived_from_live_job'}
dates={x['id']:x for x in read('research/round3-energy/coverage-ministry-date-candidates.json',[])}
manual=read('research/round3-energy/coverage-ministry-manual-date-adjudications.json',{})
root_records=read('research/round3-root/coverage/register-window-records.json',{}).get('records',[])
sg_lookup={x['id']:x for x in root_records};sg_by_sha=collections.defaultdict(list)
for x in read('research/round3-root/coverage/register-archive-manifest.json',{}).get('records',[]):
 if x.get('sha256') and x.get('status')=='archived_not_screened':sg_by_sha[x['sha256']].append(x['id'])
log=read('research/round3-energy/screening-log.json',[]);read_by_file={}
for x in log:
 for f in x.get('local_files',[]):read_by_file[f]=x
units={}
for x in rows:
 a=archives.get(x['id'],{});sha=a.get('sha256');key=sha or x['url']
 if key not in units:
  units[key]={'id':x['id'],'aliases':[],'author_labels':[],'process_ids':[],'process_titles':[],'ministry':x['ministry'],'urls':[],'local_files':[],'source_pages':[],'depth':'metadata_only','screened_substantively':False,'sha256':sha,'archive_state':'pdf_archived' if sha else 'not_archived','source_kind':'official_ministry_attachment_labelled_submission','date_state':'unverified','submission_date_verified':False,'registered_records':[],'sent_events':[]}
 u=units[key]
 for field,value in [('aliases',x['id']),('author_labels',x['title']),('process_ids',x['source_process_id']),('process_titles',x['process']),('urls',x['url']),('local_files',x['local_file']),('source_pages',x['source_page'])]:
  if value not in u[field]:u[field].append(value)
 d=dates.get(x['id'])
 if d:
  u.setdefault('date_candidate_files',[]).append({'attachment_id':x['id'],'metadata_text_file':d.get('metadata_text_file'),'metadata_readability':d.get('metadata_readability'),'has_window_date_candidate':d.get('has_window_date_candidate',False)})
 m=manual.get(x['id'])
 if m:u.setdefault('date_adjudications',[]).append({'attachment_id':x['id'],**m});u['date_state']=m['window_state']
 for sid in sg_by_sha.get(sha,[]):
  if sid in u['registered_records']:continue
  s=sg_lookup[sid];u['registered_records'].append(sid)
  for e in s.get('recipient_events',[]):u['sent_events'].append({'register_id':sid,**e,'basis':'registrant-reported delivery event; independently archived byte-identical submitted PDF'})
  u['submission_date_verified']=True;u['date_state']='register_delivery_in_window_subject_to_root_event_date_gate'
 lr=read_by_file.get(x['local_file'])
 if lr and lr.get('depth')!='extracted_only':u['depth']=lr['depth'];u['screened_substantively']=True;u['screen_log_id']=lr['screen_id']
items=list(units.values())
out={'scope':{'window_start':'2026-07-25','window_end':'2026-10-24','snapshot_date':'2026-10-25','purpose':'Enumerate observed public attachments and reconcile versions/dates; not an assertion that every attachment is a window-eligible external submission or substantively screened.','deduplication':'Exact PDF SHA-256 where available; otherwise exact attachment URL. Same bytes linked from multiple processes counted once, all contexts retained. Near-duplicates and annex/package relations need separate checks.','submission_date_rule':'Verified recipient delivery is primary. Document Stand/author date is retained separately; a cited law/draft/deadline date never automatically admits the response.','collection_read_limit':'Automated first-two-page extraction is metadata work, not a content read.'},'stats':{'observed_attachment_urls':len(rows),'byte_or_url_document_units':len(items),'pdf_archived_units':sum(x['archive_state']=='pdf_archived'for x in items),'byte_matched_register_units':sum(bool(x['registered_records'])for x in items),'substantively_screened_units':sum(x['screened_substantively']for x in items)},'document_units':items,'known_limits':['BMWE ordinary HTTP access blocked by challenge; parent browser process captures and Open Data portal datasets are separate ongoing enumeration.','Some labelled submissions are official state/Bundesrat material or attachments/annexes, requiring source-kind/package adjudication before external-response counts.','Undated or scanned historical attachments remain uncertain; absence of a first-two-page date is not proof of exclusion.','Current public snapshot does not prove every attachment was already public by 24 October; late-publication histories may be unavailable.','Unpublished responses are outside publicly readable corpus and are recorded where ministry acknowledges them.']}
(R/'coverage-ministry-document-inventory.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps(out['stats']))
