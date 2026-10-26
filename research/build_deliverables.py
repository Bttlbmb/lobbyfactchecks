"""Assemble the screened records without changing original-language quotations."""

import copy
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data"


def read(path):
    return json.loads((ROOT / path).read_text())


def write(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


registries = [
    ("research/energy/sources.json", "research/energy"),
    ("research/root/sources.json", "research/root"),
    ("research/social-digital/source-registry.json", "research/social-digital"),
]
round2_manifest_path = ROOT / "research/round2/assembly-manifest.json"
round2_manifest = read("research/round2/assembly-manifest.json") if round2_manifest_path.is_file() else {}
# Keep each round's explicit admission manifest separate on disk. Collection
# ledgers never promote records into the finding set.
replacement_inputs = {}
later_manifests = ["research/round3/assembly-manifest.json", "research/round4/assembly-manifest.json", "research/round5/assembly-manifest.json", "research/round6/assembly-manifest.json", "research/factual-pilot/assembly-manifest.json"]
later_manifests.extend(str(p.relative_to(ROOT)) for p in sorted((ROOT / "research/factual-checks").glob("*/assembly-manifest.json")))
for later_path in later_manifests:
    if not (ROOT / later_path).is_file():
        continue
    later = read(later_path)
    for key in ["inputs", "source_registries", "document_registries", "review_directories"]:
        round2_manifest.setdefault(key, []).extend(later.get(key, []))
    round2_manifest.setdefault("submission_sources", {}).update(later.get("submission_sources", {}))
    replacement_inputs.update(later.get("replacement_inputs", {}))
registries.extend(tuple(item) for item in round2_manifest.get("source_registries", []))
source_index = {}


def add_source(source, base):
    source = copy.deepcopy(source)
    source.setdefault("retrieved_at", "2026-10-24")
    if "local_path" in source:
        source["local_file"] = source.pop("local_path")
    if source.get("local_file"):
        p = Path(source["local_file"])
        if not p.parts[0] == "research":
            p = Path(base) / p
        source["local_file"] = str(p)
        if (ROOT / p).is_file():
            source["sha256"] = hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
    existing = source_index.get(source["id"])
    if existing:
        # Keep the earliest metadata and add independently recorded details.
        for key, value in source.items():
            if key not in existing:
                existing[key] = value
            elif key in {"url", "local_file", "sha256"} and existing[key] != value:
                variants = existing.setdefault("recorded_variants", [])
                item = {key: value}
                if item not in variants:
                    variants.append(item)
    else:
        source_index[source["id"]] = source


for path, base in registries:
    registry = read(path)
    for source in registry if isinstance(registry, list) else registry["sources"]:
        add_source(source, base)

inputs = [
    "research/energy/candidates.json",
    "research/energy/enefg2026-uim-l01.json",
    "research/energy/enefg2026-bund-a01.json",
    "research/energy/enefg2026-vik-a01.json",
    "research/energy/enefg2026-hansgrohe-a01.json",
    "research/energy/enefg2026-algorithmwatch-l01.json",
    "research/energy/enefg2026-dce-a01.json",
    "research/tax/jstg2026-dstg-tax01.json",
    "research/tax/jstg2026-dstg-tax02.json",
    "research/tax/jstg2026-dstg-tax03-unresolved.json",
    "research/tax/jstg2026-bdst-tax01.json",
    "research/tax/staendg2025-dehoga-tax01.json",
    "research/tax-round2/luftvst2026-bdi-tax04.json",
    "research/tax-round2/stefeg2024-dgb-tax05.json",
    "research/tax-round2/jstgII2024-dgb-tax06.json",
    "research/tax-round2/forg2026-financewatch-tax07.json",
    "research/tax-round2/begiv2024-bitkom-tax08.json",
    "research/root/candidates.json",
    "research/root/ggdg2026-sdc-root01.json",
    "research/root/ipspeicherung2026-brak-root01.json",
    "research/social-digital/candidates.json",
    "research/social-digital/ggdg2026-hateaid-a01.json",
    "research/social-digital/ggdg2026-hateaid-a02.json",
    "research/social-digital/sbgg2023-eggd-a01.json",
    "research/social-digital/bstabg2026-pharmadeutschland-a01.json",
    "research/social-digital/bstabg2026-dzvhae-candidates.json",
    "research/social-digital/mindestlohn2026-bda-a01.json",
]
inputs.extend(round2_manifest.get("inputs", []))
# Reassessments replace an explicitly named earlier input; they do not create
# another issue or alter the preserved earlier research record.
for previous, replacement in replacement_inputs.items():
    if inputs.count(previous) != 1:
        raise ValueError(f"Replacement must name exactly one existing input: {previous}")
    if not (ROOT / replacement).is_file():
        raise FileNotFoundError(replacement)
    previous_ids = read(previous)
    replacement_ids = read(replacement)
    previous_ids = {r["id"] for r in previous_ids} if isinstance(previous_ids, list) else {previous_ids["id"]}
    replacement_ids = {r["id"] for r in replacement_ids} if isinstance(replacement_ids, list) else {replacement_ids["id"]}
    if previous_ids != replacement_ids:
        raise ValueError(f"Reassessment must preserve issue identity: {previous}")
    inputs[inputs.index(previous)] = replacement

review_links = {
    "geg2023-hausgrund-a01": [("tax_consultations_ai", "research/reviews/tax-reviews-energy.json")],
    "wassbg2024-waniczek-a01": [("tax_consultations_ai", "research/reviews/tax-reviews-energy.json")],
    "enefg2026-uim-l01": [("tax_consultations_ai", "research/reviews/tax-reviews-energy.json")],
    "enefg2026-bund-a01": [("tax_consultations_ai", "research/reviews/tax-reviews-energy.json")],
    "enefg2026-vik-a01": [("tax_consultations_ai", "research/reviews/tax-reviews-energy.json"), ("root_independent_ai", "research/reviews/root-reviews-vik.json")],
    "enefg2026-hansgrohe-a01": [("tax_consultations_ai", "research/reviews/tax-reviews-energy.json")],
    "enefg2026-algorithmwatch-l01": [("tax_consultations_ai", "research/reviews/tax-reviews-energy.json")],
    "enefg2026-dce-a01": [("tax_consultations_ai", "research/reviews/tax-reviews-dce-enefg.json"), ("root_independent_ai", "research/reviews/root-reviews-dce-enefg.json")],
    "jstgII2024-dgb-tax06": [("energy_hearings_ai", "research/reviews/energy-reviews-dgb-attac.json")],
    "forg2026-financewatch-tax07": [("social_digital_independent_ai", "research/reviews/social-reviews-financewatch-forg.json")],
    "begiv2024-bitkom-tax08": [("energy_hearings_ai", "research/reviews/energy-reviews-bitkom-begiv.json")],
    "jstg2026-dstg-tax01": [("social_digital_independent_ai", "research/reviews/social-reviews-tax.json")],
    "jstg2026-dstg-tax02": [("social_digital_independent_ai", "research/reviews/social-reviews-tax.json")],
    "tabstaendg2026-vdr-root01": [("tax_consultations_ai", "research/reviews/tax-reviews-root.json")],
    "tabstaendg2026-bvte-root01": [("tax_consultations_ai", "research/reviews/tax-reviews-root.json")],
    "cannkg2018-baek-a01": [("energy_hearings_ai", "research/reviews/energy-reviews-social.json"), ("root_ai", "research/reviews/root-reviews-social.json")],
    "cannkg2018-baek-a02": [("energy_hearings_ai", "research/reviews/energy-reviews-social.json"), ("root_ai", "research/reviews/root-reviews-social.json")],
    "cannkg2018-baek-a03": [("energy_hearings_ai", "research/reviews/energy-reviews-baek-chronology.json")],
    "mindestlohn2026-bda-a01": [("energy_hearings_ai", "research/reviews/energy-reviews-bda-mindestlohn.json")],
    "ggdg2026-hateaid-a01": [("energy_hearings_ai", "research/reviews/energy-reviews-hateaid.json")],
    "ggdg2026-hateaid-a02": [("energy_hearings_ai", "research/reviews/energy-reviews-hateaid-deepfake.json")],
    "ggdg2026-sdc-root01": [("social_digital_independent_ai", "research/reviews/social-reviews-sdc.json")],
    "luftvst2026-bdi-tax04": [("social_digital_independent_ai", "research/reviews/social-reviews-bdi-airtax.json")],
    "sbgg2023-eggd-a01": [("energy_hearings_ai", "research/reviews/energy-reviews-eggd.json")],
    "bstabg2026-pharmadeutschland-a01": [("energy_hearings_ai", "research/reviews/energy-reviews-pharma.json")],
    "bstabg2026-dzvhae-a01": [("tax_consultations_ai", "research/reviews/tax-reviews-dzvhae.json")],
    "bstabg2026-dzvhae-a02": [("tax_consultations_ai", "research/reviews/tax-reviews-dzvhae.json")],
    "staendg2025-dehoga-tax01": [("social_digital_independent_ai", "research/reviews/social-reviews-dehoga.json")],
}

records = []
primary_sources = {
    "hausgrund-geg-2023-bt20-25-403": "hausgrund-geg-2023",
    "waniczek-wassbg-2024-bt20-25-673": "waniczek-wassbg-2024",
    "bund-enefg-2026": "bund-enefg-2026",
    "vik-enefg-2026-sg2608060032": "vik-enefg-2026-mirror",
    "hansgrohe-enefg-2026": "hansgrohe-enefg-2026",
    "uim-enefg-2026": "uim-enefg-2026",
    "dstg-jstg-2026": "dstg-jstg2026-author",
    "bdst-jstg-2026": "bdst-jstg2026",
    "dehoga-staendg-2025-bt": "dehoga-staendg2025",
    "vdr-tabstaendg-2026": "vdr-tabstaendg-2026",
    "bvte-tabstaendg-2026": "bvte-tabstaendg-2026",
    "sdc-ggdg-20260522": "sdc-ggdg-20260522",
    "hateaid-ggdg-20260522": "hateaid-ggdg-20260522",
    "baek-cannkg-2018": "baek-cannkg-2018",
    "eggd-sbgg-2023": "eggd-sbgg-2023",
    "bdi-luftvst-20260317": "bdi-luftvst-20260317",
    "pharmadeutschland-bstabg-20260420": "pharmadeutschland-bstabg-20260420",
    "dzvhae-bstabg-20260417": "dzvhae-bstabg-20260417",
    "bda-mindestlohn-20260112": "bda-mindestlohn-20260112",
    "dgb-stefeg-20241001": "dgb-stefeg-20241001",
    "dgb-jstgII-20240719": "dgb-jstgII-20240719",
    "algorithmwatch-enefg-2026": "algorithmwatch-enefg-2026",
    "dce-enefg-20260416": "dce-enefg-20260416",
    "financewatch-forg-20260126": "financewatch-forg-20260126",
    "bitkom-begiv-2024": "bitkom-begiv-2024",
    "brak-ip-20260128": "brak-ip-20260128-ministry",
}
primary_sources.update(round2_manifest.get("submission_sources", {}))
for origin in inputs:
    if not (ROOT / origin).is_file():
        if origin in round2_manifest.get("inputs", []):
            raise FileNotFoundError(f"Explicitly manifested issue input is missing: {origin}")
        continue
    raw = read(origin)
    for record in raw if isinstance(raw, list) else [raw]:
        record = copy.deepcopy(record)
        record["research_record"] = origin
        if "request_quote_ref" in record:
            record["request_quote"] = record.pop("request_quote_ref")
        if record["id"] in {"cannkg2018-baek-a03", "mindestlohn2026-bda-a01", "luftvst2026-bdi-tax04", "forg2026-financewatch-tax07", "ipspeicherung2026-brak-root01"}:
            record["reporting_tier"] = "ancillary_minor_chronology_or_attribution"
        if record["document_id"] in primary_sources:
            record["submission_source_id"] = primary_sources[record["document_id"]]
        if "draft_version" in record:
            record["draft"] = record.pop("draft_version")
        if "materiality" in record:
            record["materiality_explanation"] = record.pop("materiality")
        if "direction_reason" in record:
            record["direction_explanation"] = record.pop("direction_reason")
        if "direction_reasoning" in record:
            record["direction_explanation"] = record.pop("direction_reasoning")
        source_ids = record.setdefault("source_ids", [])
        for source in record.pop("sources", []):
            if isinstance(source, str):
                sid = source
            else:
                add_source(source, str(Path(origin).parent))
                sid = source["id"]
            if sid not in source_ids:
                source_ids.append(sid)
        review = record.setdefault("review", {"specialist": None})
        checks = review.pop("independent_ai", []) + review.get("ai_reviews", [])
        checks = [
            {"review_file": c, "review_type": "independent_AI", "specialist_review": False}
            if isinstance(c, str) else c
            for c in checks
        ]
        for check in checks:
            if "file" in check and "review_file" not in check:
                check["review_file"] = check.pop("file")
            if "path" in check and "review_file" not in check:
                check["review_file"] = check.pop("path")
        for reviewer, path in review_links.get(record["id"], []):
            if not (ROOT / path).is_file():
                continue
            if not any(c.get("review_file") == path for c in checks):
                checks.append({
                    "reviewer": reviewer, "date": "2026-10-24",
                    "review_file": path, "review_type": "independent_AI",
                    "specialist_review": False,
                    "note": "See the review and subsequent adjudication; a linked review is not necessarily an endorsement of the final disposition."
                })
        review["ai_reviews"] = checks
        record.setdefault("direction_explanation", "See effect and limits; direction describes the claim’s relationship to the request, not author intent.")
        records.append(record)

# Shared request text is stored once so it can be resolved without duplicating excerpts.
documents = copy.deepcopy(read("research/social-digital/source-registry.json")["documents"])
for path in round2_manifest.get("document_registries", []):
    extra = read(path)
    documents.extend(copy.deepcopy(extra if isinstance(extra, list) else extra["documents"]))
for document in documents:
    document["registry_note"] = "Shared verbatim request quotation, referenced by issues with this document_id."
    if document.get("url"):
        add_source({k: v for k, v in document.items() if k not in {"request_quote", "draft", "registry_note"}}, "research/social-digital")
for record in records:
    if isinstance(record.get("request_quote"), dict) and record["request_quote"].get("quote_id"):
        record["request_quote"]["metadata_file"] = "data/documents.json"
    shared_document = next((d for d in documents if d["id"] == record["document_id"]), None)
    if shared_document and not record.get("draft"):
        record["draft"] = copy.deepcopy(shared_document.get("draft"))
    for source_id in [record.get("submission_source_id"), record.get("draft", {}).get("source_id", record.get("draft", {}).get("id"))]:
        if source_id and source_id not in record["source_ids"]:
            record["source_ids"].append(source_id)
    if not any(d["id"] == record["document_id"] for d in documents):
        documents.append({
            "id": record["document_id"],
            "source_ids": record["source_ids"],
            "draft": record.get("draft"),
            "request_evidence": {"issue_id": record["id"], "field": "request_quote"},
        })

# Repair missing spaces only in English narrative fields. Never alter quotations,
# underlines, identifiers, source URLs, file paths, timestamps or locator strings.
prose_keys = {
    "law_is_about", "they_want", "they_claim", "the_problem", "translation_en",
    "correction", "effect", "limits", "materiality_explanation", "direction_explanation",
    "context_and_alternatives", "context_checks", "context_checked", "provenance_limit",
    "temporal_note", "illustration_only", "note", "comparison", "version_limit",
}


def readable(value, key=None):
    if isinstance(value, dict):
        return {k: readable(v, k) for k, v in value.items()}
    if isinstance(value, list):
        return [readable(v, key) for v in value]
    if isinstance(value, str) and key in prose_keys:
        protected = {}
        def protect(match):
            token = f"PLACEHOLDER{chr(65 + len(protected))}END"
            protected[token] = match.group(0)
            return token
        value = re.sub(r"https?://\S+|\b(?:SG|RV|R)\d+\b|\b[a-z]+\d+(?:-[a-z0-9]+)+\b|§\s*\d+[a-z]\b", protect, value)
        value = re.sub(r"(?<=[A-Za-z])(?=\d)", " ", value)
        value = re.sub(r"(?<=\d)(?=[A-Za-z])", " ", value)
        value = value.replace("Translation:", "Translation: ")
        value = re.sub(r" +", " ", value)
        for token, original in protected.items():
            value = value.replace(token, original)
    return value


records = [readable(r) for r in records]

groups = {
    "findings.json": "provisional_finding",
    "unresolved-leads.json": "unresolved_lead",
    "rejected-candidates.json": "rejected_after_review",
}
for filename, state in groups.items():
    write(filename, sorted([r for r in records if r["finding_state"] == state], key=lambda r: r["id"]))
write("source-registry.json", sorted(source_index.values(), key=lambda s: s["id"]))
write("documents.json", documents)
write("review-index.json", [
    {"file": str(p.relative_to(ROOT)), "specialist_review": False}
    for directory in ["research/reviews"] + round2_manifest.get("review_directories", [])
    for p in sorted((ROOT / directory).glob("*.json"))
])
print(json.dumps({filename: sum(r["finding_state"] == state for r in records) for filename, state in groups.items()}))
