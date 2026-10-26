# Publishing and maintenance

The public website is built from the saved findings. Publishing does not repeat the research, resolve unresolved leads or establish human specialist confirmation.

## Local workflow

```sh
python3 site/build_static.py
python3 -m http.server 8000 --bind 127.0.0.1 --directory dist
```

Open [the local preview](http://127.0.0.1:8000). Stop the server with Ctrl+C. Rebuild after editing templates or data. The build replaces only the generated `dist/` directory after the new output passes validation. Removed findings therefore leave no stale evidence pages.

The public artifact contains the findings index, an About page, an evidence page per admitted finding, CSS, `.nojekyll`, and six JSON exports: findings, unresolved leads, rejected candidates, sources, documents and the issue schema. The explicit file list prevents templates, Python scripts, raw source downloads and other research files from being included in the website. The GitHub repository itself will expose every committed file when made public.

All site links are relative, so the same output works at a domain root and at `https://OWNER.github.io/REPOSITORY/`. External original-source links and the existing Google Fonts requests need internet access; the core content uses local HTML and system font fallbacks. No visitor authentication or backend is required.

## Branch publishing on GitHub Pages

The source repository is [Bttlbmb/lobbyfactchecks](https://github.com/Bttlbmb/lobbyfactchecks), with SSH remote `git@github.com:Bttlbmb/lobbyfactchecks.git`. The website is [Claim Monitor](https://bttlbmb.github.io/lobbyfactchecks/).

Commit source changes on `main`, then run:

```sh
git push origin main
python3 site/publish.py
```

The publishing script builds and validates `site/` and `data/` from the pushed commit. It uses a temporary directory, leaving the current checkout and unrelated research work in place. It then commits only the generated public files to `gh-pages` and pushes that branch without force. An unchanged build creates no new deployment commit. Removed findings leave no stale evidence pages.

In **Settings → Pages → Build and deployment**, use **Deploy from a branch**, branch **gh-pages**, folder **/(root)**. The branch must exist before it can be selected. `.nojekyll` keeps the generated HTML intact. No custom domain or custom GitHub Actions workflow is required. GitHub still uses its own internal Pages deployment machinery, which may appear in the Actions interface. See [GitHub's branch-publishing instructions](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site).

Pushing `main` saves the source changes; running the publishing script updates the live website. The script rejects uncommitted changes in `site/` or `data/`, and requires `main` to have been pushed first. The public artifact is the same explicit file set checked by the local build.

## Updating findings

Research decisions must still follow [the contributor guidance](../AGENTS.md). Preserve rejected decisions, unresolved leads and review records. The site reads the current assembled `data/` files; it does not automatically promote candidate records from `research/`.

When changing research inputs, use the affected builders and saved-record validation:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-research.txt
.venv/bin/python research/build_deliverables.py
.venv/bin/python research/validate_deliverables.py
python3 site/build_static.py
```

Routine research validation checks schemas, issue/review references and recorded metadata. `data/validation-report.json` explicitly labels its scope as `saved_records_only`; it does not authenticate quotations or recheck substantive truth. Validation failures also return a nonzero process status.

To repeat original-source checks, restore only the exact files needed for that task, then pass `--check-local-sources`. This mode also requires Poppler's `pdftotext` (and `pdfinfo` for factual batches). The factual pilot, batch and resolution builders default to validating authored records without rewriting historical ledgers or reports. Their explicit source-check mode retains the stricter checks used to assemble a new snapshot. Remove temporary originals and regenerated extractions/renders after the task.

Downloaded PDFs, fetched HTML, text extractions, datasets and page renders are temporary and ignored. The MVP keeps links, source identity/version, access dates, short quotations, locators and authored research/review records. Do not use `git add -f` to publish entire source directories or retain downloads to keep validators working offline. Retain a snapshot only when explicitly requested or when it is unique evidence that cannot be regenerated, with the exception recorded in its metadata.

Consult `research/cache-manifest.json` for intentionally evicted files. List them with `python3 research/source_cache.py --list` and restore only the exact paths needed for the current check. The tool covers that eviction manifest; it is not a general installer for every local asset omitted from Git. A changed or unavailable live source must be disclosed and reassessed. Restoration and a successful website build are not new factual checks.
