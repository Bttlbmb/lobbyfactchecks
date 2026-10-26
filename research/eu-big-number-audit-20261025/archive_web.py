"""Save public pages used for source comparisons and prior-coverage checks."""
import datetime
import hashlib
import json
import warnings
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    import requests

ROOT = Path(__file__).resolve().parent / "sources"
URLS = {
    "eppo-2024-announcement": "https://www.eppo.europa.eu/media/news/2024-annual-report-eppo-leading-charge-against-eu-fraud-2025-03-03_en",
    "tax-package-announcement": "https://taxation-customs.ec.europa.eu/news/european-commission-proposes-landmark-tax-simplification-package-streamline-compliance-and-boost-2026-06-24_en",
    "commission-simplification-overview": "https://commission.europa.eu/topics/competitiveness/simplification_en",
    "prior-art-wallet-headlines": "https://www.europeanbusinesswallet.com/savings-estimates",
    "prior-art-eudr-costs": "https://www.iisd.org/articles/deep-dive/european-union-deforestation-regulation-uneven-impact",
}


def fetch(item):
    key, url = item
    try:
        response = requests.get(url, timeout=40)
        result = {"id": key, "url": url, "final_url": response.url,
                  "status": response.status_code, "bytes": len(response.content),
                  "retrieved_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  "sha256": hashlib.sha256(response.content).hexdigest()}
        if response.ok:
            path = ROOT / (key + ".html")
            path.write_bytes(response.content)
            result["archive"] = str(path)
        return result
    except Exception as error:
        return {"id": key, "url": url, "error": str(error)}


if __name__ == "__main__":
    rows = list(ThreadPoolExecutor(max_workers=5).map(fetch, URLS.items()))
    (ROOT / "web-fetch-manifest.json").write_text(json.dumps(rows, indent=2))
    for row in rows:
        print(json.dumps(row))
