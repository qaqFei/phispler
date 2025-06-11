import noprocessfp_warn as _

import json
from sys import argv

if len(argv) < 5:
    print("Usage: tool-phiChart2onlyOneNote <input> <output> <ntype> <interval>")
    raise SystemExit

def _processNotes(ns: list, bpm: int):
    result = []
    for n in ns:
        if n["type"] != 3:
            n["type"] = int(argv[3])
            result.append(n)
        else:
            n["type"] = int(argv[3])
            n["speed"] = 1.0
            ht = n["holdTime"] * 1.875 / bpm
            dt = 0.0
            while True:
                nn = n.copy()
                nn["holdTime"] = 0.0
                if dt > ht:
                    break
                nn["time"] = n["time"] + dt / (1.875 / bpm)
                dt += float(argv[4])
                result.append(nn)
    return result

chart = json.load(open(argv[1], "r", encoding="utf-8"))
for l in chart["judgeLineList"]:
    l["notesAbove"] = _processNotes(l["notesAbove"], l["bpm"])
    l["notesBelow"] = _processNotes(l["notesBelow"], l["bpm"])

json.dump(chart, open(argv[2], "w", encoding="utf-8"), indent=4, ensure_ascii=False)
