"""Archive explicitly listed public official pages and record outgoing PDF links."""
import concurrent.futures
import hashlib
import gzip
import json
import pathlib
import sys
import urllib.request
from urllib.parse import urljoin
from bs4 import BeautifulSoup

BASE = pathlib.Path(__file__).resolve().parent
INPUT = pathlib.Path(sys.argv[1])
jobs = json.loads(INPUT.read_text())

def get(job):
    url, name = job['url'], job['id']
    item = dict(job)
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=35) as response:
            blob = response.read()
            item['effective_url'] = response.url
            item['content_type'] = response.headers.get('Content-Type')
        if blob.startswith(b'\x1f\x8b'):
            blob = gzip.decompress(blob)
        file = BASE / 'sources' / (name + '.html')
        file.write_bytes(blob)
        item.update(local_file=str(file.relative_to(BASE.parents[1])), sha256=hashlib.sha256(blob).hexdigest(), access='retrieved')
        soup = BeautifulSoup(blob, 'html.parser')
        main = soup.find('main') or soup.find('article') or soup
        textfile = file.with_suffix('.txt')
        textfile.write_text(main.get_text('\n', strip=True))
        item['text_file'] = str(textfile.relative_to(BASE.parents[1]))
        item['links'] = [{'text': a.get_text(' ', strip=True), 'url': urljoin(item['effective_url'], a['href'])} for a in main.find_all('a', href=True)]
    except Exception as exc:
        item.update(access='failed', error=str(exc))
    return item

with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    results = list(pool.map(get, jobs))
output = INPUT.with_name(INPUT.stem + '-results.json')
output.write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n')
for row in results:
    print(row['id'], row['access'], len(row.get('links', [])))
