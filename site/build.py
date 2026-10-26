# Renders the front page from data/findings.json (read only) into index.html.
import json, html, sys, collections, datetime as dt
from pathlib import Path
from labels import law_label, author_label, headline
from text import tidy
from dates import submission_date
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
F = json.load(open(ROOT / "data" / "findings.json", encoding="utf-8"))
R = {x["id"]: x for x in json.load(open(ROOT / "data" / "source-registry.json", encoding="utf-8"))}
DOCS = {x["id"]: x for x in json.load(open(ROOT / "data" / "documents.json", encoding="utf-8"))}
OUT = sys.argv[1] if len(sys.argv) > 1 else str(HERE / "index.html")
TEMPLATE = sys.argv[2] if len(sys.argv) > 2 else str(HERE / "template.html")

SIBLINGS = collections.Counter(i["submission_source_id"] for i in F)   # findings per statement, minor ones included
def d(s): return dt.date.fromisoformat(s) if s else None
rows=[]
for i in F:
    found=d(i["history"][0]["date"])
    sd=d(submission_date(i,DOCS)); hd=d(i["draft"].get("hearing_date"))
    a=author_label(i["submission_source_id"],R.get(i["submission_source_id"],{}).get("title",""))
    rows.append(dict(id=i["id"],sid=i["submission_source_id"],found=found,sd=sd,hd=hd,sev=i["severity"],fav=i["favours_author_request"],
        law=law_label(i["law_id"]),author=a[0],kind=a[1],claim=i["card"]["they_claim"],
        problem=i["card"]["the_problem"],effect=i["effect"],wants=i["card"]["they_want"],about=i["card"]["law_is_about"]))
# sections: newest date first, where the date is the submission date or, failing that, the hearing date;
# findings with neither come last.
# Within a section major errors first, then the most recently found.
rows.sort(key=lambda r:(1 if r["sev"]=="major" else 0,r["found"]),reverse=True)

fmt=lambda x:f"{x.day} {x.strftime('%B %Y')}"
raw=html.escape                         # for URLs and ids: never repaired
e=lambda s: html.escape(tidy(s))      # for the project's own prose
n_major=sum(r["sev"]=="major" for r in rows); n_fav=sum(r["fav"] is True for r in rows)
n_maj_fav=sum(r["sev"]=="major" and r["fav"] is True for r in rows)
n_sub=len({i["submission_source_id"] for i in F}); n_law=len({i["law_id"] for i in F})
FAV={True:"Favours the author’s request",False:"Works against the author’s request",None:"Direction unclear"}
def row(r):
    tags=[]
    if r["sev"]!="major": tags.append(("Minor error"," sev"))
    if r["fav"] is False: tags.append(("Works against the author’s request",""))
    if r["fav"] is None: tags.append(("Direction unclear",""))
    tag="".join(f'<span class="tag{c}">{e(t)}</span>' for t,c in tags)
    date=""   # the section heading already gives the date (submission or hearing)
    auth=e(r["author"])+(f", {e(r['kind'])}" if r["kind"] else "")
    sib=f'<span class="by sib">One of {SIBLINGS[r["sid"]]} findings in this statement</span>' if SIBLINGS[r["sid"]]>1 else ""
    role=f'<p class="role">{e(r["kind"][:1].upper()+r["kind"][1:])}</p>' if r["kind"] and r["kind"]!="individual expert" else ""   # "individual expert" is already in the headline
    by=sib+(f'<span class="by">{e(date)}</span>' if date else "")
    link=f'<a class="more" href="evidence/{raw(r["id"])}.html">Open the evidence<span class="vh"> for {e(r["law"])}, {auth}</span>&nbsp;→</a>'
    hid=" hidden" if r["sev"]!="major" else ""   # matches the default view without JavaScript
    return f'''<article class="rc" id="{raw(r['id'])}" data-sev="{r['sev']}" data-fav="{str(r['fav']).lower()}"{hid}>
<header class="fhead"><p class="lawlabel">{e(r['law'])}</p><h3 class="fh">{e(headline(r['author'],r['kind']))}</h3>{role}</header>
<div class="meta">{tag}<p class="about">{e(r['about'])}</p>{by}{link}</div>
<dl class="rows">
<div class="r"><dt>They want</dt><dd>{e(r['wants'])}</dd></div>
<div class="r said"><dt>They said</dt><dd>{e(r['claim'])}</dd></div>
<div class="r real"><dt>The source says</dt><dd>{e(r['problem'])}</dd></div>
<div class="r eff"><dt>What it changes</dt><dd>{e(r['effect'])}</dd></div>
</dl>
</article>'''

groups={}
for r in rows: groups.setdefault(("Submitted",r["sd"]) if r["sd"] else ("Hearing",r["hd"]) if r["hd"] else None,[]).append(r)
order=sorted([k for k in groups if k],key=lambda k:(k[1],k[0]=="Submitted"),reverse=True)+([None] if None in groups else [])
body=""
for day in order:
    rs=groups[day]
    nm=sum(r["sev"]=="major" for r in rs)
    title=(fmt(day[1]) if day[0]=="Submitted" else f"Hearing on {fmt(day[1])}") if day else "No date recorded"   # submission dates are the default, so only hearings are labelled
    body+=f'<section class="day" data-day{"" if nm else " hidden"}><div class="dayhd"><h2 class="h2">{title}</h2><span class="n"{" hidden" if nm==1 else ""}><span data-n>{nm}</span> findings</span></div>'+"".join(row(r) for r in rs)+'</section>'

n_minor=len(rows)-n_major
def filt(f,label,n,pressed=False):
    return f'<button type="button" data-f="{f}" aria-pressed="{str(pressed).lower()}">{label}<span class="n">{n}</span></button>'
# The favour filter only earns its place while it differs from "Major errors".
filters=filt("major","Major errors",n_major,True)+("" if n_maj_fav==n_major else filt("fav","Major, favouring the request",n_maj_fav))+filt("minor","Minor errors",n_minor)
tpl=open(TEMPLATE,encoding="utf-8").read()
out=(tpl.replace("{{FILTERS}}",filters).replace("{{BODY}}",body).replace("{{COUNT}}",f"{n_major} findings").replace("{{NSUB}}",str(n_sub)).replace("{{NLAW}}",str(n_law))
 .replace("{{NALL}}",str(len(rows))).replace("{{NMAJOR}}",str(n_major)).replace("{{NMAJFAV}}",str(n_maj_fav)).replace("{{NFAV}}",str(n_fav))
 .replace("{{SNAP}}",fmt(max(r["found"] for r in rows))))
open(OUT,"w",encoding="utf-8").write(out); print(len(rows),"rows",n_major,"major",len(groups),"days")
