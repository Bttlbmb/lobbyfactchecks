import json,re,collections,datetime
from pathlib import Path
base=Path('research/round3-tax')
a=json.loads((base/'coverage-register-ministry-crosswalk.json').read_text())
rows={}
for m in a['ministries']:
 for r in m['records']:
  z=rows.setdefault(r['id'],dict(r,matched_ministries=[]));z['matched_ministries'].append(m['ministry'])
for r in rows.values():
 d=(r.get('draft_field') or {}).get('text','')
 rv=r['regulatory_project']['text']
 if 'Finanzbildungsstrategie' in d:
  s='non_legislative_strategy_as_described';reason='The draft-field title identifies a financial-education strategy, not a law or ordinance. A registrant-entered Referentenentwurf label alone does not make it a legislative process.';typ='strategy'
 elif 'Vorschlag für eine Verordnung des Europäischen Parlaments' in d or 'Vorschlag für eine Richtlinie des Europäischen Parlaments' in d:
  s='eu_instrument_not_domestic_bill';reason='The explicit draft-field title describes an EU legislative proposal. A Bundesrat printing number and German recipients do not by themselves establish a domestic implementing bill.';typ='eu_proposal'
 elif 'Allgemeinen Verwaltungsvorschrift' in d or 'Lohnsteuer-Richtlinien' in d:
  s='administrative_rule_separate_scope';reason='The draft field identifies administrative tax guidelines. Preserve as a separate scope category rather than silently count it as a law or ordinance.';typ='administrative_rule'
 elif d and ('gesetz' in d.lower() or 'verordnung' in d.lower()):
  s='domestic_legislative_draft_link_in_metadata';reason='The explicit draft-field title identifies a domestic law or ordinance proposal. This supports a process link, but the response body and exact addressed version have not been established by this metadata decision.';typ='ordinance' if 'verordnung' in d.lower() and 'gesetz' not in d.lower() else 'law_or_mixed'
 elif d:
  s='scope_pending';reason='A draft field is present but its title alone is insufficient for a confident scope decision.';typ='unresolved'
 else:
  s='scope_pending_no_explicit_draft_field';reason='No explicit draft field is attached. Regulatory-project descriptions can describe proposals, implementation, administration, strategies or general advocacy; the response body and primary process evidence still need checking.';typ='unresolved'
 r['scope_adjudication']={'status':s,'instrument_type':typ,'basis':'register structured metadata only','reason':reason,'addressed_version':'not established by this decision; registry links can point to a later or earlier version','content_screening_depth':'metadata_only; not a substantive claim screen'}
 r['date_adjudication']={'recipient_date':'in-window self-reported recipient event verified against the archived native register metadata','document_date':'not established by this decision','receipt_independently_verified':False}
counts=collections.Counter(r['scope_adjudication']['status'] for r in rows.values())
out={'id':'round3-tax-register-scope-metadata','as_of_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'window':a['window'],'source_file':'research/round3-tax/coverage-register-ministry-crosswalk.json','unit':'unique SG transmittal record IDs across the five-ministry crosswalk, not unique authored submissions','unique_records':len(rows),'counts':dict(counts),'limitations':['These are metadata-level provisional scope labels, not completed eligibility determinations or substantive screens.','The absence of a draft field is not evidence that a record is outside scope.','The date window is based on self-reported recipient events. It is not derived from the SG identifier, publication date, hearing date or document cover date.','A later upload can report an earlier transmittal. The census is a current retrieval, not a frozen historical register snapshot.','Binary and semantic duplicates must be adjudicated separately while preserving distinct recipient events.'],'records':list(rows.values())}
(base/'coverage-register-scope-metadata.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'unique_records':len(rows),'counts':dict(counts)},ensure_ascii=False))
