#!/usr/bin/env python3

import fileinput
import re

chars = "-+=()0123456789im"
subtr = "₋₊₌₍₎₀₁₂₃₄₅₆₇₈₉ᵢₘ"
suptr = "⁻⁺⁼⁽⁾⁰¹²³⁴⁵⁶⁷⁸⁹ⁱᵐ"

pseudocode = re.compile(r"^(~~~~*) *pseudocode$")
inlinecode = re.compile(r"(?:^|(?<=[^\\]))`")
sub = re.compile(r"(?:<sub>([" + chars + r"]+)</sub>|(?<=\w)_([" + chars + r"]))")
sup = re.compile(r"(?:<sup>([" + chars + r"]+)</sup>|(?<=\w)\^([" + chars + r"]))")

def tr(line, pattern, target):
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

def trcode(line, code):
    result = ""
    lastend = 0
    for m in inlinecode.finditer(line):
        span = line[lastend:m.start()]
        if code:
            span = tr(span, sub, subtr)
            span = tr(span, sup, subtr)

        code = not code
        result += span + "`"
        lastend = m.end()

    result += line[lastend:]
    return (result, code)

end = None
code = False
for line in fileinput.input():
    if end is None:
        m = pseudocode.match(line)
        if m:
            end = m[1]
        elif line == "":
            code = False
        else:
            (line, code) = trcode(line, code)
    else:
        if line.strip() != end:
            line = tr(line, sub, subtr)
            line = tr(line, sup, suptr)
        else:
            end = None

    print(line, end="")
