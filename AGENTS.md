# Project guidance

This is an MVP. Keep the app, structured findings, source metadata, research decisions and review records small and usable. Do not turn the repository into a mirror of public document collections.

## Source storage

- Record the original URL, document identity/version, access date, page locators, check results and relevant limitations in structured research records. A URL alone is not evidence that a check was performed.
- Download sources to a system temporary directory for the current task. If a resumable working cache is needed, use `.cache/sources/`; it is disposable and ignored. Remove temporary downloads when the task is complete.
- Do not bulk-download census inventories, ministry websites or all linked PDFs simply to enumerate coverage. Save URLs and metadata; fetch only documents needed for actual checks.
- Do not routinely retain public PDFs, ZIPs, datasets, fetched HTML, extracted text, OCR output or page renders that can be downloaded or regenerated. Avoid duplicate copies across research rounds.
- Retain a local snapshot only when required by a current report/build/validation dependency, a review needs its exact historical version, or recovery would be unreliable (for example a disappearing source or hard-to-recreate evidence). Explain the exception in its source record and record a hash where exact identity matters. Prefer one shared copy.
- Never delete findings, unresolved/rejected decisions, human/AI review records, authored research notes, schemas, provenance metadata or unique evidence as cache cleanup. Check references and build/validation dependencies before deleting existing assets. Existing factual-batch builders and quotation validation still require some saved source files.
- Keep short source excerpts and locators where necessary; do not save whole extracted books or webpages as a substitute for a citation.

## Existing cleanup and recovery

`research/cache-manifest.json` records intentionally evicted downloads and their URLs, hashes and ZIP member names. Existing research inventories and audit reports describe historical snapshots; a recorded archive path does not guarantee that its file remains on disk. Consult the manifest before treating a missing historical download as corruption.

Use `python3 research/source_cache.py --list` to find evicted paths, then `python3 research/source_cache.py <project-relative-path>` to restore only what is needed. The restore tool refuses changed bytes. If the live source has changed or disappeared, disclose that limitation and reassess the source; do not silently replace an old snapshot or pretend its previous checks still apply. Restoration is not a new factual check.

After cleanup or changes to reporting, run the affected builders and `python3 research/validate_deliverables.py`. Preserve current report dependencies unless their callers are explicitly updated to support on-demand sources. Do not run full crawls or restore the entire collection just to validate a small change.
