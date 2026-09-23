#!/usr/bin/env python3
"""Mechanical AI-flavor and style checks for the paper LaTeX source.

Checks:
1. The repo's list of overused AI words (去AI味 prompt appendix).
2. Em-dash usage (—, ---) which both the repo prompts and the humanizer
   skill flag.
3. not-X-but-Y contrast constructions ("not only ... but also").
4. Inflation adverbs (very, extremely, highly, significantly without
   a statistical qualifier).
5. Contraction usage (it's, don't) forbidden by the polish prompt.
6. \item density in prose sections (allowed only in the contribution
   list and the checklist).
"""
import re
import sys

AI_WORDS = """accentuate amass ameliorate amplify alleviate ascertain
advocate articulate bolster cherish conceptualize conjecture consolidate
convey culminate decipher demonstrate depict devise delineate delve
diverge disseminate elucidate endeavor engage enumerate envision enduring
exacerbate expedite foster galvanize harmonize hone innovate inscription
integrate interpolate intricate lasting leverage manifest mediate nurture
nuance nuanced obscure opt originates perceive perpetuate permeate pivotal
ponder prescribe prevailing profound recapitulate reconcile rectify
rekindle reimagine scrutinize substantiate tailor testament transcend
traverse underscore unveil vibrant""".split()

PATH = sys.argv[1] if len(sys.argv) > 1 else "paper/main.tex"
src = open(PATH).read()

# Strip comments and verbatim/listings
lines = []
for l in src.splitlines():
    if l.lstrip().startswith("%"):
        continue
    lines.append(l)
body = "\n".join(lines)

issues = []

# 1. AI words (case-insensitive, whole word)
for w in AI_WORDS:
    for m in re.finditer(rf"\b{w}(?:d|s|ing)?\b", body, re.I):
        ctx = body[max(0, m.start() - 45):m.end() + 45].replace("\n", " ")
        issues.append(("AI-WORD", m.group(0), ctx))

# 2. Em dashes
for m in re.finditer(r"(---|—|–)", body):
    ctx = body[max(0, m.start() - 40):m.end() + 40].replace("\n", " ")
    if "tabular" not in ctx and "\\hline" not in ctx:
        issues.append(("EMDASH", m.group(0), ctx))

# 3. not only ... but also
for m in re.finditer(r"not only[^.]{0,80}but also", body, re.I):
    issues.append(("NOTONLYBUT", m.group(0)[:60],
                   body[m.start():m.end()][:100]))

# 4. inflation adverbs
for w in ("very", "extremely", "highly", "remarkably", "strikingly"):
    for m in re.finditer(rf"\b{w}\b", body, re.I):
        ctx = body[max(0, m.start() - 45):m.end() + 45].replace("\n", " ")
        issues.append(("INTENSIFIER", m.group(0), ctx))
for m in re.finditer(r"\bsignificantly\b", body, re.I):
    ctx = body[max(0, m.start() - 60):m.end() + 60]
    if not re.search(r"p\s*[<=]|confidence|interval|test", ctx, re.I):
        issues.append(("INTENSIFIER", m.group(0), ctx[:110]))

# 5. contractions
for m in re.finditer(r"\b(it's|don't|doesn't|can't|won't|isn't|aren't"
                     r"|wasn't|weren't|didn't|hasn't|haven't)\b", body, re.I):
    issues.append(("CONTRACTION", m.group(0), ""))

# 6. \item outside contribution/checklist blocks
for m in re.finditer(r"\\item", body):
    line_no = body[:m.start()].count("\n")
    issues.append(("ITEM", "\\item", f"line {line_no + 1}"))

print(f"{len(issues)} findings in {PATH}")
for kind, hit, ctx in issues:
    print(f"  [{kind}] {hit!r} :: {ctx[:100]}")
