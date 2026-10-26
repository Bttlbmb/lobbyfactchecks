import json,pathlib,re,collections
P=pathlib.Path('research/round3-social');src=json.load(open(P/'coverage-register-social-crosscheck.json'))['recipient_domain_selection'];byid={}
for domain,rs in src.items():
 for r in rs:
  if r['id'] not in byid:byid[r['id']]={**r,'recipient_domains':[]}
  byid[r['id']]['recipient_domains'].append(domain)
out=[]
for r in byid.values():
 fields=r['structured_fields'];draft=fields.get('printed-matters-draft-bills',{}).get('text','');rv=fields.get('regulatory-project',{}).get('text','');laws=fields.get('affected-laws',{}).get('text','');context=draft+' '+rv
 is_eu=bool(re.search(r'Europäischen (?:Parlament|Kommission)|Europäische Kommission|Kommissions(?:entwurf|vorschlag)|EU[- ](?:Verordnung|Richtlinie|Biotech|Strategie)|COM\s*\(?20\d\d|ECHA|CLH-Verfahren|Digital Omnibus|MDR und.*IVDR',draft,re.I))
 is_formal=bool(draft) and not is_eu
 if is_formal:
  status='identified_federal_draft_process_metadata';why='Structureddraftfieldidentifiesconcretefederalbill/ordinance/printedmatter;exactversionandcontentmustbecheckedinPDF.'
 elif is_eu:
  status='identified_EU_process_not_federal_draft';why='StructuredfieldreferstoEUlegislativeproposal;keepseparatefromGermanfederallaws/ordinances.'
 elif re.search(r'Haushaltsgesetz|Bundeshaushalt\s*202[67]|Haushaltsentwurf\s*202[67]|Bundeshaushaltsgesetz',rv,re.I):
  status='federal_budget_process_candidate';why='Budgetlegislationidentified;retainforactualHaushaltsbilllinkverification,notgeneralfundingexclusion.'
 elif re.search(r'Gesetz(?:entwurf|esvorhaben| zur| zum| für| über)|verordnung|Gesetzes(?:änderung|reform)|Gesetzgebungs(?:verfahren|vorhaben)|\bBT[- ]Drs|\bBundestagsdrucksache|\b[A-ZÄÖÜ][A-Za-zÄÖÜäöüß]{2,}(?:G|VG|V)\b',rv):
  status='possible_federal_legislation_scope_pending';why='Projectdescriptionmayconcernaconcretefederallaw/ordinancebutnodraftfield;actualPDF/contextrequired.'
 elif re.search(r'Europäisch|EU[- ]|ECHA|CLH[- ]|Kommission|COM\(',rv,re.I):
  status='EU_or_mixed_policy_scope_pending';why='EUcontextwithoutconcreteGermanfederaldraft;checkfornationalimplementationlinkbeforedisposition.'
 else:
  status='general_policy_or_motion_scope_pending';why='Noidentifiedconcretefederaldraftinmetadata;couldcontainafederallegislativerequest,motionorbroadpolicy. DonotcountasoutofscopewithoutPDFcheck.'
 out.append({'id':r['id'],'author':r['registered_author'],'recipient_domains':r['recipient_domains'],'reported_recipient_events':r['recipient_events'],'detail_url':r['detail_url'],'pdf_url':r['pdf_url'],'scope_state':status,'scope_reason':why,'evidence':{'draft_field':draft,'project_field':rv,'affected_law_field':laws},'scope_check_depth':'structured_register_metadata_triage','content_read_depth':'not_read','actual_document_date':None,'version_identity':'pending_archivedPDFcomparison'})
# Individually checked scope corrections: a Bundestag printed matter is not necessarily a bill.
overrides={
 'SG2609190004':('parliamentary_question_adjacent_not_identified_bill','Metadata expressly says answer to KleineAnfrage21/4974; retain relatedpsychotherapyadvocacy asadjacent, notidentifiedlegislativebill.'),
 'SG2609300201':('parliamentary_question_adjacent_not_identified_bill','PrimaryBT21/7402physical1 labelsKleineAnfrage29July2026; plannedfuturebillmentionedthereisnotitselfthisprintedmatter.'),
 'SG2609240049':('identified_EU_process_not_federal_draft','Fullmetadata identifiesCommissionEUpovertystrategyandBT21/6499listofreferredEUdocuments, notGermanfederalbill.'),
 'SG2608060013':('federal_draft_candidate_with_motion_reference','StructuredBT20/7630isamotion(primaryphysical1Antrag), butRVexplicitlynamesSuizidPrävG-E. Keepcandidate;verifyactualPDFdraft/version.'),
 'SG2608110010':('motion_and_possible_federal_draft_scope_pending','BT20/7630isamotion(primaryphysical1Antrag);otherprintedmatterandgenericrequestedSuizidlawneedPDFscopeverification, notautomaticformalbill.'),
 'SG2610070030':('identified_federal_amendment_process_metadata','FullRVexpresslyidentifiesNotfallversorgungomnibusandAusschussdrucksache21(14)207amendment5; draftfieldabsenceisnotabsenceofaconcreteprocess.'),
 'SG2609110020':('identified_federal_ordinance_process_metadata','FullRVnamesRentenübersichtsauthentifizierungsverordnungandpreciseproposedtrust-levelchange, correspondingBMASordinanceprocess.'),
 'SG2609160001':('identified_federal_draft_candidate_metadata','ModernisierungFernunterrichtsschutzgesetz isconcretecurrentprocess; exactrefe/versionrequiresPDF.'),
 'SG2609100008':('identified_federal_draft_candidate_metadata','AbolitionFernUSGandtransitionrequest correspondscurrentFernunterrichtreform; exactaddresseddraftrequiresPDF.')
}
for x in out:
 if x['id']in overrides:x['scope_state'],x['scope_reason']=overrides[x['id']];x['manual_metadata_adjudication']=True
archive=json.load(open('research/round3-root/coverage/register-archive-manifest.json'));ad={r['id']:r for r in archive['records']};official=json.load(open(P/'coverage-window-collected.json'))['documents'];oh=collections.defaultdict(list)
for x in official:
 if x.get('sha256'):oh[x['sha256']].append({'url':x['url'],'local_pdf':x['local_pdf'],'process':x['process']})
for x in out:
 a=ad.get(x['id'])
 if a and a.get('status')=='archived_not_screened':
  x['register_archive']={k:a.get(k)for k in ['status','local_file','text_file','sha256','extracted_pages','readability']};x['exact_byte_mirrors_in_official_candidate_set']=oh.get(a['sha256'],[])
adjudication_file=P/'register_pdf_scope_adjudications.json'
if adjudication_file.exists():
 known={r['id']:r for r in json.load(open(adjudication_file))['adjudications']}
 for x in out:
  if x['id']in known:
   x['actual_pdf_metadata_adjudication']=known[x['id']];x['content_read_depth']=known[x['id']]['depth']
   if known[x['id']].get('scope_state_after_pdf_metadata_check'):
    x['registered_metadata_scope_state']=x['scope_state'];x['scope_state']=known[x['id']]['scope_state_after_pdf_metadata_check'];x['scope_reason']='ActualPDFselectedmetadataadjudication supersedes registry-only process guess; seeevidencelocators.'
matchfile=P/'coverage-register-official-text-matches.json'
if matchfile.exists():
 match_by_id={x['SG_id']:x for x in json.load(open(matchfile))['matches']}
 for x in out:
  if x['id']in match_by_id:
   x['official_candidate_text_identity']=match_by_id[x['id']]
   if any(z['byte_identical']for z in match_by_id[x['id']]['matched_files']):
    x['official_byte_identity_scope_evidence']='Exact same PDF published as a response in authoritative ministry chapter; use actual process metadata from that chapter, retaining register field as historical description.'
   if x['id']in ['SG2608110010','SG2608060013']:
    x['scope_state']='identified_federal_draft_from_exact_ministry_mirror';x['scope_reason']='ExactbyteidenticalcurrentSuizidPrävGresponseinBMG21LPchapter;register20/7630motionfieldisbackgroundanddoesnotdetermineactualPDFscope.'
result={'as_of':'2026-10-25','source':'research/round3-root/coverage/register-window-records.json','selection':'Recipientministrydomaincrosscheck;overlapdeduplicatedbySGID. NotallBundestag-onlyhealth/socialrecordswillappear.','documents':out,'summary':{'unique_SG_ids':len(out),'by_scope_state':dict(collections.Counter(x['scope_state']for x in out)),'actual_PDFs_currently_archived':sum('register_archive'in x for x in out)},'limits':['Metadata classificationispreliminary;formalstatute/ordinance/motiontypeandexactdraftmustbeverifiedagainstPDF.','EUlegislationkeptseparatebutmixednationalimplementationargumentscanrequireadditionalclassification.','Noactualdocumentdateinferredfromreportedrecipientdate;theregisterfiltercoversrecipientdeliverydates.','Generalpolicy/fundingisnotexcludedwhereanactualHaushaltsgesetzorconcretebillisreferenced.','NoPDFcontentreadingimpliedbyarchiveorhashcomparison.']}
(P/'coverage-register-social-scope.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(result['summary'])

