import json,pathlib,hashlib,collections
R=pathlib.Path('research/round3-root/coverage');B=pathlib.Path('research/round3-energy')
def read(p):return json.loads(p.read_text())
cur=read(R/'bmwe-browser-process-records.json');completed=read(R/'bmwe-completed-browser-process-records.json');ci=read(R/'bmwe-current-browser-pages.json');di=read(R/'bmwe-completed-index-browser-records.json')
expected_cur={a['url']for p in ci for a in p['links']if a.get('text','').strip()=='Öffnet Einzelsicht'}
expected_comp={a['url']for p in di for a in p['resource_links']if '/Redaktion/DE/Gesetze/' in a.get('url','')}
results=[];completed_catalogue=[]
for label,rows,expected in [('current',cur,expected_cur),('completed',completed,expected_comp)]:
 actual={x['url']for x in rows};errors=[];downloads=set();datasets=set();response_links=set();source_hashes=[]
 for x in rows:
  p=pathlib.Path(x['local_file']);b=p.read_bytes();raw=json.loads(b);source_hashes.append({'url':x['url'],'local_file':str(p),'sha256':hashlib.sha256(b).hexdigest()})
  if raw.get('url')!=x['actual_url']or x['actual_url']!=x['url']:errors.append({'url':x['url'],'error':'URL mismatch'})
  if raw.get('title')!=x['page_title']or not raw.get('title'):errors.append({'url':x['url'],'error':'title mismatch/empty'})
  body=raw.get('text','')
  if any(t in body.lower() for t in ['radware','access denied','captcha','seite nicht gefunden']): errors.append({'url':x['url'],'error':'challenge/error body requires review'})
  if len(body)<1200: errors.append({'url':x['url'],'error':'short body requires review'})
  links=raw.get('links',[])
  if {json.dumps(a,sort_keys=True)for a in links}!={json.dumps(a,sort_keys=True)for a in x['resource_links']}:errors.append({'url':x['url'],'error':'manifest vs raw observed anchors differ'})
  resource=[a for a in links if any(e in a.get('url','').lower()for e in ['.pdf','.zip','.xlsx','.docx'])]
  ds=[a for a in links if '/ODP/Redaktion/DE/OpenData/'in a.get('url','')]
  responses=[a for a in resource if 'stellungnahme'in(a.get('url','')+' '+a.get('text','')).lower()]
  downloads.update(a['url']for a in resource);datasets.update(a['url']for a in ds);response_links.update(a['url']for a in responses)
  if label=='completed':completed_catalogue.append({'url':x['url'],'title':x['page_title'],'source_file':x['local_file'],'resource_links':resource,'consultation_datasets':ds,'submission_labelled_links':responses,'depth':'metadata_only','screened_substantively':False})
 results.append({'channel':label,'index_pages':15,'expected_exact_urls':len(expected),'captured_records':len(rows),'captured_unique_urls':len(actual),'missing':sorted(expected-actual),'extra':sorted(actual-expected),'raw_manifest_access_errors':errors,'download_links_all_kinds':len(downloads),'submission_labelled_download_links':len(response_links),'distinct_linked_consultation_datasets':len(datasets),'source_hashes':source_hashes})
(B/'coverage-bmwe-completed-process-catalogue.json').write_text(json.dumps({'processes':completed_catalogue,'depth':'metadata_only','count':len(completed_catalogue),'limits':'Completed-law pages use different URLs from consultation dossiers; conceptual process overlap is not inferred from URL differences.'},ensure_ascii=False,indent=2)+'\n')
out={'review_id':'energy-reviews-root-bmwe-browser-coverage','reviewer':'energy_hearings independent AI','date':'2026-10-25','scope':'Independent metadata/anchor and access-state audit of all captured BMWE current and completed master process pages; not substantive submission screening.','results':results,'conclusion':'Exact URL closure supported for both bounded master indexes. All captured actual URLs/titles/observed anchors reconcile with their raw browser exports; no challenge/error body detected by these checks. No additional submission-labelled downloadable response or Open Data dataset link was identified in the141completed-law page exports. This does not prove absence of unlinked, unpublished or differently labelled responses.','limits':['Displayed index totals were inconsistent across loads; closure is to the actual observed index URL sets, not a stable website-reported total.','Current and completed URL families can describe the same substantive legislative process;287URLs are not287deduplicated processes.','All observed anchors were compared, but PDF/ZIP response classification is a label/URL discovery heuristic. Body text and opaque links may still require manual scope review.','A current25October snapshot is not archived proof of public availability by24October. No individual dispatch date inferred.','Collection and metadata audit are not full reads or every-claim fact checks.'],'manual_short_page_review': 'Five completed-law exports initially fell below1500characters; all five full exported bodies independently read. They are legitimate brief statutory metadata pages (Eichordnung,2009Grundgesetz amendment,UWG,NZV,Telemedien amendment), with no access challenge or response download links. None shorter than1200characters.', 'new_quotations':[]}
pathlib.Path('research/round3-reviews/energy-reviews-root-bmwe-browser-coverage.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print([{k:v for k,v in x.items()if k!='source_hashes'}for x in results])
