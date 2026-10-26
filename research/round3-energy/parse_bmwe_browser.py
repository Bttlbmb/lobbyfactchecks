import json,pathlib,re
R=pathlib.Path('research/round3-root/coverage'); B=pathlib.Path('research/round3-energy')
rows=json.loads((R/'bmwe-browser-process-records.json').read_text());ps=[]
for x in rows:
 ls=x['resource_links'];ps.append({'url':x['url'],'title':x['page_title'],'source_file':x['local_file'],'resource_links':[v for v in ls if any(e in v.get('url','').lower() for e in ['.pdf','.zip','.xlsx','.docx']) and 'Redaktion/DE/' in v['url']],'consultation_datasets':[v for v in ls if 'daten.bundeswirtschaftsministerium.de/ODP/Redaktion/DE/OpenData/' in v.get('url','')],'submission_form_links':[v for v in ls if any(s in v.get('url','').lower() for s in ['konsultation.','eusurvey'])],'depth':'metadata_only','screened_substantively':False,'exact_draft_version':'not verified from metadata alone'})
out={'processes':ps,'captured_processes':len(ps),'capture_expected_current_index':146,'depth':'metadata_only','limits':['All actual observed anchors parsed. Browser current-process capture in progress until146current URLs reconcile.','A page update or draft date is not an individual response date. Submission templates, drafts and response documents remain separate.']}
(B/'coverage-bmwe-browser-process-catalogue.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print('captured',len(ps),'resources',sum(len(x['resource_links'])for x in ps),'datasets',sum(len(x['consultation_datasets'])for x in ps))
for x in ps:
 for v in x['resource_links']:
  if 'stellungnahme' in v.get('text','').lower() or 'stellungnahme' in v.get('url','').lower():print(x['url'].split('/')[-1],v['text'][:70],v['url'])
