import sys,json,pathlib,re,concurrent.futures,urllib.parse
from bs4 import BeautifulSoup
from crawl_coverage import fetch,BASE,absu

def heading_before(a):
 h=a.find_previous(['h1','h2','h3','h4','h5']);return h.get_text(' ',strip=True) if h else None

def process(x):
 html,meta=fetch(x['url']);s=BeautifulSoup(html,'html.parser');main=s.find('main') or s;h1=main.find('h1');title=h1.get_text(' ',strip=True) if h1 else x['title'];docs=[];related=[]
 for a in main.find_all(attrs={'href':True}):
  u=absu(x['url'],a['href']);t=' '.join(str(v).strip() for v in a.find_all(string=True) if str(v).strip())
  if not t and a.find(['h2','h3','h4']):t=' '.join(a.find(['h2','h3','h4']).strings).strip()
  if re.search(r'\.(pdf|zip|docx?|xlsx?)(?:\?|$)',u,re.I) or '/resource/blob/' in u or '/SharedDocs/Downloads/' in u:
   parent=a.find_parent('li') or a.parent;context=parent.get_text(' ',strip=True);heading=heading_before(a)
   typ='submission' if any(re.search(r'Stellungnahm|Stellungnahme|Stellungnahmen|Stellungnahm|Anhörung',v or '',re.I) for v in [t,u,context,heading]) else 'other_document'
   if re.search(r'(Wortprotokoll|Tagesordnung|Sachverständigenliste|Teilnehmerliste)',t,re.I):typ='committee_record'
   if re.search(r'(Referentenentwurf|Regierungsentwurf|Gesetzentwurf|Wortlaut|Entwurf der Verordnung)',t,re.I) and not re.search(r'Stellungnahm',t,re.I):typ='draft_or_law'
   docs.append({'url':u,'link_title':t,'context':context,'preceding_heading':heading,'inferred_kind':typ,'date_status':'unverified','reading_depth':'collected_link_only'})
  elif re.search(r'Stellungnahm',t,re.I):related.append({'url':u,'link_title':t,'preceding_heading':heading_before(a)})
 # Family ministry publishes its transparent-law timeline as embedded JSON rather than anchor links.
 embedded=[]
 for script in main.find_all('script'):
  text=script.string or script.get_text()
  match=re.search(r'var\s+GLAESERNES_GESETZ\s*=\s*',text)
  if match:
   try:
    data=json.JSONDecoder().raw_decode(text[match.end():])[0];embedded.append(data)
    for stage in data.get('dataPoints',[]):
     for listing in stage.get('documentLists',[]):
      for document in listing.get('documents',[]):
       if not document.get('uri'):continue
       typ='submission' if ('Stellungnahm' in listing.get('title','') or 'Stellungnahm' in document.get('documentName','')) else 'other_document'
       if re.search(r'Referenten|Gesetzentwurf|Verordnung|Gesetz',document.get('documentName',''),re.I) and typ!='submission':typ='draft_or_law'
       docs.append({'url':document['uri'],'link_title':document.get('title'),'context':document.get('text'),'preceding_heading':listing.get('title'),'inferred_kind':typ,'date_status':'unverified' if not document.get('date') else 'structured_document_date_unverified_against_pdf','structured_document_date':document.get('date'),'stage_date':stage.get('date'),'stage_title':stage.get('title'),'reading_depth':'collected_link_only','source_format':'official_embedded_GLAESERNES_GESETZ_JSON'})
   except Exception as err:meta['embedded_json_error']=str(err)
 meta['embedded_timeline_count']=len(embedded)
 unique={}
 for d in docs:
  if d['url'] not in unique:unique[d['url']]=d
  else:unique[d['url']].setdefault('duplicate_link_contexts',[]).append(d['context'])
 meta['title']=title;meta['index_evidence']=x;meta['norm_type']='ordinance' if re.search(r'Verordnung',title,re.I) else 'law' if re.search(r'Gesetz',title,re.I) else 'unverified';meta['documents']=list(unique.values());meta['submission_related_pages']=related;meta['process_text_archive']=meta.get('archive');return meta
if __name__=='__main__':
 name=sys.argv[1];p=BASE/('coverage-index-'+name+'.json');d=json.loads(p.read_text());out=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
  for i,x in enumerate(ex.map(process,d['processes'])):
   out.append(x)
   if (i+1)%25==0:print(name,i+1,flush=True)
 result={'authority':d['authority'],'retrieved_at':'2026-10-25','time_window':{'submission_date_from':'2026-07-25','submission_date_through':'2026-10-24'},'index_evidence':str(p),'index_complete':d['index_complete'],'process_pages':out,'collection_only':True,'limits':'Automatic link and surrounding-heading collection is not factual review. Document dates and submission/attachment identity require verification. Historical index entries retained; no indexdate used as a submissiondate.'}
 (BASE/('coverage-processes-'+name+'.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print('DONE',name,'pages',len(out),'all_doclinks',sum(len(x['documents']) for x in out),'submission_candidates',sum(sum(y['inferred_kind']=='submission' for y in x['documents']) for x in out),flush=True)
