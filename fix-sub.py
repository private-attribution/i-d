#!/usr/bin/env python3

import fileinput
import re

chars = "-+=()0123456789i"
subtr = "₋₊₌₍₎₀₁₂₃₄₅₆₇₈₉ᵢ"
suptr = "⁻⁺⁼⁽⁾⁰¹²³⁴⁵⁶⁷⁸⁹ⁱ"

pseudocode = re.compile(r"^(~~~~*) *pseudocode$")
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
