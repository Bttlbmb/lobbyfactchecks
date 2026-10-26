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
    (re.compile(r"(?<=\d)(?=(?:%s)(?![A-Za-z]))" % "|".join(_MONTHS)), " "),
    (re.compile("(?:" + "|".join(f"(?<={m})" for m in _MONTHS) + r")(?=\d)"), " "),
]

_URL = re.compile(r"(https?://\S+)")

def tidy(s):
    s = str(s if s is not None else "")
    parts = _URL.split(s)                      # odd items are URLs: left exactly as they are
    for n in range(0, len(parts), 2):
        for rx, rep in _RULES:
            parts[n] = rx.sub(rep, parts[n])
    return "".join(parts)
