from pathlib import Path
import json,re,hashlib
pool=json.loads(Path('data/screening-pool.json').read_text())['documents']; original=[]
def words(t):return re.findall(r'[a-zäöüß]+',t.lower())
def grams(t):
 w=words(t);return {hash(tuple(w[i:i+8])) for i in range(len(w)-7)}
for d in pool:
 files=[]
 for f in d.get('local_files',[]):
  p=Path(f)
  if p.suffix=='.txt' and p.exists():files.append(p)
  if p.suffix=='.pdf' and p.with_suffix('.txt').exists():files.append(p.with_suffix('.txt'))
 ss=set()
 for p in set(files):
  try:ss|=grams(p.read_text())
  except UnicodeError:pass
 if ss:original.append((d['id'],ss))
ids=['SG2610220021','SG2610130007','SG2609210006','SG2608260002','SG2609210007','SG2608060005','SG2608050020','SG2610150012','SG2610080031','SG2610080006','SG2608060003','SG2608050026','SG2608060033','SG2609300186','SG2609300084','SG2608240019','SG2609280075','SG2609170015','SG2609300277','SG2609300287','SG2608180005','SG2610060012','SG2608260005','SG2610130030','SG2610190010','SG2608200012']
hearing=['hearing-1191806-response-002','hearing-1183612-response-002','hearing-1183612-response-003','hearing-1183612-response-004','hearing-1217406-response-005','hearing-1217406-response-008']
out=[]
for id in ids+hearing:
 p=Path('research/round3-root/coverage/register-pdfs' if id.startswith('SG') else 'research/round3-tax/sources')/(id+'.txt');g=grams(p.read_text());matches=sorted([(len(g&s)/len(g),x) for x,s in original],reverse=True)[:3] if g else []
 out.append({'original_id':id,'top_existing_pool_overlap':matches,'metric':'Share of distinct eight-word shingles from new text contained in one prior reading unit; alias signal, not conclusive identity.'})
Path('research/round6-tax/text-novelty-audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
for x in out:
 if x['top_existing_pool_overlap'] and x['top_existing_pool_overlap'][0][0]>.75:print(x)
