"""Read only published results using the GET requests in the ministry-linked publicpage."""
import concurrent.futures,json,pathlib,re,urllib.request
from bs4 import BeautifulSoup
BASE=pathlib.Path(__file__).resolve().parents[2];ROOT=BASE/'research/round3-energy';DIR=ROOT/'sources/coverage-pages'
def survey(alias):
 p=DIR/f'eusurvey-{alias}.html';html=p.read_text();s=BeautifulSoup(html,'html.parser')
 # Columnorderisexplicitlyrenderedinthepublicpage'sloadMorefunction.
 script=html[html.index('while (i < list.length)'):html.index('while (i < list.length)')+45000]
 cells=re.findall(r'addClass\("cell(\d+)"\)',script);cells=list(dict.fromkeys(cells));width=len(cells)+2
 result={'alias':alias,'public_page_url':'https://ec.europa.eu/eusurvey/publication/'+alias,'public_page_archive':str(p.relative_to(BASE)),'column_ids':cells,'row_width':width,'pages':[],'responses':[],'date_basis':'The public response payload does not expose a submissiontimestamp. Windoweligibilitymustnotbeassumedfromconsultationopening/deadline.','substantive_screening':'collectiononly'}
 for page in range(1,31):
  url=f'https://ec.europa.eu/eusurvey/{alias}/management/resultsJSON?page={page}&rows=40&publicationmode=true';f=DIR/f'eusurvey-{alias}-results-page{page}.json'
  try:
   if not f.exists():f.write_bytes(urllib.request.urlopen(url,timeout=30).read())
   arr=json.loads(f.read_text());result['pages'].append({'page':page,'url':url,'local_file':str(f.relative_to(BASE)),'flat_items':len(arr)})
   if len(arr)<=1:result['pagination_complete']=True;break
   if (len(arr)-1)%width:raise ValueError('Unexpectedflatrowwidth; manualparse required')
   for i in range(1,len(arr),width):
    v=arr[i:i+width];fields=dict(zip(cells,v[2:]));clean=[BeautifulSoup(str(x),'html.parser').get_text(' ',strip=True)for x in v[2:]]
    result['responses'].append({'id':alias+'-'+str(v[1]),'public_response_id':str(v[1]),'public_response_uuid':v[0],'organisation':clean[2]if len(clean)>2 else None,'organisation_type':clean[1]if len(clean)>1 else None,'consent':clean[0]if clean else None,'public_answer_fields':fields,'source_json':str(f.relative_to(BASE)),'flat_array_start_index':i,'depth':'collected_only','screened_substantively':False,'date_verified':False})
  except Exception as e:result['access_or_parse_error']={'page':page,'error':str(e)};break
 result['response_count']=len(result['responses']);return result
with concurrent.futures.ThreadPoolExecutor(max_workers=2)as ex:out=list(ex.map(survey,['ErsatzbaustoffV','RohrFLtgV']))
(ROOT/'coverage-eusurvey-published-responses.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps([{'alias':x['alias'],'responses':x['response_count'],'pagination_complete':x.get('pagination_complete'),'error':x.get('access_or_parse_error'),'row_width':x['row_width']}for x in out]))
