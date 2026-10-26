"""Validate and render a reviewed overlay without rewriting historical claim ledgers."""

import argparse
import hashlib
import html
import json
import os
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def read(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def build(directory):
    here = (ROOT / directory).resolve()
    here.relative_to(ROOT)
    protocol = read(here / "protocol.json")
    require(protocol["status"] == "complete", "Follow-up is not complete")
    baseline = read(here / "baseline-claims.json")
    originals = {x["claim"]["id"]: x for x in baseline["claims"]}
    require(len(originals) == len(baseline["claims"]) == protocol["baseline_claims"],
            "Baseline claim count/identity mismatch")
    require(baseline["baseline_ledgers"] == protocol["baseline_ledgers"],
            "Baseline ledger declarations differ")
    all_claims = {}
    for item in baseline["baseline_ledgers"]:
        path = ROOT / item["ledger"]
        require(digest(path) == item["sha256"], f"Historical ledger changed: {path}")
        ledger = read(path)
        claims = ledger["claims"] if isinstance(ledger, dict) else ledger
        all_claims.update({x["id"]: x for x in claims})
    require({k for k, v in all_claims.items() if v["result"] == "unresolved"} == set(originals),
            "Follow-up does not cover exactly the baseline unresolved claims")
    for key, item in originals.items():
        require(item["claim"] == all_claims[key], f"Baseline claim changed: {key}")
        document = item["document"]
        require(digest(ROOT / document["local_file"]) == document["sha256"],
                f"Original document changed: {document['id']}")
    preservation = read(here / "preservation-baseline.json")
    for item in preservation["files"]:
        require(digest(ROOT / item["file"]) == item["sha256"],
                f"Preserved historical file changed: {item['file']}")
    freeze = read(here / "review-freeze.json")
    require(freeze["builder_sha256"] == digest(Path(__file__)), "Follow-up builder changed")
    frozen = {x["file"]: x["sha256"] for x in freeze["files"]}
    require(len(frozen) == len(freeze["files"]), "Duplicate frozen file")
    for filename in ["baseline-claims.json", "protocol-initial.json", "preservation-baseline.json",
                     "initial-freezes.json", "protocol.json", "adjudication.json"]:
        require(str((here / filename).relative_to(ROOT)) in frozen, f"Unfrozen context: {filename}")
    for filename, sha in frozen.items():
        path = (ROOT / filename).resolve()
        path.relative_to(here)
        require(digest(path) == sha, f"Review input changed: {filename}")
    final = read(here / "adjudication.json")
    decisions = {x["claim_id"]: x for x in final["decisions"]}
    require(len(decisions) == len(final["decisions"]) and set(decisions) == set(originals),
            "Every baseline case needs exactly one decision")
    require(final["status"] == "complete", "Adjudication incomplete")
    require(final["new_main_findings"] == 0,
            "This overlay does not admit main findings; use the separate issue review workflow")
    reviewed = set()
    allocations = [key for ids in protocol["agent_allocations"].values() for key in ids]
    require(len(allocations) == len(set(allocations)) and set(allocations) == set(originals),
            "Agent allocations must partition the baseline")
    initial = read(here / "initial-freezes.json")
    require(len(initial["freezes"]) == len(protocol["agent_allocations"])
            and {x["agent"] for x in initial["freezes"]} == set(protocol["agent_allocations"]),
            "Missing initial freeze")
    for item in initial["freezes"]:
        expected = {str((here / "agents" / f"resolutions-{item['agent']}.json").relative_to(ROOT)),
                    str((here / "sources" / f"{item['agent']}-primary-checks.json").relative_to(ROOT))}
        require(len(item["files"]) == 2 and {x["file"] for x in item["files"]} == expected,
                f"Incomplete initial freeze: {item['agent']}")
        for source in item["files"]:
            require(frozen.get(source["file"]) == source["sha256"], "Initial freeze changed")
    for agent, ids in protocol["agent_allocations"].items():
        proposal_path = here / "agents" / f"resolutions-{agent}.json"
        require(str(proposal_path.relative_to(ROOT)) in frozen, "Unfrozen proposal")
        proposal = read(proposal_path)
        if proposal.get("baseline_claims_sha256"):
            require(proposal["baseline_claims_sha256"] == digest(here / "baseline-claims.json"),
                    "Proposal baseline changed")
        if proposal.get("protocol_sha256"):
            require(proposal["protocol_sha256"] == digest(here / "protocol-initial.json"),
                    "Initial protocol changed")
        proposed = {x["claim_id"]: x for x in proposal["resolutions"]}
        require(len(proposed) == len(proposal["resolutions"]) and set(proposed) == set(ids),
                f"Proposal coverage mismatch: {agent}")
        reviewer = next(a for a, target in protocol["peer_review_rotation"].items() if target == agent)
        peer_path = here / "reviews" / f"{reviewer}-reviews-{agent}.json"
        require(str(peer_path.relative_to(ROOT)) in frozen, "Unfrozen peer review")
        peer = read(peer_path)
        target_freeze = next(x for x in initial["freezes"] if x["agent"] == agent)
        own_freeze = next(x for x in initial["freezes"] if x["agent"] == reviewer)
        peer_time = peer.get("created_at_utc") or peer.get("reviewed_at_utc")
        require(peer_time, "Peer review has no recorded time")
        require(all(datetime.fromisoformat(x["recorded_at_utc"]) <=
                    datetime.fromisoformat(peer_time) for x in [target_freeze, own_freeze]),
                "Peer predates initial freeze")
        require(peer["reviewer"] == reviewer and peer["target_agent"] == agent,
                "Peer independence/identity mismatch")
        require(peer["proposal_sha256"] == digest(proposal_path), "Peer reviewed different proposal")
        reviews = {x["claim_id"]: x for x in peer["reviews"]}
        require(len(reviews) == len(peer["reviews"]) and set(reviews) == set(ids),
                f"Peer coverage mismatch: {reviewer}")
        reviewed.update(reviews)
        for claim_id in ids:
            decision = decisions[claim_id]
            require(decision["peer_review_file"] == str(peer_path.relative_to(ROOT)),
                    f"Wrong peer reference: {claim_id}")
            require(decision.get("root_review"), f"No root review: {claim_id}")
    require(reviewed == set(originals), "Incomplete peer coverage")
    rows = []
    for claim_id, item in originals.items():
        decision = decisions[claim_id]
        protected = {"document_id", "author", "process", "original_url", "pdf_pages",
                     "original_excerpt", "claim_en", "baseline_result"}
        require(not protected.intersection(decision), f"Baseline context override: {claim_id}")
        require(decision["result"] in {"supported", "unresolved", "contradicted"}, "Unknown result")
        for key in ["resolution_basis", "explanation", "limits", "next_step"]:
            require(decision.get(key), f"Missing {key}: {claim_id}")
        require(decision.get("evidence"), f"No evidence/check references: {claim_id}")
        for evidence in decision["evidence"]:
            filename = evidence["source_file"]
            require(filename in frozen, f"Unfrozen evidence: {filename}")
            source = read(ROOT / filename)
            records = source.get("sources", source.get("records", source.get("checks", [])))
            matched = [x for x in records if x.get("id", x.get("source_id")) == evidence["source_id"]]
            require(len(matched) == 1,
                    f"Unknown evidence ID: {claim_id}: {evidence['source_id']}")
            require(evidence.get("locator"), f"No evidence locator: {claim_id}")
            evidence["source_url"] = matched[0]["url"]
            evidence["source_title"] = matched[0].get("title") or matched[0].get("identity") or evidence["source_id"]
        rows.append({"claim_id": claim_id, "document_id": item["claim"]["document_id"],
                     "author": item["document"]["author"], "process": item["document"]["process"],
                     "original_url": item["document"]["url"], "pdf_pages": item["claim"]["pdf_pages"],
                     "original_excerpt": item["claim"]["original_excerpt"],
                     "claim_en": item["claim"]["claim_en"], "baseline_result": "unresolved", **decision})
    counts = Counter(x["result"] for x in rows)
    effective = Counter(x["result"] for x in all_claims.values())
    effective["unresolved"] -= len(rows)
    effective.update(counts)
    summary = {"id": protocol["id"], "status": "complete", "reviewed": len(rows),
               "resolved": len(rows) - counts["unresolved"], "outcomes": dict(counts),
               "baseline_assessments": len(all_claims), "effective_baseline_outcomes": dict(effective),
               "independent_peer_reviews": len(reviewed), "new_reading_units": 0,
               "new_main_findings": final["new_main_findings"],
               "historical_files_preserved": len(preservation["files"]), "limits": protocol["limits"]}
    (here / "resolution-ledger.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
    (here / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    e = html.escape
    def local_link(filename, label):
        return f'<a href="{e(os.path.relpath(ROOT / filename, here))}">{e(label)}</a>'
    cards = []
    for row in sorted(rows, key=lambda x: (x["result"] == "unresolved", x["process"], x["claim_id"])):
        evidence = "".join(f'<li><a href="{e(x["source_url"])}">{e(x["source_title"])}</a>: {e(x["locator"])} — {e(x.get("summary", ""))} ({local_link(x["source_file"], "saved check")})</li>' for x in row["evidence"])
        cards.append(f'''<article data-result="{e(row['result'])}" id="{e(row['claim_id'])}">
<p class="meta">{e(row['process'])} · {e(row['author'])} · {e(row['claim_id'])}</p>
<h2>{e(row['claim_en'])}</h2><p><strong>Unresolved → {e(row['result'])}</strong> · {e(row['resolution_basis'].replace('_', ' '))}</p>
<p>{e(row['explanation'])}</p><p><strong>Limits:</strong> {e(row['limits'])}</p>
<p><strong>Next step:</strong> {e(row['next_step'])}</p>
<details><summary>Original wording, evidence and review</summary><blockquote>{e(row['original_excerpt'])}</blockquote>
<p><a href="{e(row['original_url'])}">Original response</a>, physical PDF page(s) {e(', '.join(map(str,row['pdf_pages'])))}.</p>
<ul>{evidence}</ul><p>{local_link(row['peer_review_file'], 'Independent peer review')} · Root: {e(row['root_review'])}</p></details></article>''')
    limits = "".join(f"<li>{e(x)}</li>" for x in protocol["limits"])
    (here / "report.html").write_text(f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Unresolved assessments: follow-up</title><style>
body{{font:17px/1.65 system-ui,sans-serif;max-width:1000px;margin:44px auto;padding:0 22px;background:#f8faf9;color:#172d35}}h1{{font-size:38px;line-height:1.2}}h2{{font-size:21px;line-height:1.4}}a{{color:#075e87}}.meta{{font-size:14px;color:#50636b}}article{{border-top:1px solid #cbd8da;padding:20px 0}}blockquote{{border-left:3px solid #cbd8da;padding-left:14px;margin-left:0}}select{{font:inherit;padding:7px}}details{{font-size:15px}}[hidden]{{display:none}}@media(max-width:600px){{h1{{font-size:30px}}body{{margin:24px auto}}}}
</style><main><p class="meta">26 October 2026 · Independent AI research and cross-review</p><h1>Revisiting unresolved assessments</h1>
<p><strong>{summary['reviewed']} reviewed · {summary['resolved']} resolved · {counts['unresolved']} remain unresolved.</strong></p>
<p>Three researchers revisited the original statements and targeted primary evidence. Each reviewed another researcher's frozen proposals; root adjudicated every case. Resolutions distinguish new evidence from corrections to an overly strong earlier evidence demand.</p>
<p>The previous 201-assessment snapshot remains preserved. Applying this overlay gives {effective['supported']} supported, {effective['unresolved']} unresolved and {effective['contradicted']} contradicted assessments. No additional reading units or new main findings were added.</p>
<p><a href="summary.json">Summary</a> · <a href="resolution-ledger.json">Resolution ledger</a> · <a href="adjudication.json">Adjudication</a> · <a href="review-freeze.json">Frozen review inputs</a> · <a href="completion-audit.json">Completion audit</a> · <a href="../short-statements-20261025/overview/report.html">Previous snapshot</a></p>
<ul>{limits}</ul><label for="filter">Show </label><select id="filter"><option value="all">All assessments</option><option value="supported">Resolved as supported</option><option value="unresolved">Still unresolved</option><option value="contradicted">Contradicted</option></select>
{''.join(cards)}</main><script>document.getElementById('filter').addEventListener('change',function(){{document.querySelectorAll('article').forEach(x=>x.hidden=this.value!=='all'&&x.dataset.result!==this.value)}});</script></html>''')
    print(json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", nargs="?", default="research/factual-checks/unresolved-followup-20261026")
    build(parser.parse_args().directory)
