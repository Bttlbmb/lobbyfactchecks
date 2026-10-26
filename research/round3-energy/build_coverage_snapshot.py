import collections
import datetime
import json
import pathlib

B = pathlib.Path('research/round3-energy')
R = pathlib.Path('research/round3-root/coverage')

def read(path):
    return json.loads(path.read_text())

catalogue = read(B / 'coverage-ministry-process-catalogue.json')['processes']
dates = read(B / 'coverage-ministry-date-candidates.json')
manual = read(B / 'coverage-ministry-manual-date-adjudications.json')
logs = read(B / 'screening-log.json')
bt = read(B / 'coverage-environment-transport-statement-metadata.json')
housing = read(B / 'coverage-housing-submission-metadata.json')
bmwe = read(R / 'bmwe-browser-process-records.json')
portal = read(B / 'coverage-bmwe-portal-index.json')
sources = []

for name, count, scope in [
    ('BMV', 41, 'Official 21st-legislature laws page'),
    ('BMWSB', 20, 'Two official process-index pages, including historical entries'),
    ('BMUKN', 246, 'Filtered national ongoing/completed draft index: 246 entries across 13 pages'),
]:
    processes = [p for p in catalogue if p['channel'] == name]
    links = {a['url'] for p in processes for a in p['attachments'] if a['kind'] == 'submission'}
    date_rows = [d for d in dates if d['ministry'] == name]
    sources.append({
        'source': name,
        'index_scope': scope,
        'observed_index_processes': count,
        'captured_process_pages': len(processes),
        'process_page_capture_state': 'closed_for_stated_bounded_index',
        'extra_related_pages_note': 'BMUKN catalogue includes six related pages beyond the 246 filtered draft processes.' if name == 'BMUKN' else None,
        'observed_submission_labelled_urls_all_years': len(links),
        'date_metadata_rows_processed': len(date_rows),
        'manual_date_records': sum(d['id'] in manual for d in date_rows),
        'window_submission_total': None,
        'inventory': 'research/round3-energy/coverage-ministry-document-inventory.json',
        'limits': 'Document, delivery, printing and publication dates are distinct. Historical/undated attachments and official-response/annex scope remain under adjudication. Collection is not substantive screening.',
    })

sources.append({
    'source': 'BMWE',
    'index_scope': 'Parent browser current-process index; completed-process index separate',
    'captured_process_pages_so_far': len(bmwe),
    'process_page_capture_state': 'closed_bounded_current_index' if len(bmwe) == 146 else 'in_progress',
    'portal_dataset_links_observed': len(portal['datasets']),
    'portal_pagination_state': portal['pagination_state'],
    'validated_dataset_downloads': 18,
    'completed_master_process_urls': 141,
    'completed_master_index_pages': 15,
    'completed_process_capture_state': 'All 141 completed-law pages captured and independently reconciled; no submission-labelled response download or Open Data dataset link identified.',
    'completed_master_audit': 'research/round3-reviews/energy-reviews-root-bmwe-browser-coverage.json',
    'window_relevant_dataset_packages': [
        {'name': 'WindSeeG August consultation', 'named_participant_packages': 43, 'explicitly_unpublished': 5, 'public_structured_rows': 34, 'public_pdf_files': 6, 'public_named_participant_rows': 38, 'external_named_contributors': 36, 'external_public_contributors': 32, 'external_withheld_contributors': 4, 'government_named_rows': 7, 'public_multipart_packages_including_government': 37, 'deduplication': '34 structured rows and six PDFs overlap; Hamburg BWAI PDF supplements the joint BWAI+BUKEA structured row. Four PDF-only listed names include this joint government supplement; only three external contributors are PDF-only. Exact delivery dates require document/register checks.'},
        {'name': 'KLtgV', 'named_participant_packages': 13, 'explicitly_unpublished': 2, 'public_pdf_files': 11},
        {'name': 'Wirtschaftsprüferexamen', 'named_participant_packages': 3, 'explicitly_unpublished': 0, 'public_pdf_files': 3, 'date_caution': 'Author dates29September,14October,13October differ from some filename dates; filenames do not prove delivery.'},
        {'name': 'Übertragungsnetzkosten2027–2029', 'named_participant_packages': 24, 'explicitly_unpublished': 1, 'public_pdf_files': 23},
        {'name': 'KrWaff amendments', 'public_pdf_files': 2},
    ],
    'window_submission_total': None,
    'limits': 'Six-page Open Data master pagination closed at observed page6 with no forward link;59datasetURLs observed despite inconsistent displayed totals. All146current-index process URLs captured and reconciled; all141completed-law pages are separately captured and audited, with no additional submission-labelled downloadable response links. EEG July dataset does not close September–October KUEBLL public consultation; UVgO publishes only a blank template, not the response set. Some periods predate window despite page updates. Current snapshot does not establish historical publication state.',
})

for name, rows, hearing_count, metadata in [
    ('Bundestag environment', [x for x in bt if x['channel'] == 'bt-environment'], 13, 'coverage-environment-transport-statement-metadata.json'),
    ('Bundestag transport', [x for x in bt if x['channel'] == 'bt-transport'], 9, 'coverage-environment-transport-statement-metadata.json'),
    ('Bundestag housing', housing, 4, 'coverage-housing-submission-metadata.json'),
]:
    sources.append({
        'source': name,
        'observed_response_pdf_links_all_dates': len(rows),
        'observed_hearing_pages': hearing_count,
        'cover_date_states': dict(collections.Counter(x.get('window_state') for x in rows)),
        'verified_delivery_dates_from_cover_alone': 0,
        'metadata_file': 'research/round3-energy/' + metadata,
        'index_capture_state': 'closed_for_stated_current_legislature_hearing_index',
        'independent_review': 'research/round3-reviews/tax-reviews-energy-coverage-dates.json',
        'limits': 'Covers are printing/distribution metadata, not precise recipient dates. Explicit cover-date and submission-date verification fields take precedence over legacy date_verified. Transport includes one annex and one unresolved year conflict. Economy handled by tax agent.',
    })

out = {
    'updated_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'window': {'start': '2026-07-25', 'end': '2026-10-24', 'primary_date': 'verified submission/recipient delivery', 'author_creation_date': 'separate metadata', 'public_snapshot': '2026-10-25'},
    'scope': 'Energy, environment, housing and transport public ministry/committee sources. Bounded source closure, not a claim of global completeness.',
    'sources': sources,
    'actual_external_pool': read(B / 'pool-audit.json')['summary'],
    'actual_screening': {
        'ledger': 'research/round3-energy/screening-log.json',
        'entries': len(logs),
        'depths': dict(collections.Counter(x['depth'] for x in logs)),
        'new_issue_records': 1,
        'new_provisional_findings': 0,
        'new_unresolved_leads': 1,
        'negative_screens': 'research/round3-energy/negative-screens.json',
        'limits': 'Initial April EnEfG screens predate new window. Metadata/extraction/downloads are not full reads or fact checks.',
    },
    'other_published_structured_responses': {
        'file': 'research/round3-energy/coverage-eusurvey-published-responses.json',
        'ErsatzbaustoffV': 77,
        'RohrFLtgV': 6,
        'individual_submission_timestamps_publicly_available': False,
        'verified_window_total': None,
    },
    'archive_date_metadata': {
        'ministry_pdf_urls_all_years': 4952,
        'unique_pdf_byte_units_archived': 4913,
        'first_two_page_metadata_extracted': 4952,
        'last_two_page_metadata_extracted': 4952,
        'sparse_first_two_page_documents_ocr_extracted': 221,
        'first_two_page_window_date_string_candidates': 123,
        'last_two_page_window_date_string_candidates': 62,
        'ocr_window_date_string_candidates': 4,
        'date_candidate_warning': 'Candidate strings are not eligible submission counts. Four OCR positives visually/context checked; two DAeC URLs are duplicate versions of one joint-draft response. Future policy deadlines excluded from author-date attribution.',
        'manual_date_annotation_records': len(manual),
        'manual_date_file': 'research/round3-energy/coverage-ministry-manual-date-adjudications.json',
    },
    'global_gaps': [
        'Unpublished responses are unreadable. UVP GE1120 explicitly acknowledges five non-public senders; historical GE1057 does too, not automatically a current-window gap.',
        'Root 1558-record register collection remains authoritative for the national register channel; our ministry-recipient filter is only a cross-reference.',
        'Mirrors, annexes, structured/PDF supplements and re-deliveries need version/package deduplication.',
        'No assertion that every archived item has been substantively read or checked.',
    ],
}
(B / 'coverage-closure-snapshot.json').write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'sources': len(sources), 'ledger_entries': len(logs), 'output': str(B / 'coverage-closure-snapshot.json')}))
