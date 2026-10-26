"""Assemble the factual pilot without changing earlier issue or reading records."""

import copy
import hashlib
import html
import json
import os
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
RENDER_ONLY = "--render-only" in sys.argv


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
schema = Draft202012Validator(read(HERE / "claim.schema.json"))
adjudication = read(HERE / "adjudication.json")
documents = {d["id"]: d for d in protocol["documents"]}
sources = {s["id"]: s for s in read(HERE / "root-sources.json")}
claims, reviews, raw_files = [], [], []
errors, warnings = [], []

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


for letter in "abc":
    path = HERE / "agents" / f"claims-{letter}.json"
    raw = read(path)
    raw_files.append({"file": str(path.relative_to(ROOT)), "sha256": digest(path)})
    for source in raw.get("sources", []):
        add_source(source)
    for claim in raw["claims"]:
        claim = copy.deepcopy(claim)
        claim["researcher"] = letter
        claim["initial_result"] = claim["result"]
        claim["inventory_file"] = str(path.relative_to(ROOT))
        claims.append(claim)

for source in adjudication.get("additional_sources", []):
    sources[source["id"]] = source
for claim in adjudication.get("additional_claims", []):
    claims.append(copy.deepcopy(claim))
claim_index = {c["id"]: c for c in claims}
if len(claim_index) != len(claims):
    errors.append("Duplicate claim identities")
for decision in adjudication.get("decisions", []):
    cid = decision["claim_id"]
    if cid not in claim_index:
        errors.append(f"Unknown adjudicated claim: {cid}")
        continue
    claim_index[cid].update(decision.get("updates", {}))
    claim_index[cid]["adjudication"] = decision

for reviewer, target in protocol["peer_review_rotation"].items():
    path = HERE / "reviews" / f"{reviewer}-reviews-{target}.json"
    review = read(path)
    for source in review.get("sources", []):
        add_source(source)
    reviewed = ROOT / review["reviewed_file"]
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
        resolved = any(
            r["review_file"] == str(path.relative_to(ROOT)) and r["omission_index"] == number
            for r in adjudication.get("omission_resolutions", [])
        )
        if not resolved:
            errors.append(f"Omission lacks resolution: {path.name}:{number}")
    reviews.append({"file": str(path.relative_to(ROOT)), "sha256": digest(path),
                    "claims_reviewed": len(seen), "omissions": len(review.get("omissions", []))})

for claim in claims:
    cid = claim["id"]
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
            if not (ROOT / claim["visual_anchor_check"]["evidence_file"]).is_file():
                errors.append(f"Missing visual anchor evidence: {cid}")
        else:
            errors.append(f"Original anchor not found on cited pages: {cid}")
    for evidence in claim["evidence"]:
        source = sources.get(evidence["source_id"])
        if not source:
            errors.append(f"Unresolved evidence source: {cid}:{evidence['source_id']}")
        elif source.get("usable_as_evidence") is False:
            errors.append(f"Unusable evidence cited: {cid}:{source['id']}")
    if claim["result"] == "supported" and not claim["evidence"]:
        errors.append(f"Supported claim has no evidence: {cid}")
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
for doc in documents.values():
    if digest(ROOT / doc["local_file"]) != doc["sha256"]:
        errors.append(f"Original author snapshot changed: {doc['id']}")

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
    "claims": len(claims), "outcomes": dict(Counter(c["result"] for c in claims)),
    "materiality": dict(Counter(c["materiality"] for c in claims)),
    "independent_peer_claim_reviews": sum(r["claims_reviewed"] for r in reviews),
    "peer_omissions_independently_adjudicated_by_root": len(adjudication.get("additional_claims", [])),
    "completed_assessments": sum(c["check_completed"] for c in claims),
    "per_document": per_doc, "main_issue_admissions": adjudication.get("main_issue_admissions", []),
    "scope": protocol["population"], "limits": adjudication["limits"],
    "conclusions": adjudication["conclusions"], "sources": len(sources),
    "archived_source_files": len(archive_checks), "new_reading_units": 0,
    "source_access_attempts_unusable": sum(s.get("usable_as_evidence") is False or bool(s.get("error")) for s in sources.values()),
}
write(HERE / "validation-report.json", {"valid": not errors, "errors": errors,
      "warnings": warnings, "author_snapshot_hashes_checked": len(documents),
      "claims_checked": len(claims), "reviews": reviews, "archives": archive_checks})
if errors:
    print(json.dumps({"errors": errors, "warnings": warnings}, indent=2))
    raise SystemExit(1)

write(HERE / "claim-ledger.json", {"summary": summary, "protocol": "research/factual-pilot/protocol.json",
      "documents": list(documents.values()), "claims": claims, "sources": list(sources.values()),
      "inventory_snapshots": raw_files, "peer_reviews": reviews,
      "adjudication": "research/factual-pilot/adjudication.json"})
write(HERE / "summary.json", summary)
pilot_index_path = ROOT / "data" / "factual-check-pilots.json"
pilot_index = read(pilot_index_path) if pilot_index_path.is_file() else {"pilots": []}
entry = {k: summary[k] for k in ["id", "status", "documents", "author_pages", "claims", "outcomes", "new_reading_units"]}
entry.update({"summary": "research/factual-pilot/summary.json", "ledger": "research/factual-pilot/claim-ledger.json", "report": "research/factual-pilot/report.html"})
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
    text = re.sub(r"(?<=[A-Za-z])([,;:])(?=\d)", r"\1 ", text)
    text = re.sub(r"(CCS|CCU|DCMI|DVGW|CMA|VDMA|BDEW|ISO|DIN|HSE)(?=[a-z])", r"\1 ", text)
    text = text.replace("EUETS", "EU ETS")
    for token, original in protected.items():
        text = text.replace(token, original)
    return text

p = lambda value: e(prose(value))

SOURCE_TITLES = {
    "c-iso27913-gso": "GSO preview of ISO 27913:2024",
    "c-din27913": "DIN EN ISO 27913:2026-07 — publisher catalogue",
    "c-din18397-drafts": "DIN standards committee — draft standards",
    "c-dvgw-c463": "DVGW C463:2025 — publisher scope and contents",
    "c-dvgw-c260": "DVGW C260:2022 — publisher catalogue",
    "c-cen-workplan2026": "CEN-CENELEC 2026 work programme",
    "c-evaluation2022": "Federal evaluation of the CO₂ Storage Act (2022), BT 20/5145",
    "c-rohrfltgv8": "Pipeline Ordinance (RohrFLtgV), section 8",
    "c-rohrfltgv5": "Pipeline Ordinance (RohrFLtgV), section 5",
    "c-commission-initiative": "European Commission — CO₂ infrastructure and markets initiative",
    "c-porthos-schedule20260416": "Porthos project schedule, 16 April 2026",
    "c-dnv-rpf104": "DNV-RP-F104 — design and operation of CO₂ pipelines",
    "c-usgs-co2": "USGS — volcanic gas hazards",
    "c-evs-pren18397": "Estonian standards body — prEN 18397",
    "c-zenodo-depressurization": "CO₂ pipe depressurisation study — author research archive",
    "c-doe-cslf2015": "Carbon Sequestration Leadership Forum — 2015 technical report",
    "c-pren18397-din": "DIN standards committee — prEN 18397 draft",
    "c-depressurization-preprint": "Experimental CO₂ pipe depressurisation — author preprint",
    "c-eu-harmonised": "European Commission — harmonised standards",
    "root-enwg49": "Energy Industry Act (EnWG), section 49",
    "cr-c491-preview": "DVGW C491:2023 — public preview",
    "cr-c466-preview": "DVGW C466:2023 — public preview",
}

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
    for ev in c["evidence"]:
        source = sources[ev["source_id"]]
        archive = f" · <a href='{local_link(source['local_file'])}'>archive</a>" if source.get("local_file") else ""
        links.append(f"<li><a href='{e(source['url'], quote=True)}'>{p(SOURCE_TITLES.get(source['id'], source['title']))}</a>{archive}"
                     f"<p>{p(str(ev.get('locator', '')))} · {p(ev.get('summary', ''))}</p></li>")
    limits = c["limits"] if isinstance(c["limits"], str) else "; ".join(c["limits"])
    cards.append(f"""<article data-result='{e(c['result'])}' id='{e(c['id'])}'>
<p class='meta'>{e(doc['author'])} · PDF page {e(', '.join(map(str,c['pdf_pages'])))} · {e(c['materiality'])} materiality</p>
<h3>{p(c['claim_en'])}</h3><p><strong class='{e(c['result'])}'>{e(c['result'].replace('_',' ').capitalize())}</strong> — {p(c['explanation'])}</p>
<p class='limit'>{p(limits)}</p><details><summary>Evidence and review</summary>
<p><a href='{local_link(doc['local_file'])}#page={c['pdf_pages'][0]}'>Original submission</a> · {e(c['section'])}</p>
<p lang='de'>Anchor: “{e(c['original_excerpt'])}”</p><p>{p(c['policy_link'])}</p><ul>{''.join(links)}</ul>
<p>Claim {e(c['id'])} · <a href='{local_link(c['peer_review']['file'])}'>Independent peer review</a></p>
</details></article>""")
conclusions = "".join(f"<li>{p(x)}</li>" for x in summary["conclusions"])
limits = "".join(f"<li>{p(x)}</li>" for x in summary["limits"])
outcomes = " · ".join(f"{v} {k.replace('_',' ')}" for k,v in summary["outcomes"].items())
report = f"""<!doctype html><html lang='en'><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>Expanded factual checks · CO₂ pipeline consultation</title><style>
body{{font:17px/1.6 system-ui,sans-serif;max-width:1040px;margin:40px auto;padding:0 22px;color:#172d35;background:#f8faf9}}
h1{{font-size:36px;line-height:1.2}}h2{{margin-top:40px}}h3{{font-size:20px;line-height:1.4;margin:8px 0}}a{{color:#075e87}}
article{{background:white;border:1px solid #cbd8da;padding:22px;margin:18px 0;border-radius:9px}}p{{margin:10px 0}}
.meta,.limit{{font-size:14px;color:#50636b}}.supported{{color:#146845}}.unresolved{{color:#885711}}.overstated,.contradicted{{color:#9c3930}}
table{{width:100%;border-collapse:collapse;font-size:14px}}th,td{{padding:10px;text-align:left;border-bottom:1px solid #cbd8da}}
select,input{{font:inherit;padding:8px;border:1px solid #82999e;border-radius:4px;background:white;margin-right:8px}}details p,details li{{font-size:14px}}
[hidden]{{display:none!important}}summary{{cursor:pointer}}@media(max-width:600px){{body{{margin:22px auto}}h1{{font-size:28px}}table{{font-size:12px}}}}
</style><main><p class='meta'>Factual review pilot · 25 October 2026 · Independent AI checks</p>
<h1>Expanded factual checks of the CO₂ pipeline consultation</h1>
<p>Seven previously examined external responses, 35 author pages and {len(claims)} recorded claims. Every claim inventory was checked by another researcher, with final adjudication recorded separately.</p>
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
