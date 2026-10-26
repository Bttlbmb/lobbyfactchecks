# Renders one evidence page per finding into evidence/<id>.html from data/*.json (read only).
import json, html, re, sys, datetime as dt
from pathlib import Path
from labels import law_label, author_label, headline
from text import tidy
from dates import submission_date

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "evidence"
F = json.load(open(ROOT / "data" / "findings.json", encoding="utf-8"))
DOCS = {x["id"]: x for x in json.load(open(ROOT / "data" / "documents.json", encoding="utf-8"))}
R = {x["id"]: x for x in json.load(open(ROOT / "data" / "source-registry.json", encoding="utf-8"))}
CSS = (HERE / "evidence.css").read_text(encoding="utf-8")

raw = html.escape                        # for URLs, ids and verbatim quotes: never repaired
e = lambda s: html.escape(tidy(s))      # for the project's own prose
def fmt(s):
    if not s: return ""
    x = dt.date.fromisoformat(str(s)[:10]); return f"{x.day} {x.strftime('%B %Y')}"
FAV = {True: "Favours the author’s request", False: "Works against the author’s request", None: "Direction unclear"}

def loc(l):
    if not l: return ""
    p = []
    if l.get("pdf_page"):
        pp = f"PDF page {l['pdf_page']}"
        if l.get("printed_page") and l["printed_page"] != l["pdf_page"]: pp += f" (printed {l['printed_page']})"
        p.append(pp)
    for k in ("table", "section", "paragraph", "row", "column"):
        if l.get(k): p.append(str(l[k]))
    return "\u00a0· ".join(p)

def link(src, label):
    u = (src or {}).get("url") or (src or {}).get("mirror_url")
    return f'<a href="{raw(u)}">{label} ↗</a>' if u else ""

def human(s):
    s = str(s or "").strip()
    return s.replace("_", " ").capitalize() if "_" in s and " " not in s else s

def nest(t, de=False):
    """Inner quotation marks become single marks so the outer marks stay unambiguous."""
    close = "‘" if de else "’"           # German single quotes close with ‘, English with ’
    t = re.sub(r'(?<=\S)"', close, t).replace('"', "‚" if de else "‘")
    t = t.replace("„", "‚")
    return t.replace("“", close if de else "‘").replace("”", close if de else "’")

def quote(q, kind, mark=None):
    lang = q.get("language", "de")
    op, cl = ("„", "“") if lang == "de" else ("“", "”")
    de = lang == "de"
    txt = nest(q.get("original", ""), de).strip()     # verbatim: escaped but never spacing-repaired
    t = raw(txt)
    mk = raw(nest(mark, de)) if mark else ""
    if mk and mk in t: t = t.replace(mk, f"<mark>{mk}</mark>", 1)
    h = f'<blockquote class="q {kind}" lang="{e(lang)}"><p class="qo">{op}{t}{cl}</p>'
    tr = q.get("translation_en")
    if tr and lang != "en":
        m = re.match(r"^(Translation[^:]*):\s*(.*)$", tr.strip(), flags=re.S)
        label, body = (m.group(1) + ":", m.group(2)) if m else ("Translation:", tr.strip())
        if label in ("Translation:", "Translation of fragment:"): label = "English:"   # the plain case; other labels name what was translated
        h += f'<p class="qt">{e(label)} “{e(nest(body))}”</p>'
    return h + "</blockquote>"

def where(q):
    t = loc(q.get("locator"))
    if q.get("retrieved_at"): t += ("\u00a0· " if t else "") + "retrieved " + fmt(q["retrieved_at"])
    return f'<p class="wh">{e(t)}</p>' if t else ""

def qblock(q, kind, mark=None):
    return f'<div class="qb {kind}">{quote(q, kind, mark)}{where(q)}</div>'

def lk(src, label):
    l = link(src, label)
    return f'<p class="lk">{l}</p>' if l else ""

def details(title, body, open_=False):
    return f'<details class="dd"{" open" if open_ else ""}><summary>{e(title)}</summary><div>{body}</div></details>'

def page(i):
    sid = i["submission_source_id"]; sub = R.get(sid, {})
    law = law_label(i["law_id"]); author, kind = author_label(sid, sub.get("title", ""))
    c = i["card"]; cq = i["claim_quote"]; rq = i.get("counter_quote") or {}; d = i.get("draft") or {}
    ctr = R.get(rq.get("source_id"), {})
    sev = i["severity"]; sevtxt = "Major error" if sev == "major" else "Minor error"
    found = fmt(i["history"][0]["date"]) if i.get("history") else ""
    date = ""
    sdate = submission_date(i, DOCS)
    if sdate: date = "submitted " + fmt(sdate)
    elif d.get("hearing_date"): date = "hearing " + fmt(d["hearing_date"])
    role = kind if kind and kind != "individual expert" else ""      # "individual expert" is already in the headline
    byline = "\u00a0· ".join(x for x in (role, date, "found " + found) if x)
    resp = i.get("author_response") or []
    secs = []
    # 1 submission
    secs.append(("Their wording", qblock(cq, "claim", cq.get("underline")) + lk(sub, "Open the original submission")))
    # 2 source
    s2 = (f'<p class="srct">{e(ctr.get("title", ""))}</p>' if ctr.get("title") else "") + qblock(rq, "source") + lk(ctr, "Open the source")
    a = i.get("additional_counter_quote")
    if a:
        at = R.get(a.get("source_id"), {})
        s2 += (f'<p class="srct">{e(at.get("title", ""))}</p>' if at.get("title") else "") + qblock(a, "source") + lk(at, "Open the source")
    calc = i.get("calculation")
    if calc and calc.get("expression"):
        s2 += f'<p class="calc"><b>Calculation</b> {e(calc["expression"])}' + (f' = {e(calc["result_percent"])}%' if calc.get("result_percent") is not None else "") + "</p>"
        if calc.get("scope"): s2 += f'<p class="sn">{e(calc["scope"])}</p>'
    secs.append(("The source’s wording", s2))
    if i.get("correction"): secs.append(("Correction in detail", f'<p class="lead">{e(i["correction"])}</p>'))
    lim = ""
    if i.get("limits"): lim += f'<p>{e(i["limits"])}</p>'
    if i.get("materiality_explanation"): lim += f'<p class="sn">{e(i["materiality_explanation"])}</p>'
    if lim: secs.append(("What this does not show", lim))
    # how we checked
    revs = i.get("review", {}).get("ai_reviews") or []
    rv = "".join(f'<li><b>{e(fmt(r.get("date")))}</b> Independent AI review: {e(human(r.get("assessment") or r.get("outcome") or "reviewed"))}</li>' for r in revs)
    cf = i.get("confidence") or {}
    conf = f'Match between text and source: {e(human(cf.get("text_source_mismatch", "n/a")))}. Seriousness: {e(human(cf.get("materiality", "n/a")))}.'
    reviews = f'<ul class="tl">{rv}</ul><p class="sn">{conf}' + "</p>"
    if resp: reviews += '<ul class="tl">' + "".join("<li>" + e("; ".join(str(v) for v in (r.values() if isinstance(r, dict) else [r]))) + "</li>" for r in resp) + "</ul>"
    ver = d.get("version") or ("Version of " + fmt(d.get("version_date")) + (" " + d["version_time"] if d.get("version_time") else "") if d.get("version_date") else "")
    draft = (f'<p><b>{e(d["title"])}</b></p>' if d.get("title") else "") + (f'<p class="sn">{e(ver)}</p>' if ver else "") \
        + (f'<p class="sn">{e(d["process_status_at_screen"])}</p>' if d.get("process_status_at_screen") else "") \
        + (f'<p class="sn">{e(d["comparison"])}</p>' if d.get("comparison") else "") \
        + (f'<p class="sn">{e(d["submission_date_note"])}</p>' if d.get("submission_date_note") else "")
    ctx = i.get("context_checked") or []
    if isinstance(ctx, str): ctx = [ctx]
    hist = "".join(f'<li><b>{e(fmt(h.get("date")))}</b> {e(h.get("event", ""))}</li>' for h in i.get("history", []))
    srcs = ""
    for sid2 in i.get("source_ids", []):
        s = R.get(sid2)
        if not s: continue
        note = s.get("access_note") or s.get("access") or s.get("provenance_note") or ""
        name = e(s.get("title", sid2)); u = s.get("url") or s.get("mirror_url")
        srcs += "<li>" + (f'<a href="{raw(u)}">{name} ↗</a>' if u else name) + (f'<span class="sn">{e(note)}</span>' if note else "") + "</li>"
    chk = (details("Draft compared", draft or "<p class='sn'>No draft details recorded.</p>")
           + details("Reviews and confidence", reviews)
           + (details("What we read around the claim", '<ul class="ctx">' + "".join(f"<li>{e(x)}</li>" for x in ctx) + "</ul>") if ctx else "")
           + details("History", f'<ul class="tl">{hist}</ul>')
           + details("Sources", f'<ul class="srcl">{srcs}</ul>'))
    secs.append(("How we checked", chk))
    body = "".join(f'<section class="sec"><h2 class="h">{e(t)}</h2>{b}</section>' for t, b in secs)
    rows = (f'<p class="lawlabel in-short">In short</p><dl class="rows"><div class="r"><dt>They want</dt><dd>{e(c["they_want"])}</dd></div>'
            f'<div class="r said"><dt>They said</dt><dd>{e(c["they_claim"])}</dd></div>'
            f'<div class="r real"><dt>The source says</dt><dd>{e(c["the_problem"])}</dd></div>'
            f'<div class="r"><dt>What it changes</dt><dd>{e(i["effect"])}</dd></div></dl>')
    claim = c["they_claim"].strip()
    if len(claim) > 90: claim = claim[:90].rsplit(" ", 1)[0] + "…"
    title = f"{headline(author, kind)} on {law}: {claim}"      # headline first: that is the part a tab still shows
    return f'''<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="../favicon.svg" type="image/svg+xml">
<title>{e(title)} · Lobby Fact Checks</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Newsreader:opsz,wght@6..72,400;6..72,600&display=swap" rel="stylesheet">
<style>{CSS}</style></head><body><div class="pg">
<header class="hd"><div class="hd-in"><a href="../index.html" class="serif" style="font-size:20px;font-weight:600;gap:10px"><svg width="26" height="20" viewBox="6 12 52 40" aria-hidden="true"><path d="M10 16h18v18H18l-8 14z" fill="#14181F"/><path d="M36 16h18v18H44l-8 14z" fill="#A84A00"/></svg>Lobby Fact Checks</a><nav aria-label="Main"><a href="../about.html">About &amp; data</a></nav></div></header>
<main class="col">
<p class="crumb"><a href="../index.html#{raw(i["id"])}">← All findings</a></p>
<p class="eyebrow"><span class="sevtag {sev}">{sevtxt}</span> {e(FAV[i["favours_author_request"]])}</p>
<p class="lawlabel">{e(law)}</p>
<h1 class="serif">{e(headline(author, kind))}</h1>
<p class="standfirst">{e(c["law_is_about"])}</p>
<p class="byline">{e(byline)}</p>
{rows}{body}
<p class="end"><a href="../index.html#{raw(i["id"])}">← Back to all findings</a></p>
<footer><p>Provisional AI-screened finding {e(i["id"])}. No human specialist confirmation is recorded.</p><p><a href="../about.html">Method, limitations and research data</a></p></footer>
</main></div></body></html>'''

OUT.mkdir(parents=True, exist_ok=True)
for i in F:
    (OUT / f'{i["id"]}.html').write_text(page(i), encoding="utf-8")
print(len(F), "evidence pages written to", OUT)
