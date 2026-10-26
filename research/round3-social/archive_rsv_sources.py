import requests,pathlib,json,hashlib,concurrent.futures,subprocess
P=pathlib.Path('research/round3-social/sources')
urls={
'baek-rsv-author-20260908.pdf':'https://www.bundesaerztekammer.de/fileadmin/user_upload/BAEK/Politik/Stellungnahmen/RSV-Prophylaxeverordnung_SN_BAEK_08.09.2026.pdf',
'baek-suizid-author-20260728.pdf':'https://www.bundesaerztekammer.de/fileadmin/user_upload/BAEK/Politik/Stellungnahmen/Suizidpraeventionsgesetz_RefE_SN_BAEK_28072026.pdf',
'li-rsv2019-2022.pdf':'https://www.pure.ed.ac.uk/ws/portalfiles/portal/286977589/PIIS0140673622004780.pdf',
'ema-enflonsia.html':'https://www.ema.europa.eu/en/medicines/human/EPAR/enflonsia',
'ema-rsv.html':'https://www.ema.europa.eu/en/human-regulatory-overview/public-health-threats/vaccine-preventable-diseases-key-facts/respiratory-syncytial-virus-rsv',
'sgbv-20i.html':'https://www.gesetze-im-internet.de/sgb_5/__20i.html',
'ifsg-2.html':'https://www.gesetze-im-internet.de/ifsg/__2.html',
'pei-beyfortus-shortage.html':'https://www.pei.de/EN/newsroom/hp-news/2024/240902-beyfortus-import.html',
'baek-legislation-index.html':'https://www.bundesaerztekammer.de/politik/stellungnahmen-gesetzgebung',
'lr-rsv-all.html':'https://www.lobbyregister.bundestag.de/inhalte-der-interessenvertretung/stellungnahmengutachtensuche?q=%22Verordnung+zur+%C3%84nderung+der+RSV-Prophylaxe-Verordnung%22&searchAttributes=printedMatterNumbers%2CdraftBillTitle&sort=UPDATE_DESC'}
def one(item):
 fn,u=item
 try:
  r=requests.get(u,timeout=45);path=P/fn;valid=r.status_code==200 and (not fn.endswith('.pdf') or r.content.startswith(b'%PDF'))
  if valid:
   path.write_bytes(r.content)
   if fn.endswith('.pdf'):subprocess.run(['pdftotext','-layout',str(path),str(path.with_suffix('.txt'))],check=False)
  return {'url':u,'status':r.status_code,'archive':str(path) if valid else None,'sha256':hashlib.sha256(r.content).hexdigest() if valid else None,'content_type':r.headers.get('content-type'),'retrieved_at':'2026-10-25','is_primary_evidence':True}
 except Exception as e:return {'url':u,'error':str(e),'archive':None}
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as e:out=list(e.map(one,urls.items()))
(P/'rsv-supporting-source-archives.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n')
print(json.dumps(out,indent=2,ensure_ascii=False))
