import requests,json,pathlib,hashlib,concurrent.futures,urllib.parse
from bs4 import BeautifulSoup
P=pathlib.Path('research/round3-social');urls=[
'https://www.vdk.de/ueber-uns/stellungnahmen/',
'https://www.sovd-bawue.de/sozialpolitik/stellungnahmen/meldungen/stellungnahme-zur-siebten-verordnung-zur-aenderung-der-versorgungsmedizin-verordnung',
'https://gdv-nw.zn-d.de/themen-positionen/detail/500460/',
'https://www.dihk.de/de/newsroom/dihk-zur-westbalkanregelung-kontingent-nicht-halbieren-188126',
'https://www.zdh.de/themen-und-positionen/zdh-positionen/positionspapiere-und-stellungnahmen/',
'https://www.institut-fuer-menschenrechte.de/publikationen']
def one(u):
 r=requests.get(u,timeout=35);key=hashlib.sha256(u.encode()).hexdigest()[:16];fn=P/'coverage-html'/('author-'+key+'.html');fn.write_bytes(r.content);s=BeautifulSoup(r.content,'html.parser');out=[]
 for a in s.find_all('a',href=True):
  label=a.get_text(' ',strip=True);url=urllib.parse.urljoin(r.url,a['href']);
  if any(q in label.lower()or q in url.lower()for q in ['versorgungsmedizin','westbalkan','beschäftigungs','beschaeftigungs']):out.append({'label':label,'url':url})
 return {'url':u,'status':r.status_code,'archive':str(fn),'relevant_links':out,'date':'2026-10-25','purpose':'supplementaryprocessdiscovery;notindexcompletenessproof'}
with concurrent.futures.ThreadPoolExecutor(max_workers=4)as ex:out=list(ex.map(one,urls))
(P/'coverage-author-supplement-pages.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps(out,ensure_ascii=False,indent=2))
