"""Expose finite reading proofs without claiming national or every-claim closure."""
import pathlib,json,datetime
ROOT=pathlib.Path(__file__).resolve().parents[1]
items=[
 ('RSV ordinance amendment','research/round3-social/coverage-rsv-proof.json',8,'Eight published response versions; public-sector/self-governance author boundaries remain separately recorded.'),
 ('Gigabit-Grundbuch-Verordnung','research/round3-tax/coverage-bounded-ggv-itkv-proofs.json',17,'Seventeen published replies: thirteen external positions and four Land responses.'),
 ('IT-Komponentenverordnung','research/round3-tax/coverage-bounded-ggv-itkv-proofs.json',12,'Twelve published replies: three formal external positions, eight Land responses, and one external reply declining a statement.'),
 ('Cash-register legislation','research/round3-tax/coverage-cash-process-version-audit.json',20,'Seventeen authored packages reconcile twenty-five register records; three additional chamber positions. The complete ministry population is not established.'),
 ('Fernunterricht reform','research/round3-social/coverage-ferns-proof.json',35,'Thirty-one unique ministry response versions plus four additional register versions. One undated; exact August draft unavailable.'),
 ('Driving-instruction reform hearing','research/round3-energy/coverage-bounded-driving-instruction-proof.json',6,'Six publicly linked external responses; one BASt government response excluded from this count.'),
 ('BEHG amendment hearing','research/round3-energy/coverage-bounded-behg-proof.json',9,'Nine publicly linked external responses; selected primary and exact-bill checks, with remaining interpretive questions recorded.'),
 ('Frühstartrente hearing','research/round3-tax/coverage-bounded-fruehstart-proof.json',7,'Seven publicly linked external responses, including one full read from the preceding round. Repeated reading adds no version.'),
 ('Land-register IDNrG proposal','research/round3-root/coverage/idnrg-known-public-proof.json',7,'All seven author PDFs in the ministry ZIP; six dated within the window and one undated. Exact delivery not independently authenticated.'),
 ('BioStoffV amendment','research/round3-social/coverage-biostoff-proof.json',9,'All nine published responses; eight external associations and DGUV with external-eligibility boundary pending. Three citation issues concern one document.'),
 ('Network-cost subsidy 2027–2029','research/round3-energy/coverage-bounded-netzkosten-proof.json',21,'All twenty-one publicly downloadable external PDF responses; government replies and withheld contributions separately labelled.'),
 ('Accountant-examination ordinance','research/round3-energy/coverage-bounded-wpexamen-proof.json',2,'Both published external author responses; government material excluded. Exact initial dispatch-version identity remains qualified.'),
 ('KrWaffGenV proposal','research/round3-energy/coverage-bounded-krwaff-proof.json',1,'One published joint external position. The currently served draft may already incorporate requested revisions; no earlier-version error inferred.'),
 ('KLtgV consultation','research/round3-energy/coverage-bounded-kltgv-proof.json',7,'Seven published external PDF responses; government replies and withheld contributions separately labelled.')]
rows=[]
for process,p,n,limits in items:
 if not (ROOT/p).is_file():continue
 rows.append({'process':process,'proof_file':p,'known_authored_versions_or_replies_fully_read':n,'count_scope':limits,'stage':'full_author_text_reading_with_targeted_checks','complete_national_process_population':False,'every_assertion_independently_verified':False,'independent_review':'See the specific proof file and linked review; count review does not repeat every factual check.'})
pilot_index_path=ROOT/'data/factual-check-pilots.json'
if pilot_index_path.is_file():
 for entry in json.loads(pilot_index_path.read_text())['pilots']:
  if entry['status']!='complete':continue
  pilot=json.loads((ROOT/entry['summary']).read_text())
  protocol=json.loads((ROOT/entry['summary']).with_name('protocol.json').read_text())
  process=protocol.get('coverage_process', 'KLtgV consultation' if entry['id']=='kltgv-2026-factual-pilot' else None)
  if pilot['status']=='complete' and process:
   row=next(r for r in rows if r['process']==process)
   row.update({'stage':'full_author_reading_and_systematic_material_claim_assessment_with_independent_peer_review','factual_pilot':entry['ledger'],'claims_assessed':pilot['claims'],'claim_outcomes':pilot['outcomes'],'new_reading_units':0})
out={'id':'bounded-public-response-reading-progress','as_of_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'rows':rows,'aggregate_denominator':None,'scope':'Finite published response sets and register-derived packages. These sets have different date and author-scope gates; do not sum them into the national three-month denominator.','limits':['A full read means all author text was read, with targeted factual and version checks. It does not certify every assertion as true.','Known public sets do not prove absence of unpublished, withheld, late-filed or differently indexed contributions.','Author dates, index publication dates, hearing dates and recipient delivery dates remain separate.','The national denominator, coverage percentage and population error rate remain unestablished.']}
(ROOT/'data/bounded-coverage.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print('bounded proof rows',len(rows))
