# German federal legislative submissions: AI screening

The first research round ran on 24 October 2026 from 08:56:30 to 10:56:41 UTC (120.2 minutes). Its timing metadata remains in [data/investigation.json](data/investigation.json). A second requested research round ran on 25 October 2026 from 00:01:28 to 02:16:46 UTC (135.3 minutes elapsed), with the additional two-hour minimum verified. See [data/investigation-round2.json](data/investigation-round2.json). Original deliverables are preserved in [research/round2/baseline/](research/round2/baseline/).

The current saved set contains **52 provisional findings: 11 major and 41 minor**, plus **26 unresolved leads** and **1 rejected candidate**. Of the minor findings, 7 are ancillary chronology, attribution or index-label issues. These are distinct issues, not a representative error rate or a count of culpable authors. In-progress raw candidates are excluded until their checks are complete.

The reconstructed screening pool contains **at least 343 distinct response versions/contributions**: **325 individually identified screened entries**, plus at least **18 additional keyword-screened members** of a rental-law consultation batch. Recorded depth is 133 full-submission reads, 1 full-text OCR read, 80 selected-passage checks, and at least 129 keyword screens. These are reading-depth categories, not a claim that every assertion in each document was verified. The pool includes three public statements and one oral contribution, labelled separately. Repeated copies and reviews are merged; joint responses count once. One original/corrected response pair counts as two versions. The rental batch log reports 25 screened documents but the archive contains 26, so the additional membership remains uncertain. Three further screens supported only by reconstructed tool history are excluded. See [data/screening-pool-summary.json](data/screening-pool-summary.json) and the entry-level [data/screening-pool.json](data/screening-pool.json).

The 79 issue records concern 64 documents within that wider pool. Of those, 46 documents have provisional findings; 10 have the 11 major findings. The pool was targeted and examined at unequal depths, so these counts do not estimate an overall error rate. Two public statements have unverified formal submission channels; an evaluation response and a general hearing contribution are also explicitly distinguished from exact-draft submissions.

## Files

| File | Contents |
| --- | --- |
| [data/findings.json](data/findings.json) | Provisional mismatches that survived context checks and independent AI review. |
| [data/unresolved-leads.json](data/unresolved-leads.json) | Open questions; these are not established errors. |
| [data/rejected-candidates.json](data/rejected-candidates.json) | A suspicion withdrawn after a substantive alternative explanation. |
| [data/source-registry.json](data/source-registry.json) | Source IDs, direct URLs, access/provenance limits and hashes of archived files. |
| [data/documents.json](data/documents.json) | Document metadata and shared request quotations referenced by issue records. |
| [data/screening-pool.json](data/screening-pool.json) | Deduplicated screening inventory, reading depth, source files, log locators and scope qualifications. |
| [data/screening-pool-summary.json](data/screening-pool-summary.json) | Screening denominator, batch uncertainty and relationship to the issue records. |
| [data/review-index.json](data/review-index.json) | Independent AI reviews, reassessments and manual quotation checks. |
| [data/issue.schema.json](data/issue.schema.json) | Machine-readable schema retaining the requested fields. |
| [data/validation-report.json](data/validation-report.json) | Schema, reference, archive and quotation-check results. |
| [data/quotation-audit.json](data/quotation-audit.json) | Aggregate short-excerpt and source-identity checks; not factual review. |
| [research/round2/completion-audit.json](research/round2/completion-audit.json) | Requirement, provenance, review and timing audit for the second round. |

Every issue has `status: ai_screened`; `finding_state` distinguishes its disposition. Severity assesses materiality separately from `favours_author_request`, which describes the direction of the specific issue. For unresolved leads, severity describes potential materiality if the premise is established; any stated favourable direction concerns that tested hypothesis and does not establish an error. Unknown direction is `null`.

The shared request evidence for BÄK, DZVhÄ and Meyer is stored once in `documents.json`, with an explicit quotation reference in each affected issue. All source IDs resolve in `source-registry.json`. PDF page numbers are one-based; printed page numbers are recorded separately where needed.

## Major provisional findings

| Issue ID | Narrow correction |
| --- | --- |
| `cannkg2018-baek-a01` | The cited share excludes alcohol and concerns a selected treatment dataset. |
| `cannkg2018-baek-a02` | The matched statistic counts deaths in crashes involving a marijuana-positive operator; it does not establish causation. |
| `dac8-2025-dstg-tax-r2-07` | The $3.5 billion is the IRS Criminal Investigation annual crypto-seizure total, including a billion-dollar seizure before the operation started. It is not a measured result or fiscal return of that operation. |
| `enefg2026-dce-a01` | The exception concerns public publication. Mandatory transmission to the federal authority and onward EU reporting remain, with confidentiality safeguards. |
| `enefg2026-vik-a01` | The 2020 quantity is primary energy, not final energy. The 11.7% EU target also uses modelled 2030 consumption from the 2020 reference scenario, not observed pandemic-year consumption. The derived comparison is invalid. |
| `grundsicherung2026-vansuntum-social01` | The matched survey measures recent job-search behaviour in a restricted sample; not searching in four weeks is not a finding of disinterest. Most non-searchers reported health obstacles. |
| `invest2025-eichfelder-tax-r2-03` | Those figures match the top 5% in the primary fiscal-income dataset; its top 1% shares are 8.16% and 14.09%. |
| `jstg2026-dstg-tax01` | The adopted EU timetable starts it on 1 July 2030. |
| `thg2026-hornsteiner-evidence-a01` | Published field measurements provide empirical evidence of increasing greenhouse forcing linked to human emissions. |
| `wassbg2024-waniczek-a01` | An industrial SGT-400 turbine had run on 100% hydrogen in France in 2023. |
| `wolf2026-pfannenstiel-root06` | The cited judgment expressly requires local and national assessment. Cross-border exchange can support favourable status; a favourable European population does not replace the national assessment. |

## Method and limits

Four AI agents searched ministry consultation pages, Bundestag hearing materials and the Lobbyregister. They independently re-read primary sources, challenged each other’s cases, checked the addressed draft versions, and recorded competing interpretations and downgrades. Each provisional finding has a saved independent AI review. This is not human specialist confirmation: `review.specialist` remains `null`.

The records distinguish incorrect source descriptions from unknown real-world quantities. They do not treat policy disagreement, uncertain forecasts or absent evidence as proof of error. For example, the cannabis records do not supply a corrected national diagnosis rate or establish the true causal change in traffic deaths. An early mixed-denominator illustration was withdrawn after checking the original treatment report; preserved earlier reviews contain explicit superseding notices.

Some primary documents were accessible only through declared mirrors or indexed official text. Those access limits and any unverified edition identities are disclosed in the relevant records. The current law or a later bill was not substituted for the draft addressed by an author.

The source registry contains 337 entries, 245 with local archives. Mechanical quotation checks distinguish exact extracted matches, line-break normalisation, visually checked reading-order problems, and web/manual checks. Passing file validation does not establish substantive truth.

No author was contacted and no response is recorded. Empty `author_response` arrays mean only that no response is recorded. No intent is inferred. Research notes, negative screens, original PDFs and review history remain under `research/`.

To reproduce assembly and file validation, run `python3 research/build_deliverables.py` followed by `python3 research/validate_deliverables.py`. Original quotations are preserved; the assembly only normalises metadata structure and selected English narrative spacing.
