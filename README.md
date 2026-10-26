# Claim Monitor

A static public website showing provisional, AI-screened checks of submissions to German federal lawmakers. The site is generated from the structured research records in `data/`. It needs no server application, database, API key or JavaScript build tool.

## Build and preview

Use Python 3.10 or newer:

```sh
python3 site/build_static.py
python3 -m http.server 8000 --bind 127.0.0.1 --directory dist
```

Open [the local preview](http://127.0.0.1:8000). The build validates the public file set, finding identities, source/document references and internal links, including compatibility with GitHub Pages repository subpaths. It uses only Python's standard library and makes no network requests. `dist/` is generated and ignored by Git.

## Publish later on GitHub Pages

This folder is a local Git repository on `main`. No GitHub repository, remote or deployment is created by the local build. When ready, create an empty public GitHub repository, add its URL as `origin`, and push `main`. In the GitHub repository, choose **Settings → Pages → Build and deployment → Source → GitHub Actions**. Run the **Static site and GitHub Pages** workflow if the first push happened before Pages was enabled.

The included [workflow](.github/workflows/pages.yml) builds and checks pull requests and publishes pushes to `main` after Pages is configured. Only the generated `dist/` directory is uploaded. See [publishing and maintenance](docs/publishing.md) for commands and the distinction between website checks and original-source research validation. The setup follows [GitHub's custom Pages workflow documentation](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages).

## Repository contents

| Path | Purpose |
| --- | --- |
| `site/` | HTML templates, styles and Python static-site builders. |
| `data/` | Current findings, unresolved/rejected decisions, source metadata and research summaries. |
| `research/` | Authored research records, review history, protocols, provenance and research tools. |
| `docs/publishing.md` | Local preview, GitHub Pages setup and maintenance. |
| `dist/` | Generated public website, including evidence pages and selected JSON records; ignored by Git. |

Downloaded sources, full extracted text, browser captures, credentials, temporary files and local caches are excluded from Git. Existing local source files remain in place for research builders and quotation validation. A fresh clone can build the public website without those downloads; it cannot automatically repeat every original-source check. Historical archive paths in research records describe the research workspace, not guaranteed files in a clone or on the public site.

No open-source licence has been selected. Third-party source documents retain their respective rights and terms. The results remain provisional; the research limitations below and on the site's **About & data** page apply.

## Research record: German federal legislative submissions

The first research round ran on 24 October 2026 from 08:56:30 to 10:56:41 UTC (120.2 minutes). Its timing metadata remains in [data/investigation.json](data/investigation.json). A second requested research round ran on 25 October 2026 from 00:01:28 to 02:16:46 UTC (135.3 minutes elapsed), with the additional two-hour minimum verified. See [data/investigation-round2.json](data/investigation-round2.json). Original deliverables are preserved in [research/round2/baseline/](research/round2/baseline/).

The current saved set contains **69 provisional findings: 13 major and 56 minor**, plus **38 unresolved leads** and **3 rejected candidates**. The latest targeted research added six provisional findings across five submissions: two major and four minor. These are distinct issues, not a representative error rate or a count of culpable authors. Corrections do not by themselves refute the authors’ policy requests. Unresolved leads remain separate from provisional findings.

The third research round ran from 02:41:17 to 05:11:51 UTC on 25 October 2026 (150.6 minutes), satisfying the requested additional 2.5 hours. See [investigation-round3.json](data/investigation-round3.json) and its [completion audit](research/round3/completion-audit.json). This round prioritised a coverage census for **25 July–24 October 2026**, using submission/recipient-delivery dates, with author and publication dates retained separately. The [coverage protocol](research/round3/coverage-protocol.json) defines the completion gates, and [coverage-progress.json](data/coverage-progress.json) records achieved stages and open gaps. The author scope is all external written submissions, including academics and NGOs; Lobbyregister membership is a separate attribute. **Complete three-month screening has not been established.** All 1,558 entries returned by the Lobbyregister delivery-date filter have been collected and independently audited; these are disclosure records, not 1,558 checked or eligible legislative submissions. Ministry and hearing inventories, scope/date checks, deduplication and substantive reviews remain in progress. A historical 2022 candidate was downgraded to an unresolved lead after further independent review distinguished the author’s methodological inference from a demonstrable source misquotation.

The current broad reading ledger contains **791 individually identified response versions/contributions**: **554 full-submission reads**, **1 full-text OCR read**, **108 selected-passage checks**, and **128 keyword screens**. These describe reading depth, not independent verification of every assertion. Repeated copies and reviews merge; joint responses count once. The ledger includes government replies, public statements, an oral contribution and papers whose legislative scope remains pending. Author-role and fixed-window eligibility remain unresolved for many entries, so this broad count is not a verified count of external submissions in the three-month window. See [screening-pool-summary.json](data/screening-pool-summary.json) and the [entry-level ledger](data/screening-pool.json).

The previous audit baseline was at least 343 units, including an anonymous lower bound of 18 rental-consultation responses. Fresh named keyword checks now document the 19 previously unrecorded members, alongside seven earlier deeper reads, so all 26 members have individual records. No anonymous batch bound is added to the current count. The original 25-versus-26 logging discrepancy remains preserved in the historical baseline; it has not been retroactively rewritten. See the [reconciliation proof](research/round3-root/rental-reconciliation-proof.json) and its [independent audit](research/round3-reviews/social-reviews-rental-pool-reconciliation.json).

The **110 issue records concern 87 documents**. **60 documents have provisional findings; 12 have the 13 major findings**. The pool is targeted, historical and examined at unequal depths. Dividing these counts does not estimate the error rate in federal legislative submissions. The national three-month denominator and coverage percentage remain `null`. Fourteen finite published-response sets or register-derived packages have saved full-reading proofs, with their different date, author-role, exact-draft and substantive-check limits in [bounded-coverage.json](data/bounded-coverage.json).

The fourth, targeted follow-up ran from **05:32:40 to 06:32:46 UTC on 25 October 2026** (60.1 minutes), satisfying the additional one-hour minimum. Its [timing report](data/investigation-round4.json) and [completion audit](research/round4/completion-audit.json) record the result. Its [admission manifest](research/round4/assembly-manifest.json) separates findings from unresolved leads and negative checks. The [reading-count reconciliation](research/round4/reading-delta.json) shows 61 additions to the ledger, including eight reads from the immediately preceding pilot and 53 other admissions reported in the round’s logs. Four existing baseline documents were checked again and add no new unit. These additions are not 61 independently timestamped first screens during the hour, or 61 verified in-window legislative submissions.

The three new minor findings are: an AG SBV debt-advice cost table whose printed components exceed its total by EUR 7,700 per post; a DStV statement that all compulsory tax returns require Anlage N despite official exceptions; and a SVDGV universal first-day price-ceiling description despite explicit exceptions. The AG SBV national difference is conditional on accepting the printed component inputs: EUR 25.795 million, not a demonstrated real funding shortfall. Its direction is unknown; the two categorical scope errors narrowly support the authors’ requests. The three source-description questions were initially unresolved and not counted as errors. A later follow-up closed the SVDGV cost allegation as unproven and retained the other two as unresolved. The potentially major BVTE tobacco-tax claim faithfully repeats a cited 2014 industry chart, but its complete original total-forecast baseline remains unauthenticated; contemporary primary evidence also confirms some fiscal disappointment. The late source-category lead supersedes its earlier research-only disposition, without promoting it to a finding. The alcohol-tax, Android-access arithmetic, plastics-cost, capacity-reserve and several energy/transport leads did not support new findings after checking the original evidence. No intent or human specialist confirmation is inferred.

The fifth follow-up specifically reassessed those three existing leads using additional primary evidence and reciprocal independent AI checks. **No new error was established.** SVDGV’s cost allegation is now `rejected_after_review`: the identified component estimate and later system-financing rule do not settle its wider pathway criticism. BVTE remains unresolved: the exact cited 2014 chart is authenticated, identified official forecast vintages differ, and one later chart-year value matches a genuine forecast; no corrected EUR 8.4 billion aggregate is established. Wir’s likely 86% recipient statistic is now matched to the exact official table and earlier author wording, but the intended work-share interpretation remains open. These reassessments add no new target units to the 626-unit pool. Earlier and later author papers are separately logged as evidence context, rather than silently increasing the screening denominator. See [investigation-round5.json](data/investigation-round5.json).

## Sixth targeted research round: short submissions and experts

The sixth round ran from **10:54:33 to 12:24:51 UTC on 25 October 2026** (90.3 minutes), satisfying the additional 90-minute minimum. It prioritised comparatively short documents and named experts after the user’s steering. Its [six new findings](data/findings-round6.json) comprise two provisional major findings: DAI describes private pension contributions as doubly taxed although the addressed draft distinguishes taxation of their income component; ITAD treats a voluntary recycling statistic as the EU target-compliance baseline although Eurostat separates the two reporting methods. The ITAD record prominently preserves a conflicting Destatis description that supports the author’s reading; no invented statistic or intent is alleged.

The four minor findings concern ITAD’s 40%/20% waste-target description, Biesemann’s billion/million port-finance figure, Marburger Bund’s annual office-cost figure and IVD’s count of years above 3% inflation. Each record explains materiality separately from direction and limits the policy implications. A French restaurant-VAT owner-share lead remains unresolved after differing AI reviews; an IVD mandatory-vacating allegation was rejected after checking its conditional context.

The [reading reconciliation](research/round6/reading-delta.json) records **173 branch resource rows**, merging to **170 distinct groups touched**: **166 new broad reading groups and four existing groups rechecked**. The net increase from 626 to 791 is **165**, because a pre-existing duplicate was also merged. Two differently packaged VdK copies count once. Of the 166 additions, 149 were full reads and 17 selected-passage checks. Historical statements and scope-pending papers remain labelled; this is not a completed recent-submission cohort or a representative yield estimate. Timing, case admission and independent review details are saved in [investigation-round6.json](data/investigation-round6.json) and the [completion audit](research/round6/completion-audit.json).

## Unresolved follow-up, 26 October 2026

The **56 unresolved assessments** from the latest short-document pass have now received targeted primary-source follow-up and independent cross-review. **13 are supported at their stated scope; 43 remain unresolved**, each with a specific blocker and next step. New evidence settles the rounded RSV price comparison; other resolutions correct earlier demands that exceeded the actual statement, such as requiring a national frequency survey for a claim that an identifier is not available in every transaction. No new main finding was admitted.

Three researchers froze their proposals before reviewing one another's work. All **56 cases** received individual peer review and root adjudication. Applying the separate follow-up to the previous 201-assessment snapshot gives **156 supported, 43 unresolved and two contradicted**. Earlier ledgers, reviews and reports remain unchanged. This follow-up concerns assessments in **16 existing originals / 53 physical pages**; it adds **zero reading units** and does not cover the separate **38 main unresolved leads**.

Open the [updated follow-up report](research/factual-checks/unresolved-followup-20261026/report.html), [resolution ledger](research/factual-checks/unresolved-followup-20261026/resolution-ledger.json), [adjudication](research/factual-checks/unresolved-followup-20261026/adjudication.json) or [completion audit](research/factual-checks/unresolved-followup-20261026/completion-audit.json). The report distinguishes new evidence from methodological reassessment and retains access, historical-version, population and causal limits. Rebuild with `python3 research/build_resolution_followup.py`.

## Previous short-document factual-check snapshot

This further pass rechecked **20 previously examined expert and association responses / 63 physical PDF pages**. It met the additional **90-minute active-work minimum**; the wall-clock pause is excluded. Every target is **one to six pages**: eight RSV responses, seven land-register identifier responses, two accountant-examination responses and three formal external IT-components responses. The IT subset does not represent all twelve replies on that consultation page.

Three researchers independently inventoried the originals, then each reviewed another researcher’s complete documents and all recorded claims. The **201 final assessments comprise 143 supported, 56 unresolved and two contradicted**. All **197 initial assessments** received individual peer reviews; root independently assessed four additional premises identified by peers. **No new substantive finding or main unresolved lead was admitted.** One contradicted assessment repeats an existing deadline issue; the other concerns an incidental one-day commencement description.

Final semantic review retained uncertainty about undetermined future commencement dates, historical interface denial, the effect of rollout funding and matched historical drug prices. It preserved reasonable contextual interpretations, including “primary source” rather than a claim of historical priority. These assessed uncertainties remain in the claim ledgers and do not automatically enter the main unresolved-lead count.

Open the [combined short-document report](research/factual-checks/short-statements-20261025/overview/report.html), [summary](research/factual-checks/short-statements-20261025/overview/summary.json), [round protocol](research/factual-checks/short-statements-20261025/round-protocol.json), [completion audit](research/factual-checks/short-statements-20261025/overview/completion-audit.json) or [source-retention record](research/factual-checks/short-statements-20261025/source-retention.json). Earlier raw inventories, peer disagreements and superseded root decisions remain preserved. Repeat checking adds **zero reading units**: the pool stays at **791**, with factual annotations now attached to **79 existing responses**. These finite sets do not establish national coverage or an error rate.

## Systematic factual-check pilot

A second pass re-read all **seven published external responses to the CO₂ pipeline ordinance (KLtgV), 35 author pages**, including the six documents with no new finding. Three researchers built claim inventories independently and then each reviewed another researcher’s complete inventory and original pages. Root separately checked the legal/draft baseline and adjudicated disagreements and omissions. The set was chosen because it was a finite, already archived consultation with no previous finding, not for expected error yield.

The final **111 claim assessments comprise 75 supported, 35 unresolved and one narrow overstatement**. These are bounded factual, technical, draft-description and interpretive assessments; supported does not certify every assertion, and unresolved is not an error. All 108 initial assessments received a separate peer review; three additional premises identified during adjudication were independently checked by root. The saved reviews preserve an initial proposed climate-necessity overstatement that was not admitted after contextual review. No new major finding emerged.

The one admitted provisional minor finding concerns CMA’s assertion that transport pipelines cross borders and traverse several Länder “by definition”. The relevant statutory definitions contain no border-crossing condition. Correcting the premise leaves the broader case for nationwide uniform procedures intact. The 35 unresolved pilot assessments stay in the claim ledger; they are not automatically added to the main unresolved-issue count.

Open the [readable report](research/factual-pilot/report.html), [full claim ledger](research/factual-pilot/claim-ledger.json), [protocol](research/factual-pilot/protocol.json), [final adjudication](research/factual-pilot/adjudication.json) or [validation](research/factual-pilot/validation-report.json), [independent integration audit](research/factual-pilot/reviews/b-final-integration-audit.json) or [completion audit](research/factual-pilot/completion-audit.json). Each record retains original-page locators, evidence, access and temporal limits, and peer-review references. The draft’s 7/8 July version distinction, unauthenticated delivery dates and unavailable full standards remain explicit. Repeated checks add **zero documents** to the 626-unit reading ledger; this pilot establishes neither national coverage nor an error rate.

Rebuild the pilot with `python3 research/factual-pilot/build_pilot.py`. The main assembly manifest admits only its separately reviewed minor issue. After main assembly, `python3 research/build_screening_pool.py` and `python3 research/build_bounded_coverage.py` reproduce the linked coverage annotations without adding reading units.

## Expanded factual checks

The extension re-read two more bounded archived external-response sets: **nine BEHG hearing responses / 60 physical PDF pages** and **21 network-cost subsidy responses / 71 physical PDF pages**. The checks use primary evidence beyond each author’s citations. Three researchers independently built inventories, then reviewed every claim and every original page in another researcher’s allocation. All **378 initial assessments** received individual cross-reviews; root adjudicated all 11 omission entries, extending one existing assessment and adding ten separately checked premises.

The final **388 assessments comprise 268 supported, 119 unresolved and one narrow overstatement**. The one admitted provisional minor finding concerns Fleischmann’s claim of a five-to-fifteen cold/heat mortality ratio in every European country. The corrected cited study’s urban country-grouped estimates fall outside both boundaries. The larger aggregate cold burden and approximately six-to-one German urban-cohort ratio remain; actual whole-population national ratios and the effect of future warming are not established. Direction is recorded as unknown because the deviations are mixed. **No new major finding and no network-cost finding were admitted.**

Fresh final reviewers found reasonable contextual alternatives for the infrasound perception-threshold and BKM craft-tax candidates. Both remain unresolved despite earlier narrow-overstatement recommendations, with disagreements preserved. Other checks distinguish conditional forecasts from observations, direct programme eligibility from indirect benefits, annual emissions budgets from auction supply, and tariff reductions from immediate universal customer savings. Missing contemporaneous versions do not become author-error findings.

Open the [combined report](research/factual-checks/report.html), [BEHG ledger](research/factual-checks/behg-2026/claim-ledger.json), [network-cost ledger](research/factual-checks/netzkosten-2026/claim-ledger.json), [completion audit](research/factual-checks/completion-audit.json), [independent integration audit](research/factual-checks/reviews/b-final-integration-audit.json) or [workflow code audit](research/factual-checks/reviews/a-workflow-code-audit.json). Frozen inventories and reviews remain separate from root corrections and explicit issue admissions. Existing issue records remain unchanged. Rechecking adds **zero units** to the existing 626-unit reading ledger; all 37 original-and-extension response records have linked assessment annotations. These finite sets establish neither national completeness nor an error rate.

## Further checks of short statements and expert evidence

The continuation prioritised short expert and association statements in three previously examined sets: **six driving-instruction responses / 31 physical pages**, **seven Frühstartrente responses / 50 pages**, and **nine BioStoffV responses / 39 pages**. **Twenty of the 22 target documents are eight pages or fewer**; the other two are 11 and 14 pages. Long bills, statutes and studies were used as supporting evidence through relevant passages. The BioStoffV set includes eight clearly external responses and one DGUV response whose external-author boundary remains pending.

The **401 final claim assessments comprise 231 supported, 169 unresolved and one existing overstatement**. All **390 initial assessments** received independent review against the complete counterpart originals; peers identified **11 additional premises**, separately assessed by root. **No new finding or main unresolved lead was admitted.** The existing vzbv allocation finding and DGAUM bibliography findings are not counted again. A new medical-latency hypothesis remained unresolved after independent contextual reviews; diagnostic timing was not treated as a universal maximum onset time. Current BioStoffV draft content does not authenticate the earlier August version addressed by authors. Correct legal locators, timing exceptions and uncertainty about compound claims are explicit.

Open the [continuation report](research/factual-checks/continuation-20261025/report.html), [summary](research/factual-checks/continuation-20261025/summary.json), [completion audit](research/factual-checks/continuation-20261025/completion-audit.json) or [independent final integration audit](research/factual-checks/continuation-20261025/reviews/c-final-integration-audit.json). The [initial inventory freezes](research/factual-checks/continuation-20261025/initial-freezes.json), original reviews and root adjudications preserve disagreements. This pass adds **zero reading units** and links factual-assessment annotations to **59 existing response records**. This continuation changes no existing issue. At final integration, **101 of the 102 starting issue objects matched exactly**; the separate Round6 task shortened one older lead’s quotation and added context/history without changing its factual disposition. The starting reading pool was **626**; a concurrent research round is adding other reading units and issues to the shared project totals. Those additions belong to that separate round. Earlier completed reports and audits retain their original snapshots; this later audit covers this continuation and records the concurrent changes separately.

Current report and strict-validator archive dependencies are listed in [source-retention.json](research/factual-checks/continuation-20261025/source-retention.json), supplementing frozen source metadata under the MVP storage policy. No national coverage, representative error rate, author intent or human specialist confirmation is inferred.

## Reusable factual-check workflow

The batch assembler is now configurable. Each new bounded response set supplies a `protocol.json` with original PDF hashes, physical page counts, draft/version limits and researcher allocations; separate frozen `agents/claims-*.json` inventories; full-document cross-reviews bound to inventory hashes; and a final `adjudication.json` resolving every challenge and omission. The shared [claim schema](research/factual-checks/claim.schema.json) retains supported and unresolved assessments alongside potential errors.

Run `python3 research/build_factual_batch.py research/factual-checks/<batch>` to validate and assemble a completed batch. It checks the original snapshots, page coverage, claim anchors, source references, archived hashes, schema, independent reviews and adjudication. `--render-only` refreshes the readable report without changing the saved JSON snapshots. `python3 research/build_factual_index.py` builds the combined entry point for the batches listed in [extension-protocol.json](research/factual-checks/extension-protocol.json). To reproduce this later continuation without replacing the earlier entry point, run `python3 research/build_factual_index.py --config research/factual-checks/continuation-20261025/protocol.json`.

A batch ledger does not automatically add issues to the main findings or unresolved-lead files. A separate `assembly-manifest.json` explicitly admits only final reviewed issue records. The reading and bounded-coverage builders attach completed assessments to existing units, preserving the reading denominator. Adding another batch therefore reuses the validation and assembly code while still requiring fresh primary-source research and independent full-context review.

## MVP storage policy

Keep research results and provenance, rather than mirrors of public source collections. Download documents into a system temporary directory (or disposable `.cache/sources/` when resuming work), check them, and remove the downloads afterward. Do not bulk-archive census PDFs, fetched websites, ZIP bundles, extracted text, OCR or rendered pages by default. Keep a single local snapshot only when a current report or validator needs it, or its exact historical evidence would be difficult to recover. Record the reason for that exception in the source metadata. Contributor instructions are in [AGENTS.md](AGENTS.md).

The 25 October 2026 cleanup removed recoverable downloads while retaining the current site, structured data, authored notes, review records and source assets required by the current reports and validation. [research/cache-manifest.json](research/cache-manifest.json) records each removed download's original path, URL, byte size, SHA-256 and ZIP member name where applicable. Older inventories, archive counts and audit hashes describe the research snapshot when they were created, not the current on-disk cache. Their historical records have been preserved.

To list evicted files, run `python3 research/source_cache.py --list`. Restore an individual source with `python3 research/source_cache.py research/path/from/the/manifest.pdf`. Restoration verifies the recorded hash and refuses to overwrite an existing different file or accept changed source bytes. Public URLs may change or stop working; in that case re-check the live source and record the limitation instead of assuming the old evidence still applies. No network request occurs unless a restore path is supplied. Current quotation validation and factual-batch rebuilds retain their required local source assets.

## Files

| File | Contents |
| --- | --- |
| [data/findings.json](data/findings.json) | Provisional mismatches that survived context checks and independent AI review. |
| [data/unresolved-leads.json](data/unresolved-leads.json) | Open questions; these are not established errors. |
| [data/rejected-candidates.json](data/rejected-candidates.json) | Suspicions closed after context checks failed to establish a factual contradiction. |
| [data/source-registry.json](data/source-registry.json) | Source IDs, direct URLs, access/provenance limits and hashes of archived files. |
| [data/documents.json](data/documents.json) | Document metadata and shared request quotations referenced by issue records. |
| [data/screening-pool.json](data/screening-pool.json) | Deduplicated screening inventory, reading depth, source files, log locators and scope qualifications. |
| [data/screening-pool-summary.json](data/screening-pool-summary.json) | Screening denominator, batch uncertainty and relationship to the issue records. |
| [data/coverage-progress.json](data/coverage-progress.json) | Three-month source census, progress stages and explicit incomplete-coverage gates. |
| [data/bounded-coverage.json](data/bounded-coverage.json) | Finite full-reading proofs, without a national completeness or prevalence claim. |
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
| `fruehstart2026-dai-doubletax-tax-r6-01` | The draft distinguishes unfunded private contributions and income-component taxation; it does not tax the same contributed principal twice. |
| `krwg2026-itad-recycling-method-energy-r6-01` | Eurostat’s voluntary recycling series is not the compliance measure for the 2025/2030/2035 targets. The alternative series changes the baseline; the record preserves contrary Destatis wording. |

## Method and limits

Four AI agents searched ministry consultation pages, Bundestag hearing materials and the Lobbyregister. They independently re-read primary sources, challenged each other’s cases, checked the addressed draft versions, and recorded competing interpretations and downgrades. Each provisional finding has a saved independent AI review. This is not human specialist confirmation: `review.specialist` remains `null`.

The records distinguish incorrect source descriptions from unknown real-world quantities. They do not treat policy disagreement, uncertain forecasts or absent evidence as proof of error. For example, the cannabis records do not supply a corrected national diagnosis rate or establish the true causal change in traffic deaths. An early mixed-denominator illustration was withdrawn after checking the original treatment report; preserved earlier reviews contain explicit superseding notices.

Some primary documents were accessible only through declared mirrors or indexed official text. Those access limits and any unverified edition identities are disclosed in the relevant records. The current law or a later bill was not substituted for the draft addressed by an author.

The research source registry contains 587 entries, 477 with a currently retained local source snapshot. It also contains primary evidence from negative checks; registry membership does not indicate a finding. The much larger coverage-census inventory is kept separately and does not increase the number screened. Its recoverable downloads were removed in the MVP cleanup described above. Mechanical quotation checks distinguish exact extracted matches, line-break normalisation, visually checked reading-order problems, and web/manual checks. Passing file validation does not establish substantive truth.

No author was contacted and no response is recorded. Empty `author_response` arrays mean only that no response is recorded. No intent is inferred. Research notes, negative screens, original PDFs and review history remain under `research/`.

To reproduce assembly and file validation, run `python3 research/build_deliverables.py` followed by `python3 research/validate_deliverables.py`. Original quotations are preserved; the assembly only normalises metadata structure and selected English narrative spacing.

The third-round independent pool and positive register-link audit is saved in [tax-final-merged-pool-register-links-audit.json](research/round3-reviews/tax-final-merged-pool-register-links-audit.json). Audits identify their exact snapshot hashes; later semantic corrections are recorded separately.

The third-round [final snapshot addendum](research/round3-reviews/tax-final-merged-pool-snapshot-addendum.json) authenticates the three subsequent committee-cover wording corrections and audit-reference addition, with unchanged counts, roles, depths and delivery-date qualifications.

The fourth-round [final snapshot audit](research/round4-reviews/energy-final-merged-pool-addendum.json) confirms the100issue/626reading-unit snapshot, including the late unresolved tobacco-tax lead. The [targeted outcomes](research/round4/targeted-outcomes.json) preserve major priority leads that did not become findings.
