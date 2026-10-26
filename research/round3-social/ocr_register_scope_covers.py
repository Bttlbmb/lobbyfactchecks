import json,pathlib,subprocess,concurrent.futures
P=pathlib.Path('research/round3-social');O=P/'coverage-pdfs/register-date-ocr';O.mkdir(exist_ok=True);m=json.load(open('research/round3-root/coverage/register-archive-manifest.json'))['records'];ids={x['id']for x in json.load(open(P/'coverage-register-social-scope.json'))['documents']};rows=[]
for x in m:
 if x['id']not in ids or x.get('status')!='archived_not_screened':continue
 text=pathlib.Path(x['text_file']).read_text()if x.get('text_file')else'';pages=text.split('\f');first=pages[0]if pages else''
 if x.get('readability')!='ocr_or_visual_read_required'and len(first.strip())>100:continue
 x={**x,'selected_pages':sorted(set([1,min(2,x['extracted_pages']),x['extracted_pages']]))};rows.append(x)
def one(x):
 out=[]
 for pg in x['selected_pages']:
  key=x['id']+'-p'+str(pg);image=O/(key+'.png');txt=O/(key+'.txt')
  if not image.exists():subprocess.run(['pdftoppm','-f',str(pg),'-l',str(pg),'-singlefile','-scale-to','1800','-png',x['local_file'],str(O/key)],capture_output=True,check=True)
  if not txt.exists():subprocess.run(['tesseract',str(image),str(O/key),'-l','eng','--psm','3'],capture_output=True,check=True)
  out.append({'pdf_page':pg,'render':str(image),'ocr_text':str(txt),'ocr_only_not_yet_visually_verified':True})
 return {'SG_id':x['id'],'local_pdf':x['local_file'],'selected_pages':out,'method':'Metadata-onlyOCRoffirst2andlastpage;notfullcontentreview'}
with concurrent.futures.ThreadPoolExecutor(max_workers=4)as ex:out=list(ex.map(one,rows))
(P/'coverage-register-ocr-metadata.json').write_text(json.dumps({'date':'2026-10-25','documents':out,'summary':{'PDFs':len(out),'OCRpages':sum(len(x['selected_pages'])for x in out)},'limits':'OCRtextisnotverifiedquotationorhumanreading;dates/scope/authorshipmustbechecked. Noautomaticfindingorfullreadcount.'},ensure_ascii=False,indent=2)+'\n');print('PDFs',len(out))
for x in out:
 print('\n',x['SG_id']);print(pathlib.Path(x['selected_pages'][0]['ocr_text']).read_text()[:800].replace('\n',' | '))
