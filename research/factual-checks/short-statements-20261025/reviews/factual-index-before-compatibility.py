"""Build a compact entry point for completed systematic factual-check batches."""

import argparse
import html
import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BATCH_ROOT = ROOT / "research/factual-checks"
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--config", default="research/factual-checks/extension-protocol.json")
args = parser.parse_args()
config_path = (ROOT / args.config).resolve()
config = json.loads(config_path.read_text())
if config.get("status") != "complete":
    raise ValueError("Factual-check phase is not complete")
if not config.get("batches") or len(config["batches"]) != len(set(config["batches"])):
    raise ValueError("Configure a nonempty list of distinct batches")
batch_paths = [(BATCH_ROOT / name).resolve() for name in config["batches"]]
if (len(batch_paths) != len(set(batch_paths))
        or any(path.parent != BATCH_ROOT.resolve() for path in batch_paths)):
    raise ValueError("Batches must identify distinct direct child directories")
HERE = (ROOT / config.get("output_directory", "research/factual-checks")).resolve()
HERE.mkdir(parents=True, exist_ok=True)
rows, outcomes = [], Counter()
for name, path in zip(config["batches"], batch_paths):
    summary = json.loads((path / "summary.json").read_text())
    if summary["status"] != "complete":
        raise ValueError(f"Incomplete batch: {name}")
    protocol = json.loads((path / "protocol.json").read_text())
    outcomes.update(summary["outcomes"])
    rows.append({"batch": path.name, "title": protocol["title"],
                 "documents": summary["documents"], "pdf_pages": summary["pdf_pages"],
                 "claims": summary["claims"], "outcomes": summary["outcomes"],
                 "initial_peer_reviews": summary["independent_peer_claim_reviews"],
                 "main_issue_admissions": summary["main_issue_admissions"],
                 "report": str((path / "report.html").relative_to(ROOT)),
                 "ledger": str((path / "claim-ledger.json").relative_to(ROOT))})
summary = {"id": config.get("id", "factual-check-extension"), "status": "complete",
           "built_at_utc": datetime.now(timezone.utc).isoformat(),
           "started_at_utc": config["started_at_utc"], "batches": rows,
           "documents": sum(x["documents"] for x in rows),
           "pdf_pages": sum(x["pdf_pages"] for x in rows),
           "claims": sum(x["claims"] for x in rows), "outcomes": dict(outcomes),
           "initial_peer_reviews": sum(x["initial_peer_reviews"] for x in rows),
           "main_issue_admissions": [a for x in rows for a in x["main_issue_admissions"]],
           "new_reading_units": 0,
           "limits": ["Finite, previously examined response sets; not a representative sample or national denominator.",
                      "Physical PDF pages include committee covers where present.",
                      "Supported concerns the recorded proposition; unresolved is neither a finding nor confirmation.",
                      "Every initial assessment received an independent AI peer review. Root adjudicated challenges and omissions.",
                      "The inventories target material testable premises; they do not certify every factual assertion.",
                      "No author contact or human specialist confirmation."]}
if config.get("population_limit"):
    summary["limits"].insert(0, config["population_limit"])
if config.get("report_note"):
    summary["report_note"] = config["report_note"]
(HERE / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
e = html.escape
table = "".join(f"<tr><td><a href='{e(os.path.relpath(ROOT / x['report'], HERE))}'>{e(x['title'])}</a></td>"
                f"<td>{x['documents']}</td><td>{x['pdf_pages']}</td><td>{x['claims']}</td>"
                f"<td>{e(', '.join(f'{n} {k}' for k,n in x['outcomes'].items()))}</td></tr>" for x in rows)
limits = "".join(f"<li>{e(x)}</li>" for x in summary["limits"])
counts = " · ".join(f"{n} {k}" for k,n in outcomes.items())
phase_note = f"<p>{e(summary['report_note'])}</p>\n" if summary.get("report_note") else ""
report = f"""<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Expanded factual checks</title><style>
body{{font:17px/1.65 system-ui,sans-serif;max-width:1050px;margin:50px auto;padding:0 22px;color:#172d35;background:#f8faf9}}
h1{{font-size:38px;line-height:1.2}}a{{color:#075e87}}table{{width:100%;border-collapse:collapse;font-size:15px}}td,th{{padding:12px;text-align:left;border-bottom:1px solid #cbd8da}}.meta{{font-size:14px;color:#50636b}}.scroll{{overflow:auto}}
@media(max-width:600px){{body{{margin:25px auto}}h1{{font-size:30px}}}}
</style><main><p class="meta">Systematic factual checks · Independent AI research and cross-review</p>
<h1>Expanded factual checks</h1><p>{summary['documents']} previously examined response PDFs, {summary['pdf_pages']} physical PDF pages and {summary['claims']} claim assessments across {len(rows)} research batches.</p>
<p><strong>{e(counts)}</strong></p>
{phase_note}<p>The checks examine material factual premises using primary evidence beyond each author's own citations. The reports retain supported claims, unresolved questions, excluded policy judgements and negative checks. Potential errors receive separate contextual and temporal review before entering the main findings.</p>
<div class="scroll"><table><thead><tr><th>Response set</th><th>Documents</th><th>PDF pages</th><th>Assessments</th><th>Outcomes</th></tr></thead><tbody>{table}</tbody></table></div>
<p>{summary['initial_peer_reviews']} initial assessments received individual peer reviews. Repeat checking adds zero units to the existing reading ledger.</p>
<h2>Scope and limits</h2><ul>{limits}</ul>
<p><a href="summary.json">Summary data</a> · <a href="completion-audit.json">Completion audit</a> · <a href="{e(os.path.relpath(config_path, HERE))}">Extension protocol</a> · <a href="{e(os.path.relpath(ROOT / 'README.md', HERE))}">Project documentation</a></p></main></html>"""
(HERE / "report.html").write_text(report)
print(json.dumps({k: summary[k] for k in ["documents", "pdf_pages", "claims", "outcomes", "initial_peer_reviews"]}, indent=2))
