"""Build bounded source-coverage reports; collection and reading are kept separate."""
from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from collections import Counter
import json,re
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[1]
def load(name):return json.loads((BASE/name).read_text())
def save(name,data):(BASE/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
window={'from':'2026-07-25','through':'2026-10-24','eligibility_basis':'Submission/transmittal/document date, not hearing or publication date; unverified dates are retained.'}
# Ministry legislation master pages, including an honest failure-to-identify entry.
masters=[
{'ministry':'BMF','url':'https://www.bundesfinanzministerium.de/Web/DE/Service/Gesetze_Gesetzesvorhaben/Gesetze_Gesetzgebungsvorhaben.html','access':'live_security_check_blocked','evidence':['research/round3-tax/sources/bmf-master-variants.web.txt','research/round3-tax/sources/bmf-index-pages123.web.txt'],'status':'incomplete','limitations':['Live page presents an explicit security/CAPTCHA check in normal browser, confirmed by root; no challenge bypass attempted.','Official cached reader variants disagree on47/48/49 items and latest date, so cached index pages are leads rather than a current population census.','BMF master additionally limits ordinance coverage to particularly significant ordinances.','Recipient mention in Lobbyregister is not enough to establish a domestic legislative process.']},
{'ministry':'BMDS','url':'https://bmds.bund.de/service/gesetzgebungsverfahren','local_file':'research/round3-tax/sources/bmds-legislation-index.html','access':'retrieved','current_processes':8,'published_response_links':188,'process_inventory':'research/round3-tax/coverage-bmds-processes.json','response_inventory':'research/round3-tax/coverage-bmds-responses.json','status':'current_master_fully_enumerated; historic/completed population not established','limitations':['Eight currently linked pages fully enumerated. Removed/completed process pages outside current master may exist.','Link-level entries include an attachment and distinct consultation phases; not188 deduplicated submissions.','No response date is excluded merely because a process was initiated before the window.']},
{'ministry':'AA','url':'https://www.auswaertiges-amt.de/de/service/opendata/2748494-2748494','local_file':'research/round3-tax/sources/aa-legislation-index.html','access':'retrieved','current_processes':6,'published_response_links_on_master':0,'status':'current_master_fully_enumerated; absence of responses not a zero-population finding','limitations':['Master says it covers consultation initiated since21stterm; earlier proceedings may be outside this index.','Six process/draft or enacted-law links, but no external-response links displayed. A missing link does not establish no responses were submitted.']},
{'ministry':'BMZ','url':None,'access':'no_central_master_identified','checked_pages':['https://www.bmz.de/de','https://www.bmz.de/de/ministerium','https://www.bmz.de/de/themen/privatwirtschaft/wirtschaftspartnerschaftsabkommen-afrikanische-staaten'],'evidence':['research/round3-tax/sources/bmz-home.html','research/round3-tax/sources/bmz-ministry.html','research/round3-tax/sources/bmz-epa-index.html'],'status':'incomplete','limitations':['No central legislative consultation index was identified from official homepage/ministry navigation or targeted primary-source discovery.','The EPA page lists four treaty bills and a11July2025 consultation deadline, but no external responses. No inference of no later submissions is made.']},
{'ministry':'BMVg','url':'https://www.bmvg.de/de/service/gesetze-und-verordnungen/gesetzgebungsverfahren-bmvg','local_file':'research/round3-tax/sources/bmvg-legislation-index.html','access':'retrieved','response_pages_linked_by_master':37,'reserve_responses':17,'response_inventory':'research/round3-tax/coverage-bmvg-responses.json','status':'current_master_enumerated; completeness challenged by missing contemporary process','limitations':['Current2026 section lists only ReserveStG, while official homepage separately announces anOctober2026 infrastructure-acceleration bill. Root crosschecks Defence committee and register.','All37 response pages linked by the historical master are being enumerated, so earlier-process responses are not silently discarded.','German Bundeswehrverband response is expressly withheld for non-consent on ReserveStG page.']}
]
# AA lists process headings then the associated draft link directly.
s=BeautifulSoup((BASE/'sources/aa-legislation-index.html').read_text(),'html.parser');aa=[]
main=s.find('main') or s
for h in main.find_all(['h2','h3']):
 title=h.get_text(' ',strip=True)
 if not title.startswith(('Entwurf','Verordnung','Gesetz zu')):continue
 a=h.find_next('a',href=True)
 aa.append({'title':title,'type':'ordinance' if title.startswith('Verordnung') else 'treaty_ratification_bill_or_enacted_act','url':urljoin(masters[2]['url'],a['href']) if a else None,'external_response_links_displayed':0,'depth':'index_metadata_read'})
masters[2]['processes']=aa
save('coverage-ministry-master-audit.json',{'window':window,'ministries':masters,'source_collection_status':'metadata/date census; not complete substantive screening'})
# Register crosswalk: broad candidates only, with source fields preserved.
register=json.loads((ROOT/'research/round3-root/coverage/register-window-records.json').read_text())['records']
reconciliation=[]
for ministry in ['BMF','BMDS','BMZ','AA','BMVg']:
 marker='('+ministry+')';rows=[]
 for r in register:
  if marker not in str(r.get('recipient_events',[]))+str(r.get('structured_fields',{})):continue
  fields=r.get('structured_fields',{})
  rows.append({'id':r['id'],'author':r.get('registered_author'),'recipient_events':r.get('recipient_events'),'regulatory_project':fields.get('regulatory-project'),'draft_field':fields.get('printed-matters-draft-bills'),'response_url':r.get('pdf_url'),'detail_url':r.get('detail_url'),'content_screening_status':'not_newly_screened_by_this_census','eligibility_status':'scope_pending; ministry mention alone is not a domestic legislative submission','source_record_file':'research/round3-root/coverage/register-window-records.json'})
 reconciliation.append({'ministry':ministry,'broad_candidate_count':len(rows),'records':rows})
save('coverage-register-ministry-crosswalk.json',{'window':window,'method':'Exact parenthesised ministry acronym in recipient events or structured fields; broad crosscheck, not a confirmed ministry consultation count. Root global1558SG census is the authoritative enumeration source.','ministries':reconciliation})
# Document API vs hearing response reconciliation by exact normalised URL.
hearing=load('coverage-bt-response-links.json');pub=load('coverage-bt-document-publication-index.json')
energy=json.loads((ROOT/'research/round3-energy/coverage-bundestag-submission-metadata.json').read_text());urls={r['response_url'] for r in hearing['documents']}
extra=[r for r in energy if r.get('channel')=='bt-energy' and r.get('url') not in urls]
save('coverage-bt-index-reconciliation.json',{'window':window,'hearing_masters':[{'committee':'Finance','declared_hits':21,'enumerated_pages':21},{'committee':'Budget','declared_hits':3,'enumerated_pages':3},{'committee':'Economy','declared_hits':26,'enumerated_pages':26}],'hearing_response_link_count':len(hearing['documents']),'hearing_response_access':dict(Counter(r.get('access') for r in hearing['documents'])),'additional_publication_index_responses':extra,'general_document_publication_index_file':'research/round3-tax/coverage-bt-document-publication-index.json','limitations':['Current21stterm hearing master pages fully paginated; earlier-term hearing archives not enumerated by this branch.','Finance/Budget publication APIs checked through the first page crossing below25July publication date; publication boundary is only a discovery control, not eligibility date.','Upcoming November hearing pages have no statements yet displayed, butOctober statements already published through the register remain eligible.','Budget API displayed agendas, while hearing pages supplied10responses. Economy API supplied oneBDIEnEfGresponse missing from hearing page.','Publication-only metadata and extracted PDFs are not labelled full substantive screening.','Deduplication by URL alone is not enough to merge mirrors or materially distinct versions.']})
print('Master audit and crosswalk saved; broad candidate counts',[(x['ministry'],x['broad_candidate_count']) for x in reconciliation])
