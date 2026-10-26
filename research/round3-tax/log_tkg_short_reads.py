import json
from pathlib import Path
b=Path('research/round3-tax');a=json.loads((b/'research-log.json').read_text());version=json.loads((b/'coverage-tkg-autumn-version-audit.json').read_text());rows={r['id']:r for r in version['records']}
results={
'SG2609300067':('sap-tkg-security-202609','Full one-page formulation aid read. Exact addressed draft timestamp remains unverified; current legal-scope assertions were not adjudicated as false.','No issue promoted. The request concerns treatment of negligible supporting telecom activities; a legal interpretation or proposed clarification is not a proven factual error.'),
'SG2609240023':('evvc-tkg-frequency-202609','Full two-page response read. Original government draft proposed §91(1) and its full relevant explanation selectively checked.','No issue promoted. The draft supports the description of frequency use without prior allocation and the relevant authorities’ proportionality assessment. Security-risk projections remain assessments.'),
'SG2608050022':('bdew-breko-vku-tkg-fairplay-202608','Full two-page joint paper read. The underlying market study was not independently audited; no numerical error inferred from that limitation.','No issue promoted. The paper expressly links its alternative agreement request to proposed §22a TKG. Coverage wording can mean availability, not necessarily active subscriptions; no contrary definition is established.')}
for id,(did,extent,result) in results.items():
 r=rows[id];z={'id':did,'author':r['authored_document_author'],'document':'TKG2026 response / supplementary proposal, '+id,'process':'TKG-Änderungsgesetz2026','date':r['document_date'],'date_basis':'No exact printed author date established; in-window transmittal is self-reported in the register','submission_url':r['url'],'local_file':r['local_file'],'registered_ids':[id],'depth':'full_submission','extent':extent,'result':result,'version_evidence':'research/round3-tax/coverage-tkg-autumn-version-audit.json'};a['screened']=[x for x in a['screened'] if x['id']!=did]+[z]
(b/'research-log.json').write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n')
print(len(a['screened']))
