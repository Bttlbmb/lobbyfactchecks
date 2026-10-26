"""Remove ignored source downloads while preserving recovery metadata and authored records."""

import argparse
import hashlib
import json
import subprocess
import zipfile
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "research/cache-manifest.json"
RAW_SUFFIXES = {
    ".pdf", ".html", ".htm", ".txt", ".png", ".jpg", ".jpeg", ".zip",
    ".csv", ".tsv", ".xlsx", ".xls", ".docx", ".gz", ".xml", ".js",
    ".download", ".empty", ".empty-response", ".download-failed-empty",
    ".retrieval", ".partial", ".cookies",
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Write manifest, then remove the listed ignored files")
    parser.add_argument("--exclude", action="append", default=[], help="Leave a directory owned by ongoing work untouched")
    args = parser.parse_args()
    ignored = subprocess.check_output(
        ["git", "ls-files", "--others", "--ignored", "--exclude-standard", "-z"], cwd=ROOT
    )
    candidates = {}
    for raw in ignored.split(b"\0"):
        if not raw:
            continue
        name = raw.decode()
        path = ROOT / name
        if not name.startswith(("research/", "tmp/")) or path.is_symlink() or not path.is_file():
            continue
        if any(name.startswith(prefix.rstrip("/") + "/") for prefix in args.exclude):
            continue
        browser_capture = path.suffix == ".json" and "-browser-" in path.name and "sources" in path.parts
        if path.suffix in RAW_SUFFIXES or browser_capture:
            candidates[name] = path
    manifest = json.loads(MANIFEST.read_text())
    candidate_names = set(candidates)
    old = {entry["path"]: entry for entry in manifest["files"]}
    links = defaultdict(list)
    hashes = defaultdict(list)
    by_name = defaultdict(list)
    for name, path in candidates.items():
        by_name[path.name].append(name)

    def register(name, url, metadata, node):
        item = {"url": url, "metadata_file": metadata}
        for key in ("sha256", "member", "zip_member", "retrieved_at", "accessed_at"):
            if node.get(key):
                item[key] = node[key]
        links[name].append(item)
        if node.get("sha256"):
            hashes[node["sha256"]].append(item)

    def visit(node, metadata):
        if isinstance(node, list):
            for value in node:
                visit(value, metadata)
        elif isinstance(node, dict):
            url = next((node[k] for k in ("url", "original_url", "download_url", "resolved_url", "source_url", "pdf_url", "source", "official_url")
                        if isinstance(node.get(k), str) and node[k].startswith(("https://", "http://"))), None)
            if not url and isinstance(node.get("urls"), list) and len(node["urls"]) == 1:
                url = node["urls"][0]
            if not url:
                urls = [value for value in node.values() if isinstance(value, str) and value.startswith(("https://", "http://"))]
                if len(set(urls)) == 1:
                    url = urls[0]
            if url:
                values = []
                for value in node.values():
                    values.extend(value if isinstance(value, list) else [value])
                for value in values:
                    if not isinstance(value, str) or value.startswith(("http:", "https:")):
                        continue
                    value = value.removeprefix(str(ROOT) + "/")
                    possible = {value, str(Path(metadata).parent / value)}
                    if len(by_name.get(Path(value).name, [])) == 1:
                        possible.update(by_name[Path(value).name])
                    for name in possible.intersection(candidate_names):
                        register(name, url, metadata, node)
                if node.get("sha256"):
                    hashes[node["sha256"]].append({"url": url, "metadata_file": metadata})
            for value in node.values():
                if isinstance(value, (dict, list)):
                    visit(value, metadata)

    for path in sorted((ROOT / "research").rglob("*.json")) + sorted((ROOT / "data").glob("*.json")):
        if path == MANIFEST or str(path.relative_to(ROOT)) in candidates:
            continue
        try:
            visit(json.loads(path.read_text()), str(path.relative_to(ROOT)))
        except (ValueError, UnicodeError):
            continue
    for name, path in candidates.items():
        if path.suffix == ".json":
            try:
                data = json.loads(path.read_text())
                visit(data, name)
                if isinstance(data, dict) and str(data.get("url", "")).startswith(("https://", "http://")):
                    register(name, data["url"], name, data)
            except (ValueError, UnicodeError):
                pass
    for name, path in candidates.items():
        if path.suffix == ".zip" and links.get(name):
            try:
                with zipfile.ZipFile(path) as archive:
                    for member in archive.infolist():
                        if member.is_dir():
                            continue
                        sha = hashlib.sha256(archive.read(member)).hexdigest()
                        hashes[sha].append({"url": links[name][0]["url"], "member": member.filename,
                                            "metadata_file": links[name][0]["metadata_file"]})
            except zipfile.BadZipFile:
                pass
    entries = []
    unmatched = []
    total = 0
    for name, path in sorted(candidates.items()):
        content = path.read_bytes()
        sha = hashlib.sha256(content).hexdigest()
        entry = {"path": name, "bytes": len(content), "sha256": sha}
        previous = old.get(name)
        if previous and previous.get("sha256") == sha:
            entry.update(previous)
        else:
            options = links.get(name) or hashes.get(sha) or []
            if options:
                exact = [x for x in options if x.get("sha256") == sha]
                chosen = (exact or options)[0]
                entry.update({k: v for k, v in chosen.items() if k != "sha256"})
                entry["method"] = "download"
                member = entry.pop("zip_member", None) or entry.get("member")
                if member:
                    entry["member"] = member
                    entry["method"] = "zip_member"
            else:
                entry["method"] = "regenerate" if path.suffix in {".txt", ".png", ".jpg", ".jpeg"} else "metadata_lookup_required"
                entry["recovery_note"] = "Consult preserved source registries and collection logs; no direct restoration URL was authenticated for this path during cleanup."
                if path.suffix in {".pdf", ".html", ".zip"} and content:
                    unmatched.append({"path": name, "bytes": len(content)})
        if path.suffix in {".txt", ".png", ".jpg", ".jpeg"}:
            # An extraction or render must not be restored as if it were original source bytes.
            entry["method"] = "regenerate"
        entry["evicted_on"] = date.today().isoformat()
        entries.append(entry)
        total += len(content)
    print(json.dumps({"files": len(entries), "bytes": total,
                      "without_direct_url": sum(not x.get("url") for x in entries),
                      "unmatched_originals": len(unmatched),
                      "largest_unmatched": sorted(unmatched, key=lambda x: x["bytes"], reverse=True)[:12]}, indent=2))
    if not args.apply:
        return
    for entry in entries:
        previous = old.get(entry["path"])
        if previous and previous.get("sha256") != entry["sha256"]:
            # Preserve old identity rather than silently replacing its historical record.
            entry["previous_manifest_record"] = previous
        old[entry["path"]] = entry
    manifest["files"] = list(old.values())
    manifest["last_cleanup_date"] = date.today().isoformat()
    manifest["purpose"] = "MVP links-first source storage. Historical downloads and regenerable extractions are absent by design; authored records and short evidence excerpts remain. Restore only a source needed for a new check."
    manifest["removed_bytes"] = sum(x["bytes"] for x in manifest["files"])
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    for entry in entries:
        path = ROOT / entry["path"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
            raise ValueError(f"File changed during cleanup; left untouched: {path}")
        path.unlink()
    for path in sorted((ROOT / "research").rglob("*"), key=lambda p: len(p.parts), reverse=True):
        if path.is_dir() and not path.is_symlink() and not any(path.iterdir()):
            path.rmdir()


if __name__ == "__main__":
    main()
