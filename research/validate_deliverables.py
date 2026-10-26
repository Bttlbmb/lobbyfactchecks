"""Check the saved JSON, references, archived files and page-located excerpts."""

import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


def read(name):
    return json.loads((DATA / name).read_text())


schema = read("issue.schema.json")
Draft202012Validator.check_schema(schema)
validator = Draft202012Validator(schema)
sources = {s["id"]: s for s in read("source-registry.json")}
documents = {d["id"]: d for d in read("documents.json")}
errors = []
warnings = []
quote_checks = []
records = []
seen = set()


def normal(text, unwrap=False):
    if unwrap:
        text = re.sub(r"-\s*\n\s*", "", text)
    return re.sub(r"\s+", " ", text).strip()


cache = {}
manual_path = ROOT / "research/reviews/manual-quote-checks.json"
manual_checks = {
    (c["issue_id"], c["field"], c["source_id"], c["pdf_page"]): c
    for c in json.loads(manual_path.read_text()).get("checks", [])
}

class VisibleText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hidden = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self.hidden += 1

    def handle_endtag(self, tag):
        if tag in {"script", "style"}:
            self.hidden = max(0, self.hidden - 1)

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def check_quote(issue_id, field, quote, fallback_source=None):
    if not isinstance(quote, dict) or not quote.get("original"):
        return
    source_id = quote.get("source_id", fallback_source)
    locator = quote.get("locator", {})
    page = locator.get("pdf_page")
    check = {"issue_id": issue_id, "field": field, "source_id": source_id, "pdf_page": page}
    source = sources.get(source_id)
    if source is None:
        check["result"] = "source_unresolved"
        errors.append(f"{issue_id}:{field}: unknown source {source_id}")
    elif (source.get("local_file") or "").endswith((".html", ".htm")):
        parser = VisibleText()
        raw_html = (ROOT / source["local_file"]).read_bytes()
        declared = re.search(br"charset\s*=\s*[\"']?([a-zA-Z0-9._-]+)", raw_html[:4096], re.I)
        encoding = source.get("encoding") or (declared.group(1).decode("ascii") if declared else "utf-8")
        parser.feed(raw_html.decode(encoding))
        if normal(quote["original"]) in normal(" ".join(parser.parts)):
            check["result"] = "exact_archived_html_text_after_whitespace_normalisation"
        else:
            check["result"] = "manual_or_web_check_required"
            check["reason"] = "Archived HTML text did not mechanically match; consult recorded web/source review."
    elif not source.get("local_file") or not page:
        check["result"] = "manual_or_web_check_required"
        check["reason"] = "No archived page-addressable PDF; consult the source access note and independent AI review."
    else:
        path = ROOT / source["local_file"]
        if path.suffix.lower() != ".pdf":
            check["result"] = "manual_or_web_check_required"
        else:
            key = (str(path), page)
            if key not in cache:
                result = subprocess.run(
                    ["pdftotext", "-layout", "-f", str(page), "-l", str(page), str(path), "-"],
                    capture_output=True, text=True,
                )
                cache[key] = result
            result = cache[key]
            if result.returncode:
                check["result"] = "extraction_failed"
                errors.append(f"{issue_id}:{field}: PDF page extraction failed")
            elif normal(quote["original"]) in normal(result.stdout):
                check["result"] = "exact_text_after_whitespace_normalisation"
            elif normal(quote["original"]) in normal(result.stdout, unwrap=True):
                check["result"] = "exact_text_after_line_end_hyphen_normalisation"
            else:
                check["result"] = "visual_reading_order_or_exactness_review_required"
                manual = manual_checks.get((issue_id, field, source_id, page))
                if manual and (ROOT / manual["evidence"]).is_file():
                    check["automated_result"] = check["result"]
                    check["result"] = manual["result"]
                    check["manual_review_file"] = str(manual_path.relative_to(ROOT))
                    check["evidence"] = manual["evidence"]
                    check["reason"] = manual["reason"]
                else:
                    warnings.append(f"{issue_id}:{field}: extracted reading order did not match; inspect cited render/review")
    quote_checks.append(check)


for name, state in [
    ("findings.json", "provisional_finding"),
    ("unresolved-leads.json", "unresolved_lead"),
    ("rejected-candidates.json", "rejected_after_review"),
]:
    for record in read(name):
        rid = record.get("id", "MISSING_ID")
        if rid in seen:
            errors.append(f"Duplicate issue id: {rid}")
        seen.add(rid)
        records.append(record)
        for err in validator.iter_errors(record):
            errors.append(f"{rid}: {'/'.join(map(str, err.path))}: {err.message}")
        if record["finding_state"] != state:
            errors.append(f"{rid}: wrong output file for finding_state")
        if record["claim_quote"]["underline"] not in record["claim_quote"]["original"]:
            errors.append(f"{rid}: underline is not an exact substring")
        if not record.get("draft"):
            errors.append(f"{rid}: exact draft metadata missing")
        if record["document_id"] not in documents:
            errors.append(f"{rid}: document metadata missing")
        for sid in record.get("source_ids", []):
            if sid not in sources:
                errors.append(f"{rid}: missing source {sid}")
        completed_reviews = [r for r in record["review"].get("ai_reviews", []) if r.get("review_file")]
        if state == "provisional_finding" and not completed_reviews:
            errors.append(f"{rid}: no independently recorded AI review")
        for review in completed_reviews:
            if not (ROOT / review["review_file"]).is_file():
                errors.append(f"{rid}: missing review file {review['review_file']}")
            elif rid not in (ROOT / review["review_file"]).read_text():
                errors.append(f"{rid}: linked AI review does not identify this issue")
        primary = record.get("submission_source_id")
        check_quote(rid, "claim_quote", record["claim_quote"], primary)
        check_quote(rid, "counter_quote", record["counter_quote"])
        for key, value in record.items():
            if key in {"claim_quote", "counter_quote"}:
                continue
            if isinstance(value, dict) and "original" in value:
                check_quote(rid, key, value, primary)
            elif isinstance(value, list) and "quote" in key:
                for index, quote in enumerate(value):
                    check_quote(rid, f"{key}[{index}]", quote, primary)
        request = record.get("request_quote")
        if isinstance(request, dict) and request.get("quote_id"):
            q = documents[record["document_id"]].get("request_quote", {})
            if q.get("id") != request["quote_id"]:
                errors.append(f"{rid}: unresolved shared request quotation")
        elif request is None and not record.get("request_quote_reference"):
            warnings.append(f"{rid}: no request quotation or reference")

for document_id, document in documents.items():
    if document.get("request_quote", {}).get("original"):
        check_quote(document_id, "shared_request_quote", document["request_quote"], document_id)

archive_checks = []
for sid, source in sources.items():
    if not source.get("local_file"):
        continue
    path = ROOT / source["local_file"]
    check = {"source_id": sid, "local_file": source["local_file"]}
    if not path.is_file():
        errors.append(f"Missing archive: {sid}")
        check["result"] = "missing"
    else:
        content = path.read_bytes()
        check["sha256"] = hashlib.sha256(content).hexdigest()
        check["result"] = "exists_hash_matches"
        if source.get("sha256") and source["sha256"] != check["sha256"]:
            errors.append(f"Hash mismatch: {sid}")
        if path.suffix.lower() == ".pdf" and not content.startswith(b"%PDF-"):
            errors.append(f"PDF archive is not a PDF: {sid}")
    archive_checks.append(check)

report = {
    "checked_at_utc": datetime.now(timezone.utc).isoformat(),
    "result": "pass_with_disclosed_manual_checks" if not errors else "requires_correction",
    "record_count": len(records),
    "errors": errors,
    "warnings": warnings,
    "schema": "data/issue.schema.json, JSON Schema Draft2020-12; validated with jsonschema",
    "quote_checks": quote_checks,
    "archive_checks": archive_checks,
    "limits": "Mechanical validation is not a specialist factual review. PDF text reading order, source access limitations and substantive alternative explanations require the recorded AI reviews and adjudications. No automated result establishes truth or author intent.",
}
(DATA / "validation-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"records": len(records), "errors": errors, "warnings": warnings}, ensure_ascii=False, indent=2))
