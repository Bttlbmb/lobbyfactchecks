import json,collections,datetime
from pathlib import Path
base=Path('research/round3-tax')
man=json.loads(Path('research/round3-root/coverage/register-archive-manifest.json').read_text());print(type(man),list(man)[:4])
byhash=collections.defaultdict(list)
for r in man['records']:
 if r.get('sha256'):byhash[r['sha256']].append(r)
rows=[];channel_counts=collections.Counter()
for file,channel in [('coverage-bt-response-links.json','Bundestag'),('coverage-bmds-responses.json','BMDS'),('coverage-bmvg-all-response-links.json','BMVg')]:
 a=json.loads((base/file).read_text())
 for r in a['documents']:
  matches=byhash.get(r.get('sha256'),[])
  if matches:
   channel_counts[channel]+=1
   rows.append({'resource_id':r['id'],'channel':r.get('committee',channel),'response_url':r.get('response_url'),'local_file':r.get('local_file'),'sha256':r['sha256'],'registry_ids':[x['id'] for x in matches],'registry_files':[x['local_file'] for x in matches],'match_basis':'byte-identical SHA256; no semantic inference','source_inventory':'research/round3-tax/'+file})
out={'as_of_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'method':'Join the independently verified register archive to published ministry/hearing resources by identical binary SHA256. Different PDF covers or metadata may prevent a match even for the same authored response.','matched_resource_links':len(rows),'matched_resource_links_by_channel':dict(channel_counts),'matched_sg_ids':len({x for r in rows for x in r['registry_ids']}),'matches':rows,'limitations':['No match is not evidence of no submission or no same-authored version.','An exact binary match does not establish a recipient timestamp independently of the self-reported register event.','Ministry master omissions and BMF access barriers remain; this does not close the full population.','This crosswalk is source reconciliation, not a substantive claim screen.']}
(base/'coverage-register-channel-binary-crosswalk.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print({k:v for k,v in out.items() if k not in ['matches','limitations','method']})
