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

## First GitHub push

Create an empty public repository in GitHub, without adding a README or other initial files. Replace the example owner and repository below with its actual SSH URL:

```sh
git remote add origin git@github.com:OWNER/REPOSITORY.git
git push -u origin main
```

In the GitHub repository, open **Settings → Pages** and select **GitHub Actions** as the source. If necessary, open **Actions → Static site and GitHub Pages → Run workflow** on `main`. The successful deployment exposes its URL in the `github-pages` environment. No custom domain is assumed.

GitHub Actions builds and validates pull requests without deploying them. Pushes to `main` and manual runs on `main` build and deploy. Build jobs have read-only repository access; the deployment job alone receives Pages and identity-token permissions. Configure the `github-pages` environment to permit deployment from `main` as appropriate for the repository. See [GitHub's publishing-source instructions](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site).

## Updating findings

Research decisions must still follow [the contributor guidance](../AGENTS.md). Preserve rejected decisions, unresolved leads and review records. The site reads the current assembled `data/` files; it does not automatically promote candidate records from `research/`.

When changing research inputs, use the affected research builders and full original-source validation in the existing research workspace:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-research.txt
.venv/bin/python research/build_deliverables.py
.venv/bin/python research/validate_deliverables.py
python3 site/build_static.py
```

Full research validation also requires Poppler's `pdftotext` and the exact local source files referenced by the records. Read `data/validation-report.json`: the historical validator writes its result there and does not signal every failure through its process exit status. The static build's checks are narrower and do not authenticate quotations or recheck substantive truth.

Downloaded PDFs, fetched HTML, text extractions, datasets and page renders remain local and ignored. Do not use `git add -f` to publish entire source directories. Keep authored metadata and review records under version control. If a particular historical snapshot or unique piece of evidence must be committed, record its reason and identity in its source metadata and add a narrow exception to `.gitignore`.

Consult `research/cache-manifest.json` for intentionally evicted files. List them with `python3 research/source_cache.py --list` and restore only the exact paths needed for the current check. The tool covers that eviction manifest; it is not a general installer for every local asset omitted from Git. A changed or unavailable live source must be disclosed and reassessed. Restoration and a successful website build are not new factual checks.
