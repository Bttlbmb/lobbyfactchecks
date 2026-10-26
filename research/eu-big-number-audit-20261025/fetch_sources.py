"""Archive public EU source documents for a read-only numerical audit."""
import datetime
import hashlib
import json
import subprocess
import warnings
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    import requests

ROOT = Path(__file__).resolve().parent / "sources"
URLS = {
    "wallet-swd837": "https://data.consilium.europa.eu/doc/document/ST-15701-2025-ADD-2/en/pdf",
    "eudr-review2026": "https://environment.ec.europa.eu/document/download/a3c5c3a0-232e-43c4-b0b8-1eecb1df45c7_en?filename=Report+from+the+Commission+to+the+Council+and+Parliament+on+the+EUDR.pdf",
    "eudr-ia2021": "https://data.consilium.europa.eu/doc/document/ST-14151-2021-ADD-3/en/pdf",
    "direct-tax-ia2026": "https://taxation-customs.ec.europa.eu/document/download/dc4034c4-5d0a-47bf-a6ea-22339e16df8c_en?filename=Impact+Assessment_Proposal+for+a+Council+Directive+-+Taxation.pdf",
    "dac-ia2026": "https://taxation-customs.ec.europa.eu/document/download/aec17175-75b0-47b7-9c3e-56e7af08b0e2_en?filename=Impact+Assessment_DAC_Proposal+for+a+Council+Directive+-+Taxation.pdf",
    "direct-tax-annexes2026": "https://taxation-customs.ec.europa.eu/document/download/dda07d79-1b3b-4620-a4f8-53a62eb1761b_en?filename=Annexes_Proposal+for+a+Council+Directive+-+Taxation.pdf",
}


def fetch(item):
    key, url = item
    try:
        response = requests.get(url, timeout=45)
        result = {
            "id": key, "url": url, "final_url": response.url,
            "status": response.status_code, "bytes": len(response.content),
            "retrieved_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "sha256": hashlib.sha256(response.content).hexdigest(),
        }
        if response.ok and response.content.startswith(b"%PDF"):
            path = ROOT / (key + ".pdf")
            path.write_bytes(response.content)
            subprocess.run(["pdftotext", "-layout", str(path), str(path.with_suffix(".txt"))], check=True)
            result["archive"] = str(path)
        else:
            result["preview"] = response.text[:100]
        return result
    except Exception as error:
        return {"id": key, "url": url, "error": str(error)}


if __name__ == "__main__":
    ROOT.mkdir(exist_ok=True)
    rows = list(ThreadPoolExecutor(max_workers=6).map(fetch, URLS.items()))
    (ROOT / "fetch-manifest.json").write_text(json.dumps(rows, indent=2))
    for row in rows:
        print(json.dumps(row))
