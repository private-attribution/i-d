#!/usr/bin/env python3

import fileinput
import re

pseudocode = re.compile(r"^(~~~~*) *pseudocode$")
sub = re.compile(r"<sub>([^<]+)</sub>")
sup = re.compile(r"<sup>([^<]+)</sup>")
chars = "0123456789+-=()i"
subtr = "₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎ᵢ"
suptr = "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ⁱ"

def tr(line, pattern, target):
    result = ""
    lastend = 0
    for m in pattern.finditer(line):
        result += line[lastend:m.start()]
        for c in m[1]:
            i = chars.find(c)
            result += target[i]
        lastend = m.end()
    result += line[lastend:]
    return result

end = None
code = False
for line in fileinput.input():
    if end is None:
        m = pseudocode.match(line)
        if m:
            end = m[1]
        else:
            # TODO Look for `code` instead
            pass
    else:
        if line.strip() != end:
            line = tr(line, sub, subtr)
            line = tr(line, sup, suptr)
        else:
            end = None

    print(line, end="")
