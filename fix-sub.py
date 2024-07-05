#!/usr/bin/env python3

import fileinput
import re

chars = "-+=()0123456789im"
subtr = "₋₊₌₍₎₀₁₂₃₄₅₆₇₈₉ᵢₘ"
suptr = "⁻⁺⁼⁽⁾⁰¹²³⁴⁵⁶⁷⁸⁹ⁱᵐ"

blockcode = re.compile(r"^(~~~~*) *(\w+)$")
inlinecode = re.compile(r"(?:^|(?<=[^\\]))`")
sub = re.compile(r"(?:<sub>([" + chars + r"]+)</sub>|(?<=\w)_([" + chars + r"]))")
sup = re.compile(r"(?:<sup>([" + chars + r"]+)</sup>|(?<=\w)\^([" + chars + r"]))")

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
    result = tr_once(line, sub, subtr)
    return tr_once(result, sup, suptr)

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

    result += line[lastend:]
    return (result, code)

end = None
code = False
pseudocode = False
for line in fileinput.input():
    if end is None:
        m = blockcode.match(line)
        if m:
            end = m[1]
            pseudocode = m[2] == "pseudocode"
        elif line == "":
            code = False
        else:
            (line, code) = trcode(line, code)
    else:
        if line.strip() != end:
            if pseudocode:
                line = tr(line)
        else:
            end = None

    print(line, end="")
