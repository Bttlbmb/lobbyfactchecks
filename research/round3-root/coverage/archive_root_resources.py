"""Public collection and extraction only, with file signature checks."""
import json,pathlib,hashlib,subprocess,concurrent.futures,datetime,zipfile,argparse
BASE=pathlib.Path(__file__).resolve().parent;ROOT=BASE.parent.parent.parent;OUT=BASE/'response-resources';OUT.mkdir(exist_ok=True)
known={}
for s in json.load(open(ROOT/'data/source-registry.json')):
 if s.get('url') and s.get('local_file') and (ROOT/s['local_file']).is_file():known[s['url']]=s['local_file']
def job(r):
 u=r['url'];p=OUT/(hashlib.sha256(u.encode()).hexdigest()[:18]+'.download');d=dict(r)
 if u in known:p=ROOT/known[u];d['reused_existing_archive']=True
 elif not p.exists():
  z=subprocess.run(['curl','-sS','-L','--retry','1','--max-time','45','--write-out','%{http_code}','--output',str(p),u],capture_output=True,text=True);d.update(http_status=z.stdout[-3:],returncode=z.returncode)
 if not p.exists():d['archive_status']='failed';return d
 b=p.read_bytes();fmt='pdf' if b.startswith(b'%PDF-') else 'zip' if b.startswith(b'PK') else None
 if not fmt:d.update(archive_status='not_validated_document',local_file=str(p.relative_to(ROOT)));return d
 if p.suffix=='.download':new=p.with_suffix('.'+fmt);p.replace(new);p=new
 d.update(archive_status='archived_not_screened',local_file=str(p.relative_to(ROOT)),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b),format=fmt,retrieved_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
 if fmt=='pdf':
  tx=OUT/(hashlib.sha256(u.encode()).hexdigest()[:18]+'.txt');subprocess.run(['pdftotext','-layout',str(p),str(tx)],capture_output=True)
  if tx.exists():d.update(text_file=str(tx.relative_to(ROOT)),extracted_pages=tx.read_text(errors='replace').count('\f'),reading_status='extracted_not_read')
 else:
  try:
   with zipfile.ZipFile(p) as z:d['container_members']=[{'name':x.filename,'uncompressed_bytes':x.file_size} for x in z.infolist() if not x.is_dir()]
  except Exception as e:d['container_error']=str(e)
 return d
args=argparse.ArgumentParser();args.add_argument('--input',default='root-statement-resource-queue.json');args.add_argument('--output',default='root-statement-resource-archive.json');opts=args.parse_args()
rows=json.load(open(BASE/opts.input));out=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
 for i,r in enumerate(ex.map(job,rows),1):
  out.append(r)
  if i%20==0 or i==len(rows):
   p=BASE/opts.output;tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps({'expected_urls':len(rows),'processed':len(out),'input_queue':opts.input,'records':out,'limit':'Archives and extracted text are not substantive screening.'},ensure_ascii=False,indent=2)+'\n');tmp.replace(p)
  if i%100==0:print('processed',i,'/',len(rows),flush=True)
print('done',len(out),'valid',sum(x['archive_status']=='archived_not_screened' for x in out),flush=True)
