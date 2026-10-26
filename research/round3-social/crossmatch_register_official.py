import json,pathlib,hashlib,collections,re
P=pathlib.Path('research/round3-social');m=json.load(open('research/round3-root/coverage/register-archive-manifest.json'));scope=json.load(open(P/'coverage-register-social-scope.json'))['documents'];ids={x['id']for x in scope};official=json.load(open(P/'coverage-window-collected.json'))['documents']+json.load(open(P/'coverage-author-supplement-documents.json'))['documents'];bytxt=collections.defaultdict(list)
def key(t):return hashlib.sha256(' '.join(t.split()).encode()).hexdigest()
for x in official:
 t=pathlib.Path(x['local_text']).read_text()if x.get('local_text')else''
 if len(t.strip())<100:continue
 bytxt[key(t)].append(x)
rows=[]
for x in m['records']:
 if x['id']not in ids or x.get('status')!='archived_not_screened':continue
 t=pathlib.Path(x['text_file']).read_text()if x.get('text_file')else''
 matches=bytxt.get(key(t),[])if len(t.strip())>100 else[]
 if matches:rows.append({'SG_id':x['id'],'register_pdf':x['local_file'],'register_sha256':x['sha256'],'complete_normalised_extracted_text_hash':key(t),'matched_files':[{'url':z['url'],'local_pdf':z['local_pdf'],'sha256':z['sha256'],'process':z['process'],'byte_identical':z['sha256']==x['sha256']}for z in matches],'content_version_state':'fulltext_identity_candidate;graphics/attachmentsandpublicationeventsseparate','content_reading_implied':False})
out={'as_of':'2026-10-25','social_SG_ids_examined':len(ids),'official_or_author_candidate_files':len(official),'matches':rows,'summary':{'SG_entries_with_complete_normalised_text_match':len(rows),'exact_byte_match_entries':sum(any(z['byte_identical']for z in x['matched_files'])for x in rows)},'adjudicated_examples':[{'SG_id':'SG2609150001','decision':'SameBÄK8Septauthoredversion;fulltextandall3renderedpagesidentityverified.','protocol':'research/round3-social/coverage-rsv-proof.json'},{'SG_id':'SG2609300259','decision':'SameDKG31Augauthoredversionascommitteeprint;allpages2–42extractedtextexactandcoverbodymatchesafteroverlayremoval;actualauthorDKG,registrantFresenius.','metadata_ledger':'research/round3-social/register_pdf_scope_adjudications.json'},{'SG_id':'SG2607290016','decision':'SameDiakonie23July2026authoredversionasministry84ea4456ca9b2680e2;completeextractedtextexact. Registerreportedrecipientdate28July2026isinsidewindowdespiteauthoreddateoutside.','date_semantics':'Do not exclude this version from submissiondatepool using authored-date-only annotation.'}],'limits':'Exacttextidentitydoesnotproverenderedimageidentityorabsenceofunextractedgraphics. Onlyexplicitadjudicatedcasesaremergedasversions;othermatchesareevidenceforfurtherdeduplication. NoactualPDFcontentreadorclaimverificationimplied.'}
(P/'coverage-register-official-text-matches.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(out['summary'])
