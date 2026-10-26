from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import parse_qs,urlsplit,unquote
from datetime import datetime
import json,re,hashlib,collections,concurrent.futures,subprocess
ROOT=Path.cwd();BASE=ROOT/'research/round3-root/coverage'
records=json.loads((BASE/'register-window-records.json').read_text());manifest=json.loads((BASE/'register-archive-manifest.json').read_text());fetches=json.loads((BASE/'register-window-fetch-log.json').read_text())
pages=[];allids=[]
for i in range(1,17):
 p=BASE/f'sources/register-window-page-{i}.html';blob=p.read_bytes();s=BeautifulSoup(blob,'html.parser')
 ids=[a.get_text(strip=True) for a in s.select('a.detailsPageLink') if re.fullmatch(r'SG\d{10}',a.get_text(strip=True))]
 text=s.get_text(' ',strip=True);banner='Zeitraum der SG-Abgabe ggü. Adressatinnen und Adressaten:' in text and '25.07.2026 bis24.10.2026'.replace('bis','bis ') in text
 # Whitespace-insensitive check of the actual displayed active-filter banner, rather than URL only.
 banner=bool(re.search(r'Zeitraum der SG-Abgabe ggü\. Adressatinnen und Adressaten:\s*25\.07\.2026\s+bis\s+24\.10\.2026',text))
 selected=s.select_one('a.link-pagination[aria-current="page"]');current=int(parse_qs(urlsplit(selected['href']).query).get('page',['1'])[0]) if selected else None
 pages.append({'page':i,'sg_detail_links':len(ids),'unique_ids':len(set(ids)),'active_recipient_date_banner_verified':banner,'selected_pagination_page':current,'sha256':hashlib.sha256(blob).hexdigest()});allids.extend(ids)
fetch_hash_failures=[]
for r in fetches:
 p=ROOT/r['local_file']
 if hashlib.sha256(p.read_bytes()).hexdigest()!=r['sha256']:fetch_hash_failures.append(r['local_file'])
start=datetime(2026,7,25).date();end=datetime(2026,10,24).date();missing=[];unparseable=[];eventdates=[]
for r in records['records']:
 dates=[]
 for event in r['recipient_events']:
  try:date=datetime.strptime(event['date'],'%d.%m.%Y').date();dates.append(date);eventdates.append(date)
  except Exception:unparseable.append({'id':r['id'],'date':event.get('date')})
 if not any(start<=date<=end for date in dates):missing.append(r['id'])
def check_file(r):
 p=ROOT/r['local_file'];blob=p.read_bytes();info=subprocess.run(['pdfinfo',str(p)],capture_output=True,text=True)
 match=re.search(r'^Pages:\s+(\d+)',info.stdout,re.M)
 return {'id':r['id'],'pdf_header':blob.startswith(b'%PDF'),'sha256_matches':hashlib.sha256(blob).hexdigest()==r['sha256'],'bytes_match':len(blob)==r['bytes'],'physical_pages':int(match.group(1)) if match else None,'recorded_pages':r.get('extracted_pages')}
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:files=list(pool.map(check_file,manifest['records']))
summary={'id':'tax-independent-review-root-register-round3','reviewer':'tax_consultations','reviewed_at_utc':datetime.now().astimezone().isoformat(),'scope':'Native register recipient-date-filter census and PDF archive integrity; not eligibility or substantive claim review','inputs':['research/round3-root/coverage/register-window-records.json','research/round3-root/coverage/register-window-fetch-log.json','research/round3-root/coverage/register-archive-manifest.json'],'native_index':{'pages':pages,'enumerated_detail_links':len(allids),'unique_sg_ids':len(set(allids)),'duplicate_sg_ids':[k for k,v in collections.Counter(allids).items() if v>1],'matches_metadata_ids':set(allids)=={r['id'] for r in records['records']},'all16active_recipient_filter_banners_verified':all(r['active_recipient_date_banner_verified'] for r in pages),'fetch_hash_failures':fetch_hash_failures,'all_records_have_at_least_one_in_window_recipient_event':not missing,'records_without_in_window_event':missing,'unparseable_event_dates':unparseable,'earliest_recipient_event_anywhere':str(min(eventdates)),'latest_recipient_event_anywhere':str(max(eventdates))},'archive':{'manifest_records':len(manifest['records']),'unique_record_ids':len({r['id'] for r in manifest['records']}),'binary_sha256_count':len({r['sha256'] for r in manifest['records']}),'physical_pdf_pages_summed_over_records':sum(r['physical_pages'] or 0 for r in files),'physical_pdf_pages_one_per_binary_hash':sum(next(f['physical_pages'] or 0 for f in files if f['id']==r['id']) for r in {r['sha256']:r for r in manifest['records']}.values()),'ocr_or_visual_required_records':sum(r.get('readability')=='ocr_or_visual_read_required' for r in manifest['records']),'file_failures':[r for r in files if not all([r['pdf_header'],r['sha256_matches'],r['bytes_match'],r['physical_pages'] is not None])],'physical_page_mismatches':[r for r in files if r['physical_pages']!=r['recorded_pages']]},'conclusion':'Native source counts and date filter independently checked. Record IDs, binary files, authored versions and in-scope legislative submissions are different units. Archiving and automatic extraction do not establish substantive screening.','limits':['Registrant-reported recipient dates are not independent receipt acknowledgements.','Distinct binary hashes are not necessarily distinct authored submissions: redaction, cover pages and PDF metadata can differ.','The1558SG records include scope-pending EU, administrative and general policy material; not1558eligible German federal legislative submissions.','Current public register retrieval25October2026 is not a frozen historical snapshot as of24October2026.','No factual conclusion about a submission follows from archive integrity.']}
out=ROOT/'research/round3-reviews/tax-reviews-root-register-census.json';out.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'native_ids':len(allids),'unique_ids':len(set(allids)),'all16filter_banners':summary['native_index']['all16active_recipient_filter_banners_verified'],'missing_in_window_event':len(missing),'archive':summary['archive']},ensure_ascii=False))
