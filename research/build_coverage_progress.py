"""Build a transparent progress ledger. Collection is never counted as screening."""
import json,pathlib,collections,datetime
ROOT=pathlib.Path(__file__).resolve().parents[1]
def read(p):return json.loads((ROOT/p).read_text())
def maybe(p):return read(p) if (ROOT/p).exists() else None
base='research/round3-root/coverage/'
protocol=read('research/round3/coverage-protocol.json')
reg=read(base+'register-window-records.json');archives=read(base+'register-archive-manifest.json')
rows=archives['records'];valid=[r for r in rows if r.get('status')=='archived_not_screened']
hashes={r['sha256']:r for r in valid}
root_sources=[]
for authority,inventory,key,fetchlog in [
 ('BMJV current',base+'bmjv-current-processes.json',None,base+'bmjv-process-fetch-log.json'),
 ('BMJV archived',base+'bmjv-archived-processes.json','processes',base+'bmjv-all-archived-process-fetch-log.json'),
 ('BMLEH',base+'bmleh-process-inventory.json','processes',base+'bmleh-all-process-fetch-log.json'),
 ('BMI',base+'bmi-browser-process-queue.json',None,base+'bmi-browser-process-records.json')]:
 d=read(inventory);p=d[key] if key else d;f=maybe(fetchlog) or []
 if isinstance(p,dict):p=p.get('processes',p.get('records',[]))
 root_sources.append({'authority':authority,'channel':'ministry','observed_process_urls':len(p),'process_pages_collected':len(f),'inventory':inventory,'page_ledger':fetchlog,'scope_date_version_adjudication':'in_progress','eligible_window_document_total':None,'complete_screening':False,'limits':'Process indexes contain older rounds and adjacent material. Collection counts do not count screened submissions.'})
root_sources.append({'authority':'BKM','channel':'ministry','observed_process_headings':7,'observed_PDF_links':len(read(base+'bkm-resource-inventory.json')),'resource_inventory':base+'bkm-resource-inventory.json','scope_date_version_adjudication':'in_progress','eligible_window_document_total':None,'complete_screening':False})
root_sources.append({'authority':'Bundeskanzleramt / central government consultation navigation','channel':'supplementary_ministry_frame','index_enumeration_status':'unresolved_navigation_and_process_crosscheck','eligible_window_document_total':None,'complete_screening':False,'limits':'Historical central URLs are unavailable. Bundestag and register references discover processes, but do not prove a complete chancellery consultation index.'})
root_hearings=read(base+'bt-root-hearing-index-closure.json')
for x in root_hearings:
 root_sources.append(dict(x,channel='Bundestag_hearing_index',eligible_window_document_total=None,complete_screening=False,limits='All indexed entries, including future, older and non-legislative sessions. Closed index enumeration does not establish all submissions read or all unlisted contributions located.'))
for name in ['a03_auswaertiges','entwicklung','geschaeftsordnung']:
 root_sources.append({'authority':name,'channel':'Bundestag','index_enumeration_status':'no_dedicated_hearing_index_located_on_captured_portal','supplementary_publication_index':'see_captured_document_tables; development_has_no_embedded_table','complete_screening':False,'eligible_window_document_total':None})
document_tables=read(base+'bt-root-document-publication-index.json')
for table in document_tables['tables']:
 root_sources.append({'authority':table['job']['committee'],'channel':'Bundestag_general_document_table','index_enumeration_closed':table['enumeration_closed'],'stop_reason':table['stop_reason'],'published_document_rows':len(table['records']),'index_pages_captured':len(table['pages']),'ledger':base+'bt-root-document-publication-index.json','eligible_window_document_total':None,'complete_screening':False,'limits':'All returned publication history. Official agendas, protocols, government material and older entries included. Publication date is not delivery date; only document-level scope and version reconciliation establishes submissions.'})
for item in read(base+'bt-special-portal-fetch-log.json'):
 root_sources.append({'authority':item['committee'],'channel':'Bundestag_supplementary_portal','portal_captured':True,'scope_notes':item['scope_notes'],'ledger':base+'bt-special-portal-fetch-log.json','eligible_window_document_total':None,'complete_screening':False})
snapshots={b:read('research/round3-'+b+'/coverage-closure-snapshot.json') for b in ['energy','tax','social']}
out={
 'id':'three-month-coverage-progress','status':'in_progress','as_of_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'window':protocol['window'],'protocol':'research/round3/coverage-protocol.json',
 'full_three_channel_coverage_established':False,
 'eligible_distinct_authored_window_versions':None,'eligible_versions_substantively_screened':None,'coverage_percentage':None,
 'why_denominator_is_null':'Scope, delivery-date and authored-version adjudication is incomplete across all channels. No file-link, SG-record, PDF-hash or reading-ledger count is substituted for the final eligible document denominator.',
 'register_collection':{
  'native_filtered_records':len(reg['records']),'unique_SG_ids':len({r['id'] for r in reg['records']}),
  'actual_PDFs_archived':len(valid),'distinct_binary_PDF_hashes':len(hashes),
  'physical_pages_summed_over_records':sum(r.get('extracted_pages',0) for r in valid),
  'physical_pages_one_per_binary_hash':sum(r.get('extracted_pages',0) for r in hashes.values()),
  'OCR_or_visual_required_records':sum(r.get('readability')=='ocr_or_visual_read_required' for r in valid),
  'stage':'native_filtered_collection_complete; scope_and_authored_version_adjudication_and_substantive_review_in_progress',
  'metadata_ledger':base+'register-window-records.json','archive_ledger':base+'register-archive-manifest.json',
  'independent_review':'research/round3-reviews/tax-reviews-root-register-census.json',
  'limits':['Registrant-reported delivery dates, not independently proved actual dispatch events.','An SG disclosure record is not necessarily an eligible legislative response; registrant may differ from document author.','Binary hash identity is only one deduplication layer; covers, redactions and supplements need authored-version reconciliation.','This is a25October retrieval snapshot. Later filings or corrections can change the publicly returned set.','No collection or extraction operation is credited as a substantive screen.']},
 'bounded_public_reading_proofs':'data/bounded-coverage.json',
 'cross_channel_copy_candidates':{'binary_crosswalk':base+'global-register-archive-crosswalk.json','matched_register_records_binary':read(base+'global-register-archive-crosswalk.json')['matched_register_records'],'text_crosswalk':base+'global-register-text-mirror-candidates.json','text_candidate_groups':read(base+'global-register-text-mirror-candidates.json')['full_text_candidate_groups'],'register_records_in_text_candidate_groups':read(base+'global-register-text-mirror-candidates.json')['register_records_in_candidate_groups'],'independent_review':'research/round3-reviews/social-reviews-global-register-crosswalk.json','limits':'Exact bytes or normalized extraction equality only. Visual authorship, scope, date and version checks remain; no automatic reading or eligibility admission.'},
 'root_channels':root_sources,'root_resource_collection':{'observed_resource_occurrences':len(read(base+'root-all-observed-resources.json')),'statement_labelled_URL_candidates':len(read(base+'root-statement-resource-queue.json')),'initial_archive':base+'root-statement-resource-archive.json','supplemental_archive':base+'root-supplemental-resource-archive.json','initial_valid_PDF_or_ZIP_resources':sum(r.get('archive_status')=='archived_not_screened' for r in read(base+'root-statement-resource-archive.json')['records']),'additional_valid_resources':sum(r.get('archive_status')=='archived_not_screened' for r in read(base+'root-supplemental-resource-archive.json')['records']),'ZIP_member_PDF_occurrences':len(read(base+'root-package-members.json')['records']),'deferred_URL_candidates':len(read(base+'root-deferred-resource-queue.json')),'limits':'Includes historical processes, containers, annexes, index sheets, government responses and unadjudicated resources. These are not eligible submission or screening counts. Initial467BMIURLsfailedactualPDFvalidation; do not count notice/errorHTML.'},'domain_snapshot_files':{b:'research/round3-'+b+'/coverage-closure-snapshot.json' for b in snapshots},
 'domain_snapshots':snapshots,
 'bounded_completed_known_public_subcorpora':[{'process':'First2026RSVordinance amendment','proof':'research/round3-social/coverage-rsv-proof.json','distinct_known_public_authored_versions_fully_read':8,'physical_pages':20,'material_findings_established':0,'independent_review':'research/round3-reviews/root-reviews-rsv-coverage.json','limits':'Known public corpus closure subject to metadata, indexing and unpublished-response limits. Historical price claims remain unverified; one incidental commencement-day mismatch is recorded. Does not close the national three-month frame.'}],
 'common_completion_gates':{
  'authoritative_enumeration_all_channels':False,'scope_and_date_adjudication':False,'authored_version_deduplication':False,
  'access_and_readability_gaps_resolved':False,'every_eligible_version_fully_screened':False,'independent_review_of_all_proposed_findings':'required_per_issue; see issue review records'},
 'active_gaps':['BMF current index security challenge; cached variants are incomplete and inconsistent.','BMFTR ministry access gap.','Ministry master indexes omit some independently discovered consultation rounds.','Publications can be workbook rows, ZIP-contained PDFs or supplements, not just directly linked PDF files.','Some participant lists expressly withhold responses; these cannot be content-checked from public sources.','Committee publication covers, author dates, hearing dates and actual delivery dates differ.','Root12general committee document tables enumerated to published no-results; document-level scope, delivery, and special-body supplementary closure remain open.','The full factual screening backlog remains much larger than the completed reading subset.'],
 'permitted_summary':'An audited register collection and ministry/hearing inventories are established or in progress. Full national three-month substantive coverage is not yet established. No error prevalence estimate is supported.'}
(ROOT/'data/coverage-progress.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'register_records':len(reg['records']),'PDFs':len(valid),'binary_hashes':len(hashes),'root_source_rows':len(root_sources),'full_three_channel_coverage_established':False}))
