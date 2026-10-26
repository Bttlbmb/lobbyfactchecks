"""Refresh current counts without implying that the timed research round is complete."""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def read(name):
    return json.loads((ROOT / name).read_text())


findings = read("data/findings.json")
leads = read("data/unresolved-leads.json")
rejected = read("data/rejected-candidates.json")
sources = read("data/source-registry.json")
major = [r for r in findings if r["severity"] == "major"]
minor = len(findings) - len(major)
counts = {
    "provisional_findings": len(findings),
    "major": len(major),
    "minor": minor,
    "unresolved_leads": len(leads),
    "rejected_candidates": len(rejected),
}
timing = read("data/investigation-round2.json")
timing["current_compiled_counts"] = counts
(ROOT / "data/investigation-round2.json").write_text(
    json.dumps(timing, ensure_ascii=False, indent=2) + "\n"
)

p = ROOT / "README.md"
text = p.read_text()
text = re.sub(
    r"The current saved set contains .*?\. Of the minor findings,",
    f"The current saved set contains **{len(findings)} provisional findings: "
    f"{len(major)} major and {minor} minor**, plus **{len(leads)} unresolved leads** "
    f"and **{len(rejected)} rejected candidate**. Of the minor findings,",
    text,
    count=1,
)
table = "| Issue ID | Narrow correction |\n| --- | --- |\n"
table += "\n".join(
    f"| `{r['id']}` | {r['card']['the_problem'].replace('|', '/')} |" for r in major
)
text = re.sub(
    r"(?<=## Major provisional findings\n\n).*?(?=\n\n## Method and limits)",
    lambda _: table,
    text,
    count=1,
    flags=re.S,
)
archives = sum(bool(s.get("local_file")) for s in sources)
text = re.sub(
    r"The source registry contains \d+ entries, \d+ with local archives\.",
    f"The source registry contains {len(sources)} entries, {archives} with local archives.",
    text,
    count=1,
)
ancillary = sum(str(r.get("reporting_tier", "")).startswith("ancillary") for r in findings)
text = re.sub(r"Of the minor findings, \d+ are ancillary .*?issues\.", f"Of the minor findings, {ancillary} are ancillary chronology, attribution or index-label issues.", text, count=1)
p.write_text(text)
print(json.dumps(counts))
