# German federal legislative submissions: AI screening

Screen date: 24 October 2026. Research ran from 08:56:30 to 10:56:41 UTC (120.2 minutes), meeting the requested two-hour minimum. Full timing metadata is in [data/investigation.json](data/investigation.json).

The saved set contains **20 provisional findings: 6 major and 14 minor**, plus **11 unresolved leads** and **1 rejected candidate**. Of the minor findings, 5 are marked as ancillary chronology or attribution issues. These are distinct issues, not a representative error rate or a count of culpable authors.

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
| `cannkg2018-baek-a01` | The cited share excludes alcohol and concerns a selected treatment dataset. |
| `cannkg2018-baek-a02` | The matched statistic counts deaths in crashes involving a marijuana-positive operator; it does not establish causation. |
| `enefg2026-dce-a01` | The exception concerns public publication. Mandatory transmission to the federal authority and onward EU reporting remain, with confidentiality safeguards. |
| `enefg2026-vik-a01` | The 2020 quantity is primary energy, not final energy. The 11.7% EU target also uses modelled 2030 consumption from the 2020 reference scenario, not observed pandemic-year consumption. The derived comparison is invalid. |
| `jstg2026-dstg-tax01` | The adopted EU timetable starts it on 1 July 2030. |
| `wassbg2024-waniczek-a01` | An industrial SGT-400 turbine had run on 100% hydrogen in France in 2023. |

## Method and limits

Four AI agents searched ministry consultation pages, Bundestag hearing materials and the Lobbyregister. They independently re-read primary sources, challenged each other’s cases, checked the addressed draft versions, and recorded competing interpretations and downgrades. Each provisional finding has a saved independent AI review. This is not human specialist confirmation: `review.specialist` remains `null`.

The records distinguish incorrect source descriptions from unknown real-world quantities. They do not treat policy disagreement, uncertain forecasts or absent evidence as proof of error. For example, the cannabis records do not supply a corrected national diagnosis rate or establish the true causal change in traffic deaths. An early mixed-denominator illustration was withdrawn after checking the original treatment report; preserved earlier reviews contain explicit superseding notices.

Some primary documents were accessible only through declared mirrors or indexed official text. Those access limits and any unverified edition identities are disclosed in the relevant records. The current law or a later bill was not substituted for the draft addressed by an author.

The source registry contains 136 entries, 95 with local archives. Mechanical quotation checks distinguish exact extracted matches, line-break normalisation, visually checked reading-order problems, and web/manual checks. Passing file validation does not establish substantive truth.

No author was contacted and no response is recorded. Empty `author_response` arrays mean only that no response is recorded. No intent is inferred. Research notes, negative screens, original PDFs and review history remain under `research/`.

To reproduce assembly and file validation, run `python3 research/build_deliverables.py` followed by `python3 research/validate_deliverables.py`. Original quotations are preserved; the assembly only normalises metadata structure and selected English narrative spacing.
