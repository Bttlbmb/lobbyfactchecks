from pathlib import Path
p=Path(__file__).parent/'archive_response_batch.py';ns={'__file__':str(p.resolve())}
exec(p.read_text().split('with concurrent.futures.ThreadPoolExecutor')[0],ns)
ns['source']=Path(__file__).parent/'coverage-bmvg-all-response-links.json';ns['data']=ns['json'].loads(ns['source'].read_text())
for row in ns['json'].loads((Path(__file__).parent/'coverage-bmvg-responses.json').read_text())['documents']:
 if row.get('local_file'):ns['existing'][row['response_url']]={'local_file':row['local_file']}
with ns['concurrent'].futures.ThreadPoolExecutor(max_workers=5) as pool:ns['data']['documents']=list(pool.map(ns['archive'],ns['data']['documents']))
ns['source'].write_text(ns['json'].dumps(ns['data'],ensure_ascii=False,indent=2)+'\n')
print('Rows',len(ns['data']['documents']),'failures',[(r['id'],r.get('error')) for r in ns['data']['documents'] if r.get('access')=='failed'])
