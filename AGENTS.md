# Project guidance

This is an MVP. Keep the app, structured findings, source metadata, research decisions and review records small and usable. Do not turn the repository into a mirror of public document collections.

## Source storage

- Record the original URL, document identity/version, access date, page locators, check results and relevant limitations in structured research records. A URL alone is not evidence that a check was performed.
- Download sources to a system temporary directory for the current task. If a resumable working cache is needed, use `.cache/sources/`; it is disposable and ignored. Remove temporary downloads when the task is complete.
- Do not bulk-download census inventories, ministry websites or all linked PDFs simply to enumerate coverage. Save URLs and metadata; fetch only documents needed for actual checks.
- Do not routinely retain public PDFs, ZIPs, datasets, fetched HTML, extracted text, OCR output or page renders that can be downloaded or regenerated. Avoid duplicate copies across research rounds.
- This MVP uses links and source metadata rather than a persistent source archive. Do not retain downloads just to support offline quotation checks, report rebuilding or hypothetical future production needs. Routine validation must work from saved records without fetching sources.
- Download an original only for a current substantive check. Remove it and its full-text extractions/renders afterward. Retain a snapshot only when the user explicitly requests that particular artifact or it is unique evidence that cannot be regenerated; record that exception.
- Never delete findings, unresolved/rejected decisions, human/AI review records, authored research notes, schemas, provenance metadata or unique evidence as cache cleanup. Preserve short quotations and page locators. Update callers that assume a permanent archive rather than keeping downloads to satisfy them.
- Keep short source excerpts and locators where necessary; do not save whole extracted books or webpages as a substitute for a citation.

## Existing cleanup and recovery

`research/cache-manifest.json` records intentionally evicted downloads and their URLs, hashes and ZIP member names. Existing research inventories and audit reports describe historical snapshots; a recorded archive path does not guarantee that its file remains on disk. Consult the manifest before treating a missing historical download as corruption.

Use `python3 research/source_cache.py --list` to find evicted paths, then `python3 research/source_cache.py <project-relative-path>` to restore only what is needed. The restore tool refuses changed bytes. If the live source has changed or disappeared, disclose that limitation and reassess the source; do not silently replace an old snapshot or pretend its previous checks still apply. Restoration is not a new factual check.

After cleanup or changes to reporting, run the affected builders and `python3 research/validate_deliverables.py`. These commands validate saved records by default and explicitly disclose that original source bytes were not rechecked. `--check-local-sources` opts into original-source checks after restoring only the needed files for that task. Historical reports, retention notes and source paths describe their original research snapshots, not files that must remain on disk. Do not run full crawls or restore the entire collection just to validate a small change.
