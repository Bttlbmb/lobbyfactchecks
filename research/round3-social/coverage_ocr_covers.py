import pathlib,json,subprocess,concurrent.futures
BASE=pathlib.Path('research/round3-social/coverage-pdfs');OUT=BASE/'date-ocr';OUT.mkdir(exist_ok=True)
items=[json.load(open(p)) for p in BASE.glob('*.json') if json.load(open(p)).get('extracted_characters',999)<100]
def ocr(x):
 key=pathlib.Path(x['local_pdf']).stem;pages=sorted({1,min(2,x['pdf_pages']),x['pdf_pages']});out=[]
 for page in pages:
  stem=OUT/(key+'-p'+str(page));txt=stem.with_suffix('.txt')
  if not txt.exists():
   subprocess.run(['pdftoppm','-f',str(page),'-l',str(page),'-scale-to','1800','-png','-singlefile',x['local_pdf'],str(stem)],capture_output=True,timeout=30)
   subprocess.run(['tesseract',str(stem)+'.png',str(stem),'-l','eng'],capture_output=True,timeout=35)
  out.append({'pdf_page':page,'image':str(stem)+'.png','ocr_text':str(txt)})
 return {'pdf':x['local_pdf'],'sha256':x['sha256'],'pages':out,'depth':'date_metadata_ocr_only; no full-submission review'}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:r=list(ex.map(ocr,items))
pathlib.Path('research/round3-social/coverage-cover-ocr.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print('OCR cover units',len(r))
