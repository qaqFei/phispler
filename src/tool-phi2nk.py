import json
from sys import argv

import const

if len(argv) < 3:
    print("Usage: tool-phi2nk <phiChart> <k> <outputChart>")
    raise SystemExit

with open(argv[1], "r", encoding="utf-8") as f:
    phic = json.load(f)

k = int(float(argv[2]))
pxr = 0.65
pxcs = [(1.0 - pxr) / 2 + pxr * (i / (k - 1)) for i in range(k)]
speed = 2.2

for line in phic["judgeLineList"]:
    line.update({
        "speedEvents": [
            {
                "startTime": 0.0,
                "value": speed,
                "endTime": 999999.0
            }
        ],
        "judgeLineMoveEvents": [
            {
                "startTime": -999999.0,
                "endTime": 999999.0,
                "start": 0.5,
                "end": 0.5,
                "start2": 0.2,
                "end2": 0.2
            }
        ],
        "judgeLineRotateEvents": [
            {
                "startTime": -999999.0,
                "endTime": 999999.0,
                "start": 0.0,
                "end": 0.0
            }
        ],
        "judgeLineDisappearEvents": [
            {
                "startTime": -999999.0,
                "endTime": 999999.0,
                "start": 1.0,
                "end": 1.0
            }
        ]
    })

    line["notesAbove"] += line["notesBelow"]
    line["notesBelow"] = []
    for note in line["notesAbove"]:
        px = note["positionX"]
        
        px *= const.PGR_UW
        px += 0.5
        dpxs = []
        for i in pxcs:
            dpxs.append(abs(px - i))
        px = pxcs[dpxs.index(min(dpxs))]
        px -= 0.5
        px /= const.PGR_UW
        
        note["positionX"] = px
        note["speed"] = speed if note["type"] == 3 else 1.0
        note["floorPosition"] = speed * (note["time"] * (1.875 / line["bpm"]))
    line["notesBelow"].sort(key=lambda note: note["time"])
    
with open(argv[3], "w", encoding="utf-8") as f:
    json.dump(phic, f)
