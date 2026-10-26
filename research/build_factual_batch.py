"""Validate and assemble one configured factual-check batch; preserve raw inventories."""

import argparse
import copy
import hashlib
import html
import json
import os
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("batch", help="Workspace-relative batch directory containing protocol.json")
parser.add_argument("--render-only", action="store_true", help="Validate and render HTML without changing saved JSON snapshots")
args = parser.parse_args()
HERE = (ROOT / args.batch).resolve()
BATCH = str(HERE.relative_to(ROOT))
RENDER_ONLY = args.render_only


def read(path):
    return json.loads(path.read_text())


def write(path, data):
    if not RENDER_ONLY:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normal(text):
    text = re.sub(r"-\s*\n\s*", "", text)
    return re.sub(r"\s+", " ", text).strip()


protocol = read(HERE / "protocol.json")
schema = Draft202012Validator(read(ROOT / protocol["schema_file"]))
adjudication = read(HERE / "adjudication.json")
documents = {d["id"]: d for d in protocol["documents"]}
sources = {s["id"]: s for s in read(HERE / "root-sources.json")}
claims, reviews, raw_files, inventory_audits = [], [], [], []
known_omissions = {}
errors, warnings = [], []
if adjudication.get("status") != "complete":
    errors.append("Adjudication is not complete")
if len(documents) != len(protocol["documents"]):
    errors.append("Duplicate protocol document identities")
allocated = [did for group in protocol["agent_outputs"].values() for did in group]
if Counter(allocated) != Counter({did: 1 for did in documents}):
    errors.append("Researcher allocations must cover every protocol document exactly once")
rotation = protocol["peer_review_rotation"]
if (set(rotation) != set(protocol["agent_outputs"])
        or Counter(rotation.values()) != Counter({letter: 1 for letter in protocol["agent_outputs"]})
        or any(reviewer == target for reviewer, target in rotation.items())):
    errors.append("Peer rotation must independently cover every researcher exactly once")

def add_source(source):
    previous = sources.get(source["id"])
    if previous:
        for key in ["url", "local_file", "sha256"]:
            if previous.get(key) != source.get(key):
                errors.append(f"Conflicting source identity: {source['id']}:{key}")
        if previous.get("temporal_limit") != source.get("temporal_limit"):
            previous.setdefault("independent_access_notes", []).append(source.get("temporal_limit"))
        for key, value in source.items():
            previous.setdefault(key, value)
    else:
        sources[source["id"]] = copy.deepcopy(source)


for letter in protocol["agent_outputs"]:
    path = HERE / "agents" / f"claims-{letter}.json"
    raw = read(path)
    raw_files.append({"file": str(path.relative_to(ROOT)), "sha256": digest(path)})
    inventory_audits.append({"researcher": letter, "file": str(path.relative_to(ROOT)),
                             "documents": raw.get("documents", []),
                             "exclusions": raw.get("exclusions", []),
                             "limits": raw.get("limits", raw.get("limitations", []))})
    read_documents = {d.get("id", d.get("document_id")): d for d in raw.get("documents", [])}
    if len(read_documents) != len(raw.get("documents", [])):
        errors.append(f"Duplicate initial reading records: {letter}")
    if set(read_documents) != set(protocol["agent_outputs"][letter]):
        errors.append(f"Initial document allocation mismatch: {letter}")
    for did, doc in read_documents.items():
        pages_read = doc.get("pages_read", [])
        complete_pages = did in documents and set(pages_read) == set(range(1, documents[did]["physical_pages"] + 1))
        if not complete_pages or len(pages_read) != len(set(pages_read)):
            errors.append(f"Initial full read not recorded: {letter}:{did}")
    for source in raw.get("sources", []):
        add_source(source)
    for claim in raw["claims"]:
        claim = copy.deepcopy(claim)
        if claim["document_id"] not in protocol["agent_outputs"][letter]:
            errors.append(f"Claim outside researcher allocation: {letter}:{claim['id']}")
        claim["researcher"] = letter
        claim["initial_result"] = claim["result"]
        claim["inventory_file"] = str(path.relative_to(ROOT))
        claims.append(claim)

for source in adjudication.get("additional_sources", []):
    add_source(source)
for claim in adjudication.get("additional_claims", []):
    claims.append(copy.deepcopy(claim))
claim_index = {c["id"]: c for c in claims}
if len(claim_index) != len(claims):
    errors.append("Duplicate claim identities")
decision_ids = [d["claim_id"] for d in adjudication.get("decisions", [])]
if len(decision_ids) != len(set(decision_ids)):
    errors.append("Duplicate root decisions for a claim")
for decision in adjudication.get("decisions", []):
    cid = decision["claim_id"]
    if cid not in claim_index:
        errors.append(f"Unknown adjudicated claim: {cid}")
        continue
    immutable = {"id", "document_id", "researcher", "inventory_file", "initial_result", "peer_review", "independent_review"}
    if immutable.intersection(decision.get("updates", {})):
        errors.append(f"Root decision attempts to change immutable identity/provenance: {cid}")
        continue
    claim_index[cid].update(decision.get("updates", {}))
    claim_index[cid]["adjudication"] = decision

for reviewer, target in protocol["peer_review_rotation"].items():
    path = HERE / "reviews" / f"{reviewer}-reviews-{target}.json"
    review = read(path)
    for source in review.get("sources", []):
        add_source(source)
    reviewed = ROOT / review["reviewed_file"]
    expected_inventory = HERE / "agents" / f"claims-{target}.json"
    if reviewed.resolve() != expected_inventory.resolve():
        errors.append(f"Peer review is not bound to expected target inventory: {path.name}")
    if digest(reviewed) != review["reviewed_sha256"]:
        errors.append(f"Review snapshot changed: {path.name}")
    expected = {c["id"] for c in claims if c.get("researcher") == target}
    seen = [c["claim_id"] for c in review["claim_reviews"]]
    if len(seen) != len(set(seen)) or set(seen) != expected:
        errors.append(f"Peer claim coverage mismatch: {path.name}")
    reread = {d["document_id"]: d["pages"] for d in review["documents_reread"]}
    for did in protocol["agent_outputs"][target]:
        pages = reread.get(did)
        if isinstance(pages, int):
            valid = pages == documents[did]["physical_pages"]
        else:
            valid = set(pages or []) == set(range(1, documents[did]["physical_pages"] + 1))
        if not valid:
            errors.append(f"Peer page coverage incomplete: {path.name}:{did}")
    for cr in review["claim_reviews"]:
        cid = cr["claim_id"]
        if cid in claim_index:
            claim_index[cid]["peer_review"] = {
                "reviewer": reviewer,
                "file": str(path.relative_to(ROOT)),
                **cr,
            }
        if cr["verdict"] != "accept" and not claim_index.get(cid, {}).get("adjudication"):
            errors.append(f"Peer challenge lacks root adjudication: {cid}")
    for number, omission in enumerate(review.get("omissions", [])):
        known_omissions[(str(path.relative_to(ROOT)), number)] = {"reviewer": reviewer, **omission}
        resolutions = [
            r for r in adjudication.get("omission_resolutions", []) if
            r["review_file"] == str(path.relative_to(ROOT)) and r["omission_index"] == number
        ]
        if len(resolutions) != 1:
            errors.append(f"Omission lacks resolution: {path.name}:{number}")
        else:
            resolution = resolutions[0]
            ids = resolution.get("claim_ids", [])
            if not resolution.get("resolution", "").strip():
                errors.append(f"Empty omission disposition: {path.name}:{number}")
            if ids:
                if any(cid not in claim_index for cid in ids):
                    errors.append(f"Omission references unknown claim: {path.name}:{number}")
            elif resolution.get("disposition") != "excluded":
                errors.append(f"Omission must reference claims or explicitly exclude: {path.name}:{number}")
    reviews.append({"file": str(path.relative_to(ROOT)), "sha256": digest(path),
                    "claims_reviewed": len(seen), "omissions": len(review.get("omissions", []))})

for resolution in adjudication.get("omission_resolutions", []):
    if (resolution.get("review_file"), resolution.get("omission_index")) not in known_omissions:
        errors.append(f"Resolution references nonexistent peer omission: {resolution}")

for claim in adjudication.get("additional_claims", []):
    independent = claim.get("independent_review", {})
    if (independent.get("reviewer") != "root"
            or independent.get("file") != f"{BATCH}/adjudication.json"
            or not independent.get("verdict")):
        errors.append(f"Additional claim lacks explicit root review: {claim['id']}")
    peer = claim.get("peer_review", {})
    omission = known_omissions.get((peer.get("file"), claim.get("omission_index")), {})
    if (peer.get("reviewer") != omission.get("reviewer")
            or claim["document_id"] != omission.get("document_id")
            or set(claim["pdf_pages"]) != set(omission.get("pdf_pages", []))):
        errors.append(f"Additional claim does not match actual peer omission: {claim['id']}")
    if not any(claim["id"] in r.get("claim_ids", []) and r["review_file"] == peer.get("file")
               and r["omission_index"] == claim.get("omission_index")
               for r in adjudication.get("omission_resolutions", [])):
        errors.append(f"Additional claim is not bound to a resolved peer omission: {claim['id']}")

for reference in adjudication.get("candidate_record_reviews", []):
    path = ROOT / reference["file"]
    if not path.is_file() or digest(path) != reference.get("sha256"):
        errors.append(f"Final candidate review snapshot changed or missing: {reference['file']}")
        continue
    for candidate in read(path).get("candidate_reviews", []):
        staged = ROOT / candidate["reviewed_file"]
        if not staged.is_file() or digest(staged) != candidate.get("reviewed_sha256"):
            errors.append(f"Staged candidate snapshot changed or missing: {candidate['reviewed_file']}")

manifest_path = HERE / "assembly-manifest.json"
admitted = []
if manifest_path.is_file():
    for filename in read(manifest_path).get("inputs", []):
        path = ROOT / filename
        if not path.is_file():
            errors.append(f"Manifested admission missing: {filename}")
            continue
        issue = read(path)
        admitted.append(issue["id"])
        claim = claim_index.get(issue.get("factual_check_claim_id"))
        if issue.get("finding_state") != "provisional_finding" or not claim or claim["result"] not in {"overstated", "contradicted"}:
            errors.append(f"Admission is not backed by a final error assessment: {filename}")
if Counter(admitted) != Counter(adjudication.get("main_issue_admissions", [])):
    errors.append("Explicit admission manifest and adjudication IDs differ")

for claim in claims:
    cid = claim["id"]
    if claim.get("result") == "not_checked" or not claim.get("check_completed"):
        errors.append(f"Incomplete material claim assessment: {cid}")
    for error in schema.iter_errors(claim):
        errors.append(f"{cid}:{'/'.join(map(str, error.path))}: {error.message}")
    doc = documents.get(claim["document_id"])
    if not doc:
        errors.append(f"Unknown author document: {cid}")
        continue
    pages = claim["pdf_pages"]
    if any(p > doc["physical_pages"] for p in pages):
        errors.append(f"Out-of-range author page: {cid}")
    extracted = (ROOT / doc["pilot_text"]).read_text().split("\f")
    text = " ".join(extracted[p - 1] for p in pages if p <= len(extracted))
    if normal(claim["original_excerpt"]) not in normal(text):
        if claim.get("visual_anchor_check", {}).get("evidence_file"):
            check = claim["visual_anchor_check"]
            visual = ROOT / check["evidence_file"]
            if (not visual.is_file() or digest(visual) != check.get("evidence_sha256")
                    or check.get("source_sha256") != doc["sha256"]
                    or check.get("excerpt") != claim["original_excerpt"]
                    or set(check.get("pdf_pages", [])) != set(pages)
                    or check.get("reviewer") not in {"root", claim.get("peer_review", {}).get("reviewer")}
                    or not check.get("reviewer")):
                errors.append(f"Visual anchor review lacks hash/page/excerpt/reviewer binding: {cid}")
        else:
            errors.append(f"Original anchor not found on cited pages: {cid}")
    for evidence in claim["evidence"]:
        source = sources.get(evidence["source_id"])
        if not source:
            errors.append(f"Unresolved evidence source: {cid}:{evidence['source_id']}")
        elif source.get("usable_as_evidence") is False:
            errors.append(f"Unusable evidence cited: {cid}:{source['id']}")
    if claim["result"] in {"supported", "contradicted", "overstated"} and not claim["evidence"]:
        errors.append(f"Resolved claim has no evidence: {cid}")
    if not claim.get("peer_review") and not claim.get("independent_review"):
        errors.append(f"Claim has no independent review: {cid}")

archive_checks = []
for source in sources.values():
    local = source.get("local_file")
    if not local:
        if not source.get("error") and source.get("usable_as_evidence") is not False:
            warnings.append(f"No local source archive: {source['id']}")
        continue
    path = ROOT / local
    if not path.is_file():
        errors.append(f"Missing archive: {source['id']}:{local}")
        continue
    actual = digest(path)
    if source.get("sha256") != actual:
        errors.append(f"Source hash mismatch or absent: {source['id']}")
    if path.suffix.lower() == ".pdf" and not path.read_bytes().startswith(b"%PDF-"):
        errors.append(f"Not a PDF: {source['id']}")
    archive_checks.append({"source_id": source["id"], "file": local, "sha256": actual})
author_text_checks = []
for doc in documents.values():
    if digest(ROOT / doc["local_file"]) != doc["sha256"]:
        errors.append(f"Original author snapshot changed: {doc['id']}")
    info = subprocess.run(["pdfinfo", str(ROOT / doc["local_file"])], capture_output=True, text=True)
    page_match = re.search(r"^Pages:\s+(\d+)", info.stdout, re.M)
    if not page_match or int(page_match.group(1)) != doc["physical_pages"]:
        errors.append(f"Original physical page count mismatch: {doc['id']}")
    extracted = subprocess.run(["pdftotext", "-layout", str(ROOT / doc["local_file"]), "-"], capture_output=True, text=True)
    text_path = ROOT / doc["pilot_text"]
    if extracted.returncode or extracted.stdout != text_path.read_text():
        errors.append(f"Saved author text differs from fresh original PDF extraction: {doc['id']}")
    author_text_checks.append({"document_id": doc["id"], "pdf_sha256": doc["sha256"],
                               "text_file": doc["pilot_text"], "text_sha256": digest(text_path),
                               "method": "Exact comparison with fresh pdftotext -layout extraction"})

per_doc = []
for doc in documents.values():
    subset = [c for c in claims if c["document_id"] == doc["id"]]
    per_doc.append({"document_id": doc["id"], "author": doc["author"],
                    "pages": doc["physical_pages"], "claims": len(subset),
                    "outcomes": dict(Counter(c["result"] for c in subset))})
summary = {
    "id": protocol["id"], "status": "complete" if not errors else "validation_failed",
    "completed_at_utc": datetime.now(timezone.utc).isoformat(),
    "started_at_utc": protocol["started_at_utc"],
    "documents": len(documents), "author_pages": sum(d["physical_pages"] for d in documents.values()),
    "pdf_pages": sum(d["physical_pages"] for d in documents.values()),
    "page_scope": "Physical PDF pages, including committee covers and appendices where present.",
    "claims": len(claims), "outcomes": dict(Counter(c["result"] for c in claims)),
    "materiality": dict(Counter(c["materiality"] for c in claims)),
    "independent_peer_claim_reviews": sum(r["claims_reviewed"] for r in reviews),
    "peer_omissions_independently_adjudicated_by_root": len(adjudication.get("omission_resolutions", [])),
    "additional_claims_independently_adjudicated_by_root": len(adjudication.get("additional_claims", [])),
    "completed_assessments": sum(c["check_completed"] for c in claims),
    "per_document": per_doc, "main_issue_admissions": adjudication.get("main_issue_admissions", []),
    "scope": protocol["population"], "limits": adjudication["limits"],
    "conclusions": adjudication["conclusions"], "sources": len(sources),
    "archived_source_files": len(archive_checks),  # Legacy per-source-record count.
    "archived_source_records": len(archive_checks),
    "unique_local_source_files": len({x["file"] for x in archive_checks}),
    "source_count_note": "Local source records can share a file; authored check-note containers are not original-source archives. Unusable-access count concerns registry records, not all nested attempts.",
    "new_reading_units": 0,
    "source_access_attempts_unusable": sum(s.get("usable_as_evidence") is False or bool(s.get("error")) for s in sources.values()),
}
write(HERE / "validation-report.json", {"valid": not errors, "errors": errors,
      "warnings": warnings, "author_snapshot_hashes_checked": len(documents),
      "author_text_extractions": author_text_checks,
      "claims_checked": len(claims), "reviews": reviews, "archives": archive_checks})
if errors:
    print(json.dumps({"errors": errors, "warnings": warnings}, indent=2))
    raise SystemExit(1)

write(HERE / "claim-ledger.json", {"summary": summary, "protocol": f"{BATCH}/protocol.json",
      "documents": list(documents.values()), "claims": claims, "sources": list(sources.values()),
      "inventory_snapshots": raw_files, "inventory_reading_and_exclusion_audits": inventory_audits,
      "peer_reviews": reviews,
      "adjudication": f"{BATCH}/adjudication.json"})
write(HERE / "summary.json", summary)
pilot_index_path = ROOT / "data" / "factual-check-pilots.json"
pilot_index = read(pilot_index_path) if pilot_index_path.is_file() else {"pilots": []}
entry = {k: summary[k] for k in ["id", "status", "documents", "author_pages", "pdf_pages", "page_scope", "claims", "outcomes", "new_reading_units"]}
entry.update({"summary": f"{BATCH}/summary.json", "ledger": f"{BATCH}/claim-ledger.json", "report": f"{BATCH}/report.html"})
pilot_index["pilots"] = [x for x in pilot_index["pilots"] if x["id"] != summary["id"]] + [entry]
write(pilot_index_path, pilot_index)

e = html.escape

def prose(value):
    """Repair display spacing in English prose, never in quotes, IDs or URLs."""
    text = str(value)
    protected = {}
    def protect(match):
        token = "PROTECTED" + chr(65 + len(protected)) + "END"
        protected[token] = match.group(0)
        return token
    text = re.sub(r"(?<=\w)(?=§)", " ", text)
    text = re.sub(r"CO2|(?<![A-Za-z])O2|§\s*\d+[a-z]?|\b[CG]\d{3}(?:-\d)?\b|\d+[a-z](?![A-Za-z])", protect, text)
    text = re.sub(r"(?<=[A-Za-z])(?=\d)|(?<=\d)(?=[A-Za-z])", " ", text)
    text = re.sub(r"(?<=\w)(?=§)", " ", text)
    text = re.sub(r"([,;:])(?=[A-Za-z§])", r"\1 ", text)
    text = re.sub(r"%(?=[A-Za-z])", "% ", text)
    text = re.sub(r"(?<=\S)(?=[€£])", " ", text)
    text = re.sub(r"\b(in|from|until)(January|February|March|April|May|June|July|August|September|October|November|December)\b", r"\1 \2", text)
    text = text.replace("fivecents", "five cents").replace("excludesVAT", "excludes VAT")
    text = re.sub(r"(?<=[A-Za-z])([,;:])(?=\d)", r"\1 ", text)
    text = re.sub(r"(CCS|CCU|DCMI|DVGW|CMA|VDMA|BDEW|ISO|DIN|HSE)(?=[a-z])", r"\1 ", text)
    text = text.replace("EUETS", "EU ETS")
    for token, original in protected.items():
        text = text.replace(token, original)
    return text

p = lambda value: e(prose(value))

SOURCE_TITLES = protocol.get("source_titles", {})

def local_link(path):
    return e(os.path.relpath(ROOT / path, HERE), quote=True)

rows = "".join(
    f"<tr><td>{e(d['author'])}</td><td>{d['pages']}</td><td>{d['claims']}</td><td>"
    + e(", ".join(f"{v} {k.replace('_', ' ')}" for k, v in d["outcomes"].items())) + "</td></tr>"
    for d in per_doc
)
cards = []
for c in claims:
    doc = documents[c["document_id"]]
    links = []
    adjudication_url = local_link(f"{BATCH}/adjudication.json")
    adjudication_link = f" · <a href='{adjudication_url}'>Root adjudication</a>" if c.get("adjudication") else ""
    for ev in c["evidence"]:
        source = sources[ev["source_id"]]
        saved_label = "saved check record" if str(source.get("local_file", "")).endswith(".json") else "archive"
        archive = f" · <a href='{local_link(source['local_file'])}'>{saved_label}</a>" if source.get("local_file") else ""
        links.append(f"<li><a href='{e(source['url'], quote=True)}'>{p(SOURCE_TITLES.get(source['id'], source['title']))}</a>{archive}"
                     f"<p>{p(str(ev.get('locator', '')))} · {p(ev.get('summary', ''))}</p></li>")
    limits = c["limits"] if isinstance(c["limits"], str) else "; ".join(c["limits"])
    cards.append(f"""<article data-result='{e(c['result'])}' id='{e(c['id'])}'>
<p class='meta'>{e(doc['author'])} · PDF page {e(', '.join(map(str,c['pdf_pages'])))} · {e(c['materiality'])} materiality</p>
<h3>{p(c['claim_en'])}</h3><p><strong class='{e(c['result'])}'>{e(c['result'].replace('_',' ').capitalize())}</strong> — {p(c['explanation'])}</p>
<p class='limit'>{p(limits)}</p><details><summary>Evidence and review</summary>
<p><a href='{local_link(doc['local_file'])}#page={c['pdf_pages'][0]}'>Original submission</a> · {e(c['section'])}</p>
<p lang='de'>Anchor: “{e(c['original_excerpt'])}”</p><p>{p(c['policy_link'])}</p><ul>{''.join(links)}</ul>
<p>Claim {e(c['id'])} · <a href='{local_link(c.get('peer_review', c.get('independent_review'))['file'])}'>Independent peer review</a>{adjudication_link}</p>
</details></article>""")
conclusions = "".join(f"<li>{p(x)}</li>" for x in summary["conclusions"])
limits = "".join(f"<li>{p(x)}</li>" for x in summary["limits"])
outcomes = " · ".join(f"{v} {k.replace('_',' ')}" for k,v in summary["outcomes"].items())
report = f"""<!doctype html><html lang='en'><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>{e(protocol["report_title"])}</title><style>
body{{font:17px/1.6 system-ui,sans-serif;max-width:1040px;margin:40px auto;padding:0 22px;color:#172d35;background:#f8faf9}}
h1{{font-size:36px;line-height:1.2}}h2{{margin-top:40px}}h3{{font-size:20px;line-height:1.4;margin:8px 0}}a{{color:#075e87}}
article{{background:white;border:1px solid #cbd8da;padding:22px;margin:18px 0;border-radius:9px}}p{{margin:10px 0}}
.meta,.limit{{font-size:14px;color:#50636b}}.supported{{color:#146845}}.unresolved{{color:#885711}}.overstated,.contradicted{{color:#9c3930}}
table{{width:100%;border-collapse:collapse;font-size:14px}}th,td{{padding:10px;text-align:left;border-bottom:1px solid #cbd8da}}
select,input{{font:inherit;padding:8px;border:1px solid #82999e;border-radius:4px;background:white;margin-right:8px}}details p,details li{{font-size:14px}}
[hidden]{{display:none!important}}summary{{cursor:pointer}}@media(max-width:600px){{body{{margin:22px auto}}h1{{font-size:28px}}table{{font-size:12px}}}}
</style><main><p class='meta'>Expanded factual checks · {datetime.now(timezone.utc).strftime('%d %B %Y')} · Independent AI checks</p>
<h1>{e(protocol["report_title"])}</h1>
<p>{e(protocol["report_intro"])} The ledger records {len(claims)} claim assessments. Every initial inventory received independent peer review, followed by final adjudication.</p>
<p><strong>{e(outcomes)}</strong></p><p>“Supported” concerns the specific bounded proposition. “Unresolved” is an assessed uncertainty, not an error or confirmation.</p>
<h2>Results</h2><ul>{conclusions}</ul><h2>Documents</h2><table><thead><tr><th>Author</th><th>Pages</th><th>Claims</th><th>Outcomes</th></tr></thead><tbody>{rows}</tbody></table>
<h2>Claim ledger</h2><p><label for='status'>Outcome</label> <select id='status'><option value='all'>All outcomes</option>""" + "".join(
    f"<option value='{e(x)}'>{e(x.replace('_',' ').capitalize())}</option>" for x in summary["outcomes"]
) + f"""</select> <label for='query'>Search</label> <input id='query' type='search' placeholder='Author, claim or evidence'></p>
<p class='meta' id='visible'>{len(claims)} claims shown</p>{''.join(cards)}<h2>Scope and limits</h2><ul>{limits}</ul>
<p><a href='claim-ledger.json'>Machine-readable ledger</a> · <a href='protocol.json'>Protocol</a> · <a href='adjudication.json'>Final adjudication</a> · <a href='validation-report.json'>Validation</a></p></main>
<script>const cards=[...document.querySelectorAll('article')],status=document.querySelector('#status'),query=document.querySelector('#query');
function filter(){{let n=0;for(const c of cards){{c.hidden=(status.value!=='all'&&c.dataset.result!==status.value)||!c.textContent.toLowerCase().includes(query.value.toLowerCase());if(!c.hidden)n++;}}document.querySelector('#visible').textContent=n+(n===1?' claim shown':' claims shown');}}status.addEventListener('change',filter);query.addEventListener('input',filter);</script></html>"""
(HERE / "report.html").write_text(report)
print(json.dumps({k:summary[k] for k in ["status","documents","author_pages","claims","outcomes","independent_peer_claim_reviews"]}, indent=2))
