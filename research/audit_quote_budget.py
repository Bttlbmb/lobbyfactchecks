"""Count unique short original excerpts across compiled issues and shared requests.

This is a quotation-length aid, not factual or legal review. It excludes underlines
and translations, merges identical archived bytes, and avoids counting a fragment
twice when a longer included excerpt contains it.
"""
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def read(path):
    return json.loads((ROOT / path).read_text())


sources = {s["id"]: s for s in read("data/source-registry.json")}
records = sum((read("data/" + name) for name in (
    "findings.json", "unresolved-leads.json", "rejected-candidates.json"
)), [])
by_document = {r["document_id"]: r for r in records}
quotes = defaultdict(set)
locations = defaultdict(set)
unresolved_sources = []


def collect(value, fallback, owner, field=""):
    if isinstance(value, dict):
        if isinstance(value.get("original"), str):
            sid = value.get("source_id", fallback)
            if not sid or sid not in sources:
                unresolved_sources.append({"owner": owner, "field": field, "source_id": sid})
            else:
                source = sources[sid]
                key = source.get("sha256") or source.get("url") or sid
                quotes[key].add(re.sub(r"\s+", " ", value["original"]).strip())
                locations[key].add(sid)
        for k, v in value.items():
            if k not in {"original", "underline", "translation_en"}:
                collect(v, fallback, owner, field + "." + k)
    elif isinstance(value, list):
        for n, v in enumerate(value):
            collect(v, fallback, owner, field + f"[{n}]")


for record in records:
    collect(record, record.get("submission_source_id"), record["id"])
for document in read("data/documents.json"):
    if document.get("request_quote"):
        fallback = by_document.get(document["id"], {}).get("submission_source_id")
        collect(document["request_quote"], fallback, document["id"], "shared_request_quote")

results = []
for key, excerpts in quotes.items():
    longest = [q for q in excerpts if not any(q != other and q in other for other in excerpts)]
    count = sum(len(q.split()) for q in longest)
    results.append({"source_ids": sorted(locations[key]), "unique_excerpt_word_count": count})
results.sort(key=lambda r: (-r["unique_excerpt_word_count"], r["source_ids"]))
report = {
    "scope": "All compiled original fields plus shared request quotations; identical archive hashes merged. Whitespace tokens include numeric tokens. Not a factual review.",
    "sources_with_excerpts": len(results),
    "over_25_words": [r for r in results if r["unique_excerpt_word_count"] > 25],
    "unresolved_sources": unresolved_sources,
    "counts": results,
}
(ROOT / "data/quotation-audit.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({k: v for k, v in report.items() if k != "counts"}, ensure_ascii=False, indent=2))
