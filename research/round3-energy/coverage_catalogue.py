"""List observed official page attachments, keeping metadata separate from content reads."""
import collections,hashlib,json,pathlib,re,urllib.parse
from bs4 import BeautifulSoup
BASE=pathlib.Path(__file__).resolve().parents[2];ROOT=BASE/'research/round3-energy'
manifest_names=['coverage-page-manifest.json','coverage-next-queue-results.json','coverage-expand-queue-results.json','coverage-bmv-curl-queue-results.json','coverage-process-expand-queue-results.json','coverage-bmwe-process-queue-results.json','coverage-bmukn-historical-queue-results.json']
pages={}
for name in manifest_names:
 p=ROOT/name
 if not p.exists():continue
 for x in json.loads(p.read_text()):
  if x.get('channel')not in ['BMV','BMWSB','BMUKN','BMUKN_historical','BMWE']:continue
  f=BASE/x.get('local_file','MISSING')
  if not f.is_file() or x.get('access_error')or x.get('error'):continue
  b=f.read_bytes()
  if b'Radware Page'in b:continue
  u=urllib.parse.urlsplit(x['url']);key=urllib.parse.urlunsplit((u.scheme,u.netloc,u.path,'',''));pages[key]=x
out=[];pdfqueue=[]
for key,x in pages.items():
 p=BASE/x['local_file'];s=BeautifulSoup(p.read_bytes(),'html.parser');heads=[h.get_text(' ',strip=True) for h in s.find_all('h1') if h.get_text(' ',strip=True) not in ['', 'Navigation', 'Servicemenü']];title=heads[0] if heads else (s.title.get_text(' ',strip=True) if s.title else x.get('title'))
 # Do not treat an index page as a processpage.
 if any(t in key for t in ['/ministerium/gesetzgebungsverfahren/gesetzgebungsverfahren.html','/ministerium/gesetze?']):continue
 process={'id':'process-'+hashlib.sha256(key.encode()).hexdigest()[:12],'channel':'BMUKN' if x['channel']=='BMUKN_historical' else x['channel'],'url':key,'source_url':x['url'],'title':title,'local_file':x['local_file'],'attachments':[],'depth':'metadata_only','screened_substantively':False}
 for tag in s(['script','style','nav','header','footer']):tag.decompose()
 text=s.get_text(' ',strip=True);process['date_context']=[text[max(0,m.start()-100):m.end()+140]for m in re.finditer(r'(?:Aktualisierungsdatum|Stellungnahmen?[^.]{0,50}bis|Frist[^.]{0,50}|Stand:|Veröffentlichungsdatum|Länder- und Verbändeanhörung)',text)][:8]
 if re.search(r'\bfünf Absender[^.]{0,120}Veröffentlichung widersprochen',text,re.I):process['publication_gap']='Page expressly states five senders opposed publication; their identities/content unavailable.'
 seen=set()
 for a in s.select('a[href]'):
  url=urllib.parse.urljoin(key,a['href']);path=urllib.parse.urlsplit(url).path
  if '.pdf'not in path.lower()and'.zip'not in path.lower():continue
  if url in seen:continue
  seen.add(url);label=a.get('title')or a.get_text(' ',strip=True)
  if x['channel'] in ['BMUKN','BMUKN_historical']:
   box=a.find_parent(class_='c-download');head=box.find(['h3','h4'])if box else None
   if head:label=head.get_text(' ',strip=True)
  label=re.sub(r'^Öffnet Dokument\s*','',label)
  hint=(url+' '+label).lower();kind='unclassified_attachment'
  if 'stellungnah'in hint or '/stn_'in hint or '_stn_'in hint or 'glaeserne_gesetze' in hint and '/stellungnahmen/'in hint:kind='submission'
  elif any(k in hint for k in ['referentenentwurf','entwurf','-refe','_refe','gesetzesentwurf','kabinett','synopse']):kind='draft_or_process_document'
  elif '.zip'in path.lower():kind='archive_container'
  item={'title':label,'url':url,'kind':kind,'source_page':x['local_file'],'source_process_id':process['id'],'process':title,'ministry':'BMUKN' if x['channel']=='BMUKN_historical' else x['channel'],'date_basis':'not_yet_verified_from_submission','depth':'metadata_only','screened_substantively':False}
  if kind=='submission':
   item['id']='ministry-'+hashlib.sha256(url.encode()).hexdigest()[:16]
   item['local_file']='research/round3-energy/sources/submissions/'+item['id']+('.zip'if '.zip'in path.lower()else'.pdf')
   pdfqueue.append(item)
  process['attachments'].append(item)
 out.append(process)
(ROOT/'coverage-ministry-process-catalogue.json').write_text(json.dumps({'processes':out,'scope':'All successfullyretrieved processpages fromobservedofficialindexes; incompletewhereaccessgap. Attachmentenumerationdoesnot implycontentread ordateeligibility.'},ensure_ascii=False,indent=2)+'\n')
pdfqueue=list({x['url']:x for x in pdfqueue}.values());(ROOT/'coverage-ministry-all-observed-pdf-queue.json').write_text(json.dumps(pdfqueue,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'processes':len(out),'bychannel':dict(collections.Counter(x['channel']for x in out)),'submission_attachments':len(pdfqueue),'bychannelattachments':dict(collections.Counter(x['ministry']for x in pdfqueue))},ensure_ascii=False))
