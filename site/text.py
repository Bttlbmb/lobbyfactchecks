"""Display-layer spacing repair for the project's own prose (never for verbatim quotes or URLs).

The findings text sometimes lacks a space after a comma, colon, semicolon, percent sign or closing
bracket, and around month names ("43%from", "years,creating", "5October 2026"). These rules add the
missing space. They are deliberately conservative; words that were run together ("billBT") are not touched."""
import re

_MONTHS = "January February March April May June July August September October November December".split()
_RULES = [
    (re.compile(r"([,;:])(?=[A-Za-z§])"), r"\1 "),
    (re.compile(r"%(?=[A-Za-z])"), "% "),
    (re.compile(r"\)(?=[A-Za-z§])"), ") "),
    (re.compile(r"(?<=[A-Za-z])([,;:])(?=\d)"), r"\1 "),                                  # "position,25 August"
    (re.compile(r"(?<=[a-z])(?=(?:%s) \d{4})" % "|".join(_MONTHS)), " "),       # "inJuly 2025"
    (re.compile(r"(?<=[a-z])(?=BT ?\d{2}/\d)"), " "),                           # "billBT20/13092"
    (re.compile(r"\b(from|on|at|see)(?=(?:pp?|pages?) ?\d)"), r"\1 "),             # "frompage 5", "onpp 5-6"
    (re.compile(r"(?<=\d)(?=(?:%s)(?![A-Za-z]))" % "|".join(_MONTHS)), " "),
    (re.compile("(?:" + "|".join(f"(?<={m})" for m in _MONTHS) + r")(?=\d)"), " "),
    (re.compile(r"(?<=[a-z])\((?=\d)"), " ("),                                     # "date(28 April"
    (re.compile(r"(\d (?:%s))(?=[a-z])" % "|".join(_MONTHS)), r"\1 "),             # "14 Aprilsubmission"
    (re.compile(r"(?<=\d),(?=\d{1,2} (?:%s) \d{4})" % "|".join(_MONTHS)), ", "),   # "13092,30 September 2025"; after the month rules have split the date
]

_URL = re.compile(r"(https?://\S+)")

def tidy(s):
    s = str(s if s is not None else "")
    parts = _URL.split(s)                      # odd items are URLs: left exactly as they are
    for n in range(0, len(parts), 2):
        for rx, rep in _RULES:
            parts[n] = rx.sub(rep, parts[n])
    return "".join(parts)
