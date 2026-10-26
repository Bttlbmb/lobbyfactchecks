import collections
import json
import pathlib

R = pathlib.Path('research/round3-energy')
members = json.loads((R/'coverage-bmwe-bundle-members.json').read_text())
queues = []
for n in ['coverage-bmwe-dataset-download-queue-results.json','coverage-bmwe-window-dataset-download-queue-results.json']:
    queues += json.loads((R/n).read_text())
by_id = {x['id']:x for x in queues}
packages = []

# Participant numbers and publication markers transcribed from the two-page primary list.
wind_names = [
 '50 Hertz Transmission GmbH','Amprion GmbH','AquaVentus Förderverein e.V.',
 'BDEW Bundesverband der Energie- und Wasserwirtschaft e.V.',
 'Behörde für Umwelt, Klima, Energie und Agrarwirtschaft (FHH Hamburg)',
 'Behörde für Wirtschaft Arbeit und Innovation der Freien und Hansestadt Hamburg',
 'Bp Offshore Wind Deutschland GmbH (Jera Nex bp Deutschland GmbH)',
 'Bundesverband Windenergie Offshore (BWO)','Copenhagen Infrastructure Partners (CIP)',
 'Deutsche Umwelthilfe e.V.','Deutscher Bauernverband','Deutscher Gewerkschaftsbund',
 'Deutscher Wasserstoff-Verband (DWV) e.V.','DVGW Deutscher Verein des Gas- und Wasserfaches e.V.',
 'EnBW Energie Baden-Württemberg AG','Equinor Deutschland GmbH','GASCADE Gastransport GmbH',
 'German Zero e.V. - FG Energie','Heike Winkler','Iberdrola Deutschland GmbH',
 'IG Metall Bezirksleitung Küste',
 'Ministerium für Energiewende, Klimaschutz, Umwelt und Natur des Landes Schleswig-Holstein',
 'Ministerium für Wirtschaft, Industrie, Klimaschutz und Energie des Landes Nordrhein-Westfalen',
 'Ministerium für Wirtschaft, Infrastruktur, Tourismus und Arbeit Mecklenburg-Vorpommern',
 'NABU (Naturschutzbund Deutschland) e.V.',
 'Niedersächsisches Ministerium für Umwelt, Energie und Klimaschutz',
 'Niedersächsisches Ministerium für Wirtschaft, Verkehr und Bauen','Orsted Germany GmbH','RWE',
 'Siemens Energy Global GmbH & Co. KG','Skyborn Renewables offshore solutions GmbH',
 'Stiftung der deutschen Wirtschaft für die Nutzung und Erforschung der Windenergie auf See (Offshore-Stiftung)',
 'Tennet TSO GmbH','TotalEnergies Renewables Deutschland GmbH','Transnet BW GmbH','Vattenfall GmbH',
 'VDMA e.V.','Vereinigung der Fernleitungsnetzbetreiber Gas e.V. (FNB Gas e.V.)','Vestas Deutschland',
 'VKU - Verband kommunaler Unternehmen e.V.','WAB e.V.','Waterekke Energy GmbH & Co. KG','WWF Deutschland',
]
wind = by_id['bmwe-data-b804866832cc01a3']
withheld = {7,27,29,31,42}
for n,name in enumerate(wind_names,1):
    packages.append({'id':f'bmwe-windsee-202608-{n:03d}','author':name,'process':'WindSeeG August 2026 Länder- und Verbändeanhörung','dataset_url':wind['dataset_url'],'participant_list_file':wind['local_file'],'participant_number':n,'ministry_publication_status':'withheld_by_author' if n in withheld else 'publicly_represented','source_components':[],'ministry_reported_submission_interval':{'start':'2026-08-10','end':'2026-08-17'},'submission_date':None,'window_state':'within_window_by_ministry_reported_consultation_interval','depth':'metadata_only','screened_substantively':False})
wind_packages = {p['participant_number']:p for p in packages}
rows = json.loads((R/'sources/bmwe-datasets/bmwe-data-2f8a69c59529b8ce-Datensatz.json').read_text())
# Row-to-participant linkage checked against the actual organization names, not the numeric placeholder values.
row_map = [37,1,21,28,3,4,36,23,16,12,25,9,10,33,2,17,41,26,5,40,15,14,13,39,8,34,30,19,38,43,32,20,24,22]
assert len(rows)-1 == len(row_map) == 34
for excel_row,n in enumerate(row_map,2):
    row = rows[excel_row-1]
    wind_packages[n]['source_components'].append({'kind':'structured_response','file':by_id['bmwe-data-2f8a69c59529b8ce']['local_file'],'sheet':'Datensatz','row':excel_row,'source_organization_label':row[1],'registration_number_as_supplied':row[3],'read_depth':'metadata_only'})
pdf_map = {'Stellungnahme_BWO.pdf':8,'Stellungnahme_DBV.pdf':11,'Stellungnahme_German Zero e.V..pdf':18,'Stellungnahme_Hamburg BWAI.pdf':6,'Stellungnahme_UENB_Transnet BW GmbH.pdf':35,'Ergänzende Stellungnahme_SH Ministerium Energiewende, Klimaschutz, Umwelt und Natur.pdf':22}
for x in members:
    if x['dataset_url'] != wind['dataset_url']:
        continue
    n = pdf_map[x['member_name']]
    wind_packages[n]['source_components'].append({'kind':'pdf_response_or_supplement','file':x['local_file'],'archive_file':x['archive_file'],'member_name':x['member_name'],'sha256':x['sha256'],'read_depth':'metadata_only'})
assert sum(p['ministry_publication_status']=='publicly_represented' for p in packages)==38
assert all(p['source_components'] for p in packages if p['ministry_publication_status']=='publicly_represented')

# Other response bundles preserve file-level authors as primary filenames until inspected.
other_groups = [
 ('KLtgV','bmwe-data-929dbaf7ccee9afe',13,2,{'start':'2026-07-08','end':'2026-08-10'}),
 ('Wirtschaftsprüferexamen','bmwe-data-735472d7503f22b1',3,0,{'start':'2026-09-23','end':'2026-10-14'}),
 ('Übertragungsnetzkosten 2027–2029','bmwe-data-428ca8ab03ba76e2',24,1,{'start':'2026-08-05','end':'2026-08-13'}),
]
group_summaries = []
for name,list_id,total,private,period in other_groups:
    s = by_id[list_id]
    docs = [x for x in members if x['dataset_url']==s['dataset_url']]
    group_summaries.append({'process':name,'dataset_url':s['dataset_url'],'participant_list_file':s['local_file'],'named_participants':total,'explicitly_withheld':private,'public_pdf_files':len(docs),'ministry_reported_interval':period,'date_limit':'Interval is contextual, not a hard individual date gate. Wirtschaftsprüferexamen includes a19October late response although portal interval ends14October.','response_files':[{'id':x['id'],'file':x['local_file'],'member_name':x['member_name'],'date_candidates':x['date_candidates'],'depth':'metadata_only','submission_date_verified':False}for x in docs]})

out = {'scope':'Observed official BMWE datasets. A participant package may contain a structured response and PDF supplement, which are not automatically two authors.','windsee_packages':packages,'other_current_dataset_summaries':group_summaries,'all_observed_bundle_members_file':'research/round3-energy/coverage-bmwe-bundle-members.json','publication_limits':['Withheld means not published in that ministry dataset; a register/author mirror may exist separately.','Public responses are collected metadata, not fact-checked content.','EEG/Netz July dataset members remain in the full member inventory; later register re-deliveries are assessed separately.','Some participants marked as PDF plus structured have only their structured submission in the published ZIP. The organization is represented, but every supplemental PDF is not demonstrably available.'],'counts':{'windsee_named_packages':43,'windsee_publicly_represented':38,'windsee_withheld':5,'windsee_structured_rows':34,'windsee_public_pdf_members':6}}
(R/'coverage-bmwe-published-responses.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(out['counts']))
