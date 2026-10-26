"""Archive public URLs supplied from observed official indexes; no substantive screening."""
import concurrent.futures,hashlib,json,pathlib,sys,time,urllib.request,subprocess
BASE=pathlib.Path(__file__).resolve().parents[2]
queue=BASE/sys.argv[1]; rows=json.loads(queue.read_text()); out=[]
def fetch(x):
 x=dict(x); p=BASE/x['local_file']
 if p.exists() and x.get('reuse_existing',True):
  b=p.read_bytes();x.update(status='existing',bytes=len(b),sha256=hashlib.sha256(b).hexdigest());return x
 for attempt in range(2):
  try:
   req=urllib.request.Request(x['url'],headers={'User-Agent':'Mozilla/5.0'})
   if 'www.bmv.de' in x['url']:
    c=subprocess.run(['curl','-L','--fail','--silent','--show-error','--max-time','30','-A','Mozilla/5.0',x['url']],capture_output=True,timeout=35)
    if c.returncode:raise RuntimeError(c.stderr.decode(errors='replace'))
    b=c.stdout;r=type('R',(),{'status':200,'url':x['url']})()
   else:
    r=urllib.request.urlopen(req,timeout=35);b=r.read()
   p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
   x.pop('access_error',None)
   x.update(status=r.status,bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),final_url=r.url)
   if b'Radware Page' in b:x['access_error']='Radware challenge, not substantive page despite HTTP200'
   if x['url'].split('?')[0].lower().endswith('.pdf') and not b.startswith(b'%PDF'):x['access_error']='ExpectedPDF, receivedotherbody'
   return x
  except Exception as e:x['access_error']=str(e)
 return x
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:out=list(ex.map(fetch,rows))
outpath=queue.with_name(queue.stem+'-results.json');outpath.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'queue':str(queue.relative_to(BASE)),'requests':len(rows),'access_errors':sum('access_error'in x for x in out),'output':str(outpath.relative_to(BASE))}))
