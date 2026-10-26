"""Check the publication file set, issue references and local links without sources."""

import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.ids = set()
        self.links = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            if attrs["id"] in self.ids:
                raise ValueError(f"Duplicate HTML id: {attrs['id']}")
            self.ids.add(attrs["id"])
        for attribute in ("href", "src"):
            if attrs.get(attribute):
                self.links.append(attrs[attribute])


def validate(directory):
    root = directory.resolve()
    read = lambda name: json.loads((root / "data" / name).read_text(encoding="utf-8"))
    sources = read("source-registry.json")
    documents = read("documents.json")
    source_ids = {source["id"] for source in sources}
    document_ids = {document["id"] for document in documents}
    if len(source_ids) != len(sources) or len(document_ids) != len(documents):
        raise ValueError("Duplicate source or document identity")
    expected = {"index.html", "about.html", "evidence.css", "favicon.svg", ".nojekyll"}
    expected.update(f"data/{name}" for name in (
        "findings.json", "unresolved-leads.json", "rejected-candidates.json",
        "source-registry.json", "documents.json", "issue.schema.json",
    ))
    seen = set()
    findings = read("findings.json")
    for name, state in (
        ("findings.json", "provisional_finding"),
        ("unresolved-leads.json", "unresolved_lead"),
        ("rejected-candidates.json", "rejected_after_review"),
    ):
        for issue in read(name):
            issue_id = issue["id"]
            if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]*", issue_id) or issue_id in seen:
                raise ValueError(f"Invalid or duplicate issue identity: {issue_id}")
            seen.add(issue_id)
            if issue["finding_state"] != state or issue["document_id"] not in document_ids:
                raise ValueError(f"Invalid state or document reference: {issue_id}")
            if not set(issue["source_ids"]) <= source_ids:
                raise ValueError(f"Unresolved source reference: {issue_id}")
            if issue["submission_source_id"] not in source_ids:
                raise ValueError(f"Unresolved submission reference: {issue_id}")
            if state == "provisional_finding":
                expected.add(f"evidence/{issue_id}.html")
    actual = {str(path.relative_to(root)) for path in root.rglob("*") if path.is_file()}
    if expected != actual:
        raise ValueError(f"Publication file set differs: missing={expected - actual}, extra={actual - expected}")
    pages = {}
    for path in root.rglob("*.html"):
        text = path.read_text(encoding="utf-8")
        if "{{" in text or "/Users/" in text or "file://" in text:
            raise ValueError(f"Unrendered template or local filesystem URL: {path.name}")
        pages[path] = Page(text)
    for path, page in pages.items():
        for link in page.links:
            url = urlsplit(link)
            if url.scheme or url.netloc:
                if url.scheme not in {"https", "http", "mailto"}:
                    raise ValueError(f"Unexpected URL scheme: {link}")
                continue
            if url.path.startswith("/"):
                raise ValueError(f"Link will break on project Pages: {link}")
            target = (path.parent / unquote(url.path)).resolve() if url.path else path
            if not target.is_relative_to(root) or not target.is_file():
                raise ValueError(f"Broken local link in {path.name}: {link}")
            if url.fragment and target in pages and unquote(url.fragment) not in pages[target].ids:
                raise ValueError(f"Broken fragment in {path.name}: {link}")
    homepage = pages[root / "index.html"]
    if not {issue["id"] for issue in findings} <= homepage.ids:
        raise ValueError("Homepage omits finding anchors")
    print(f"Static validation passed: {len(findings)} findings, {len(pages)} HTML pages, {len(actual)} public files.")


if __name__ == "__main__":
    validate(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "dist")
