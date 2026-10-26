"""Archive observed official ZIP members and extract date metadata only."""
import concurrent.futures
import hashlib
import json
import pathlib
import re
import subprocess
import zipfile

BASE = pathlib.Path(__file__).resolve().parents[2]
R = BASE / 'research/round3-energy'
queues = []
for name in ['coverage-bmwe-dataset-download-queue-results.json', 'coverage-bmwe-window-dataset-download-queue-results.json']:
    queues.extend(json.loads((R / name).read_text()))
out = []
for source in queues:
    archive = BASE / source['local_file']
    if archive.suffix != '.zip':
        continue
    with zipfile.ZipFile(archive) as bundle:
        for member in bundle.infolist():
            if member.is_dir():
                continue
            raw = bundle.read(member)
            digest = hashlib.sha256(raw).hexdigest()
            ext = pathlib.PurePosixPath(member.filename).suffix.lower()
            target = R / 'sources/bmwe-members' / (digest[:20] + ext)
            target.parent.mkdir(exist_ok=True)
            if not target.exists():
                target.write_bytes(raw)
            out.append({
                'id': 'bmwe-member-' + digest[:20],
                'member_name': member.filename,
                'member_bytes': len(raw),
                'sha256': digest,
                'local_file': str(target.relative_to(BASE)),
                'archive_file': source['local_file'],
                'archive_url': source['url'],
                'dataset_url': source['dataset_url'],
                'dataset_title': source['dataset_title'],
                'source_page': source['source_page'],
                'depth': 'metadata_only',
                'screened_substantively': False,
                'author_or_date_from_filename_verified': False,
            })

def dates(row):
    row = dict(row)
    p = BASE / row['local_file']
    if p.suffix != '.pdf':
        row['metadata_state'] = 'non_pdf_member_requires_separate_check'
        return row
    if not p.read_bytes().startswith(b'%PDF'):
        row['metadata_state'] = 'invalid_pdf_magic'
        return row
    text = p.with_suffix('.first2.txt')
    subprocess.run(['pdftotext', '-f', '1', '-l', '2', '-layout', str(p), str(text)], capture_output=True)
    t = text.read_text(errors='replace') if text.exists() else ''
    row['metadata_text_file'] = str(text.relative_to(BASE))
    row['metadata_state'] = 'extracted_not_read'
    row['date_candidates'] = [
        {'raw': m.group(), 'context': t[max(0, m.start()-80):m.end()+100].replace('\n', ' ')}
        for m in re.finditer(r'(?<!\d)\d{1,2}\.\d{1,2}\.20\d{2}|\d{1,2}\.\s*(?:Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s*20\d{2}', t)
    ]
    row['date_verified'] = False
    return row

with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
    out = list(ex.map(dates, out))
(R / 'coverage-bmwe-bundle-members.json').write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'members': len(out), 'unique_bytes': len({x['sha256'] for x in out}), 'not_substantively_screened': True}))
