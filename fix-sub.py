#!/usr/bin/env python3

import fileinput
import re
import sys

chars = "-+=()0123456789im"
subtr = "₋₊₌₍₎₀₁₂₃₄₅₆₇₈₉ᵢₘ"
suptr = "⁻⁺⁼⁽⁾⁰¹²³⁴⁵⁶⁷⁸⁹ⁱᵐ"

blockcode = re.compile(r"^(~~~~*) *(\w+)$")
inlinecode = re.compile(r"(?:^|(?<=[^\\]))`")
sub = re.compile(r"(?:<sub>([" + chars + r"]+)</sub>|(?<=\w)_([" + chars + r"]))")
sup = re.compile(r"(?:<sup>([" + chars + r"]+)</sup>|(?<=\w)\^([" + chars + r"]))")

def warn(msg, **kwargs):
    print(msg, file=sys.stderr, **kwargs)

def code_off(code, linenum):
    if code:
        warn(f"Warning: Unterminated inline code block detected on line {linenum}.")
    return False

def tr_once(line, pattern, target):
    result = ""
    lastend = 0
    for m in pattern.finditer(line):
        result += line[lastend:m.start()]
        for c in (m[1] or m[2]):
            i = chars.find(c)
            result += target[i]
        lastend = m.end()
    result += line[lastend:]
    return result

def tr(line):
    line = line.replace("\\*", "·").replace("\\+", "⊕").replace("...", "…")
    line = tr_once(line, sub, subtr)
    line = tr_once(line, sup, suptr)
    return line.replace("\\_", "_")

def trcode(line, code):
    result = ""
    lastend = 0
    for m in inlinecode.finditer(line):
        span = line[lastend:m.start()]
        if code:
            span = tr(span)

        code = not code
        result += span + "`"
        lastend = m.end()

    result += tr(line[lastend:]) if code else line[lastend:]
    return (result, code)

linenum = 0
blockend = None
code = False
pseudocode = False
for line in fileinput.input():
    linenum += 1
    if blockend is None:
        m = blockcode.match(line)
        if m:
            code = code_off(code, linenum)
            blockend = m[1]
            pseudocode = m[2] == "pseudocode"
        elif line.strip() == "":
            code = code_off(code, linenum)
        else:
            (line, code) = trcode(line, code)
    elif line.startswith(blockend):
        blockend = None
    elif pseudocode:
        line = tr(line)

    print(line, end="")
