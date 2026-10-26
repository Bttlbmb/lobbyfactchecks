import requests,pathlib,hashlib,json,subprocess,concurrent.futures
P=pathlib.Path('research/round3-social/sources');items=[('suizid-refe-20260625.pdf','https://www.bundesgesundheitsministerium.de/fileadmin/Dateien/3_Downloads/Gesetze_und_Verordnungen/GuV/S/Suizidpraeventionsgesetz_RefE_LP-21.pdf'),('priovi-clinical-report-20240124.pdf','https://priovi.de/downloads/Studienbericht_priovi.pdf'),('priovi-fachkreise.html','https://priovi.de/fachkreise/')]
def one(x):
 fn,u=x;r=requests.get(u,timeout=45);p=P/fn;ok=r.ok and(not fn.endswith('.pdf')or r.content.startswith(b'%PDF'))
 if ok:
  p.write_bytes(r.content)
  if fn.endswith('.pdf'):subprocess.run(['pdftotext','-layout',str(p),str(p.with_suffix('.txt'))],check=True)
 return{'url':u,'status':r.status_code,'local_file':str(p)if ok else None,'sha256':hashlib.sha256(r.content).hexdigest()if ok else None,'retrieved_at':'2026-10-25'}
with concurrent.futures.ThreadPoolExecutor(max_workers=3)as e:out=list(e.map(one,items))
(P/'gaia-supporting-source-archives.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(out)
