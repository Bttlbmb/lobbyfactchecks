import json,pathlib,concurrent.futures
from coverage_collect_pdfs import one
P=pathlib.Path('research/round3-social');pages=json.load(open(P/'coverage-author-supplement-pages.json'));rows={}
for p in pages:
 for l in p['relevant_links']:
  u=l['url']
  if not u.lower().endswith('.pdf')or'stellungnahmen_2025'in u:continue
  isdraft='Entwurf_7.'in u
  rows[u]={'url':u,'link_title':l['label'],'source_page':p['url'],'source_page_archive':p['archive'],'authority':'author_published_mirror','process':'7thVersMedVamendment2026'if any(w in u.lower()for w in ['versorgungsmedizin','7-vo-vmv','/gdv/'])else'9thBeschVamendment2026','norm_type':'ordinance','document_kind':'addressed_draft'if isdraft else'written_submission','eligibility_status':'not_submission'if isdraft else'date_and_formal_channel_pending','reading_depth':'collected_link_only'}
with concurrent.futures.ThreadPoolExecutor(max_workers=4)as ex:out=list(ex.map(one,rows.values()))
result={'as_of':'2026-10-25','documents':out,'summary':{'PDFfiles':len(out),'stakeholder_response_files':sum(x['document_kind']=='written_submission'for x in out),'addressed_draft_files':sum(x['document_kind']=='addressed_draft'for x in out)},'limits':'SupplementarydiscoveryforprocessesnotfoundinthecompleteBMASindex. Authorspublishedresponsesmaynotbeidenticaltoministryorregisterversions; noindexcompletenessclaim.'}
(P/'coverage-author-supplement-documents.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(result['summary'])
for x in out:print(x.get('local_pdf'),x['document_kind'],x.get('pdf_pages'),x.get('date_candidates'),x.get('error'))
