"""Publish the reading guide and timing metadata only after the requested minimum."""
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'data'

def read(name):
    return json.loads((DATA / name).read_text())

investigation = read('investigation.json')
started = datetime.fromisoformat(investigation['started_at_utc'])
finished = datetime.now(timezone.utc)
elapsed = (finished - started).total_seconds()
if elapsed < investigation['minimum_duration_seconds']:
    raise SystemExit('Minimum research duration has not elapsed; completion metadata was not changed.')
validation = read('validation-report.json')
if validation['errors'] or validation['warnings']:
    raise SystemExit('Resolve outstanding validation items before finalisation.')
findings = read('findings.json')
leads = read('unresolved-leads.json')
rejected = read('rejected-candidates.json')
records = findings + leads + rejected
sources = read('source-registry.json')
counts = Counter(r['severity'] for r in findings)
ancillary = sum(r.get('reporting_tier') == 'ancillary_minor_chronology_or_attribution' for r in findings)
investigation.update({
    'status': 'complete',
    'completed_at_utc': finished.isoformat(),
    'duration_seconds': round(elapsed, 3),
    'counts': {
        'provisional_findings': len(findings),
        'major_provisional_findings': counts['major'],
        'minor_provisional_findings': counts['minor'],
        'ancillary_chronology_or_attribution_findings': ancillary,
        'unresolved_leads': len(leads),
        'rejected_candidates': len(rejected),
        'distinct_submission_documents_with_provisional_findings': len({r['document_id'] for r in findings}),
        'distinct_process_ids_in_all_issue_records': len({r['law_id'] for r in records}),
        'registered_sources': len(sources),
        'source_records_with_local_archives': sum(bool(s.get('local_file')) for s in sources),
    },
    'completion_note': 'Research and adversarial evaluation continued through the minimum period; source, quote, schema and reference checks were completed before this snapshot.',
})
(DATA / 'investigation.json').write_text(json.dumps(investigation, ensure_ascii=False, indent=2) + '\n')
major_rows = '\n'.join(
    f"| `{r['id']}` | {r['card']['the_problem']} |"
    for r in findings if r['severity'] == 'major'
)
minutes = elapsed / 60
text = f'''# German federal legislative submissions: AI screening

Screen date: 24 October 2026. Research ran from {started.strftime('%H:%M:%S')} to {finished.strftime('%H:%M:%S')} UTC ({minutes:.1f} minutes), meeting the requested two-hour minimum. Full timing metadata is in [data/investigation.json](data/investigation.json).

The saved set contains **{len(findings)} provisional findings: {counts['major']} major and {counts['minor']} minor**, plus **{len(leads)} unresolved leads** and **{len(rejected)} rejected candidate**. Of the minor findings, {ancillary} are marked as ancillary chronology or attribution issues. These are distinct issues, not a representative error rate or a count of culpable authors.

## Files

| File | Contents |
| --- | --- |
| [data/findings.json](data/findings.json) | Provisional mismatches that survived context checks and independent AI review. |
| [data/unresolved-leads.json](data/unresolved-leads.json) | Open questions; these are not established errors. |
| [data/rejected-candidates.json](data/rejected-candidates.json) | A suspicion withdrawn after a substantive alternative explanation. |
| [data/source-registry.json](data/source-registry.json) | Source IDs, direct URLs, access/provenance limits and hashes of archived files. |
| [data/documents.json](data/documents.json) | Document metadata and shared request quotations referenced by issue records. |
| [data/review-index.json](data/review-index.json) | Independent AI reviews, reassessments and manual quotation checks. |
| [data/issue.schema.json](data/issue.schema.json) | Machine-readable schema retaining the requested fields. |
| [data/validation-report.json](data/validation-report.json) | Schema, reference, archive and quotation-check results. |

Every issue has `status: ai_screened`; `finding_state` distinguishes its disposition. Severity assesses materiality separately from `favours_author_request`, which describes the direction of the specific issue. For unresolved leads, severity describes potential materiality if the premise is established; any stated favourable direction concerns that tested hypothesis and does not establish an error. Unknown direction is `null`.

The request evidence for BÄK and DZVhÄ is stored once in `documents.json`, with an explicit quotation reference in each affected issue. All source IDs resolve in `source-registry.json`. PDF page numbers are one-based; printed page numbers are recorded separately where needed.

## Major provisional findings

| Issue ID | Narrow correction |
| --- | --- |
{major_rows}

## Method and limits

Four AI agents searched ministry consultation pages, Bundestag hearing materials and the Lobbyregister. They independently re-read primary sources, challenged each other’s cases, checked the addressed draft versions, and recorded competing interpretations and downgrades. Each provisional finding has a saved independent AI review. This is not human specialist confirmation: `review.specialist` remains `null`.

The records distinguish incorrect source descriptions from unknown real-world quantities. They do not treat policy disagreement, uncertain forecasts or absent evidence as proof of error. For example, the cannabis records do not supply a corrected national diagnosis rate or establish the true causal change in traffic deaths. An early mixed-denominator illustration was withdrawn after checking the original treatment report; preserved earlier reviews contain explicit superseding notices.

Some primary documents were accessible only through declared mirrors or indexed official text. Those access limits and any unverified edition identities are disclosed in the relevant records. The current law or a later bill was not substituted for the draft addressed by an author.

The source registry contains {len(sources)} entries, {sum(bool(s.get('local_file')) for s in sources)} with local archives. Mechanical quotation checks distinguish exact extracted matches, line-break normalisation, visually checked reading-order problems, and web/manual checks. Passing file validation does not establish substantive truth.

No author was contacted and no response is recorded. Empty `author_response` arrays mean only that no response is recorded. No intent is inferred. Research notes, negative screens, original PDFs and review history remain under `research/`.

To reproduce assembly and file validation, run `python3 research/build_deliverables.py` followed by `python3 research/validate_deliverables.py`. Original quotations are preserved; the assembly only normalises metadata structure and selected English narrative spacing.
'''
(ROOT / 'README.md').write_text(text)
print(json.dumps({'completed_at_utc': finished.isoformat(), 'duration_seconds': round(elapsed, 3), 'counts': investigation['counts']}, ensure_ascii=False))
