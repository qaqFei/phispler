import json
from copy import deepcopy
from fractions import Fraction
from sys import argv
from threading import Thread

import const

if len(argv) < 3:
    print("Usage: tool-phi2rpe <input> <output>")
    raise SystemExit

with open(argv[1], "r", encoding="utf-8") as f:
    phic = json.load(f)

def n2f(x: float):
    x *= 0.03125
    fra = Fraction(x % 1.0).limit_denominator((2 << 30) - 1)
    return [int(x), fra.numerator, fra.denominator]

def f2n(x: list):
    return (x[0] + x[1] / x[2]) / 0.03125

def optimize_events(es: list[dict], x: float):
    for e in es:
        if f2n(e["startTime"]) >= x:
            es.remove(e)

bpms = [i["bpm"] for i in phic["judgeLineList"]]
rpeop = {
    "BPMList": [
        {
            "bpm": (sum(bpms) / len(bpms)) if bpms else 120.0,
            "startTime": [0, 0, 1]
        }
    ],
    "META": {
        "RPEVersion": 140, "background": "",
        "charter": "", "composer": "",
        "id": "", "level": "",
        "name": "", "offset": int(phic["offset"] * 1000), "song": ""
    },
    "judgeLineGroup": ["Default"],
    "judgeLineList": [],
    "multiLineString": "",
    "multiScale": 1.0
}

def unpack_pos(number: int) -> tuple[int, int]:
    return (number - number % 1000) // 1000, number % 1000

def transform_line(line: dict):
    rpel = {
        "Group": 0,
        "Name": "Untitled",
        "Texture": "line.png",
        "bpmfactor": rpeop["BPMList"][0]["bpm"] / line["bpm"],
        "father": -1,
        "isCover": 1,
        "zOrder": 0,
        "notes": [],
        "eventLayers": [
            {
                "alphaEvents": [],
                "moveXEvents": [],
                "moveYEvents": [],
                "rotateEvents": [],
                "speedEvents": []
            },
            *((None, ) * 4)
        ],
        "alphaControl": [{"alpha": 1.0, "easing": 1, "x": 0.0}, {"alpha": 1.0, "easing": 1, "x": 9999999.0}],
        "extended": {"inclineEvents": [{"bezier": 0, "bezierPoints": [0.0, 0.0, 0.0, 0.0], "easingLeft": 0.0, "easingRight": 1.0, "easingType": 0, "end": 0.0, "endTime": [1, 0, 1], "linkgroup": 0, "start": 0.0, "startTime": [0, 0, 1]}]},
        "posControl": [{"easing": 1, "pos": 1.0, "x": 0.0}, {"easing": 1, "pos": 1.0, "x": 9999999.0}],
        "sizeControl": [{"easing": 1, "size": 1.0, "x": 0.0}, {"easing": 1, "size": 1.0, "x": 9999999.0}],
        "skewControl": [{"easing": 1, "skew": 0.0, "x": 0.0}, {"easing": 1, "skew": 0.0, "x": 9999999.0}],
        "yControl": [{"easing": 1, "x": 0.0, "y": 1.0}, {"easing": 1, "x": 9999999.0, "y": 1.0}],
    }
    holds = []
    
    for e in line["speedEvents"]:
        rpel["eventLayers"][0]["speedEvents"].append({
            "linkgroup": 0,
            "startTime": n2f(e["startTime"]),
            "endTime": n2f(e["endTime"]),
            "start": e["value"] * const.PGR_UH * 900 / 120,
            "end": e["value"] * const.PGR_UH * 900 / 120,
        })
    
    for e in line["judgeLineMoveEvents"]:
        if phic["formatVersion"] != 3:
            sp, ep = unpack_pos(e["start"]), unpack_pos(e["end"])
            e["start"] = sp[0] / 880
            e["end"] = ep[0] / 880
            e["start2"] = sp[1] / 520
            e["end2"] = ep[1] / 520
        
        rpel["eventLayers"][0]["moveXEvents"].append({
            "linkgroup": 0,
            "bezier": 0,
            "bezierPoints": [0.0, 0.0, 0.0, 0.0],
            "easingLeft": 0.0,
            "easingRight": 1.0,
            "easingType": 1,
            "startTime": n2f(e["startTime"]),
            "endTime": n2f(e["endTime"]),
            "start": e["start"] * 1350 - 675,
            "end": e["end"] * 1350 - 675,
        })
        
        rpel["eventLayers"][0]["moveYEvents"].append({
            "linkgroup": 0,
            "bezier": 0,
            "bezierPoints": [0.0, 0.0, 0.0, 0.0],
            "easingLeft": 0.0,
            "easingRight": 1.0,
            "easingType": 1,
            "startTime": n2f(e["startTime"]),
            "endTime": n2f(e["endTime"]),
            "start": e["start2"] * 900 - 450,
            "end": e["end2"] * 900 - 450,
        })
    
    for e in line["judgeLineRotateEvents"]:
        rpel["eventLayers"][0]["rotateEvents"].append({
            "linkgroup": 0,
            "bezier": 0,
            "bezierPoints": [0.0, 0.0, 0.0, 0.0],
            "easingLeft": 0.0,
            "easingRight": 1.0,
            "easingType": 1,
            "startTime": n2f(e["startTime"]),
            "endTime": n2f(e["endTime"]),
            "start": -e["start"],
            "end": -e["end"],
        })
    
    for e in line["judgeLineDisappearEvents"]:
        rpel["eventLayers"][0]["alphaEvents"].append({
            "linkgroup": 0,
            "bezier": 0,
            "bezierPoints": [0.0, 0.0, 0.0, 0.0],
            "easingLeft": 0.0,
            "easingRight": 1.0,
            "easingType": 1,
            "startTime": n2f(e["startTime"]),
            "endTime": n2f(e["endTime"]),
            "start": int(e["start"] * 255),
            "end": int(e["end"] * 255),
        })
    
    for n in line["notesAbove"]:
        if n["type"] == 3: 
            holds.append((n, 1))
            continue
            
        rpel["notes"].append({
            "above": 1, "alpha": 255, "isFake": 0, "size": 1.0,
            "visibleTime": 999999.0, "yOffset": 0.0,
            
            "type": {1:1, 2:4, 3:2, 4:3}[n["type"]],
            "startTime": n2f(n["time"]),
            "endTime": n2f(n["time"] + n["holdTime"]),
            "positionX": n["positionX"] * const.PGR_UW * 1350,
            "speed": n["speed"]
        })
        
    for n in line["notesBelow"]:
        if n["type"] == 3: 
            holds.append((n, 0))
            continue
            
        rpel["notes"].append({
            "above": 0, "alpha": 255, "isFake": 0, "size": 1.0,
            "visibleTime": 999999.0, "yOffset": 0.0,
            
            "type": {1:1, 2:4, 3:2, 4:3}[n["type"]],
            "startTime": n2f(n["time"]),
            "endTime": n2f(n["time"] + n["holdTime"]),
            "positionX": n["positionX"] * const.PGR_UW * 1350,
            "speed": n["speed"]
        })
    
    for n, above in holds:
        fel, fer = n["time"], n["time"] + n["holdTime"]
        sevs = []
        for e in rpel["eventLayers"][0]["speedEvents"]:
            etl, etr = f2n(e["startTime"]), f2n(e["endTime"])
            if (
                fel <= etl <= etr <= fer
                or fel <= etl <= fer <= etr
                or etl <= fel <= fer <= etr
                or etl <= fel <= etr <= fer
            ):
                sevs.append(e["start"]) # start == end
                
        if len(set(sevs)) <= 1:
            rpel["notes"].append({
                "above": above, "alpha": 255, "isFake": 0, "size": 1.0,
                "visibleTime": 999999.0, "yOffset": 0.0,
                
                "type": 2,
                "startTime": n2f(n["time"]),
                "endTime": n2f(n["time"] + n["holdTime"]),
                "positionX": n["positionX"] * const.PGR_UW * 1350,
                "speed": ((n["speed"] / (sevs[0] * 120 / 900 / const.PGR_UH)) if sevs and sevs[0] != 0.0 else 1.0)
            })
        else:
            hnl = deepcopy(rpel)
            
            ses = hnl["eventLayers"][0]["speedEvents"]
            for e in ses:
                e_st, e_et = f2n(e["startTime"]), f2n(e["endTime"])
                n_st, n_et = n["time"], n["time"] + n["holdTime"]
                
                if n_st <= e_st <= n_et <= e_et:
                    ses.remove(e)
                elif e_st <= n_st <= n_et <= e_et:
                    e["endTime"] = n2f(n_st)
                elif e_st <= n_st <= e_et <= n_et:
                    e["endTime"] = n2f(n_st)
                elif e_st <= e_et <= n_st <= n_et:
                    pass
                elif n_st <= n_et <= e_st <= e_et:
                    ses.remove(e)
                
            hnl["notes"].clear()
            hnl["eventLayers"][0]["alphaEvents"].clear()
            hnl["eventLayers"][0]["alphaEvents"].append({
                "linkgroup": 0, "bezier": 0,
                "bezierPoints": [0.0, 0.0, 0.0, 0.0], "easingLeft": 0.0,
                "easingRight": 1.0, "easingType": 1,
                "startTime": [0, 0, 1], "endTime": [1, 0, 1],
                "start": 0, "end": 0,
            })
            hnl["eventLayers"][0]["speedEvents"].append({
                "linkgroup": 0,
                "startTime": n2f(n["time"]),
                "endTime": n2f(n["time"] + n["holdTime"]),
                "start": n["speed"] * const.PGR_UH * 900 / 120,
                "end": n["speed"] * const.PGR_UH * 900 / 120,
            })
            hnl["notes"].append({
                "above": above, "alpha": 255, "isFake": 0, "size": 1.0,
                "visibleTime": 999999.0, "yOffset": 0.0,
                
                "type": 2,
                "startTime": n2f(n["time"]),
                "endTime": n2f(n["time"] + n["holdTime"]),
                "positionX": n["positionX"] * const.PGR_UW * 1350,
                "speed": 1.0
            })
            
            optimize_events(hnl["eventLayers"][0]["moveXEvents"], n["time"] + n["holdTime"])
            optimize_events(hnl["eventLayers"][0]["moveYEvents"], n["time"] + n["holdTime"])
            optimize_events(hnl["eventLayers"][0]["rotateEvents"], n["time"] + n["holdTime"])
            optimize_events(hnl["eventLayers"][0]["alphaEvents"], n["time"] + n["holdTime"])
            rpeop["judgeLineList"].append(hnl)
    
    rpeop["judgeLineList"].append(rpel)

ts: list[Thread] = []
for line in phic["judgeLineList"]:
    ts.append(Thread(target=transform_line, args=(line, ), daemon=True))
    ts[-1].start()
(*(map(lambda x: x.join(), ts)), )

json.dump(rpeop, open(argv[2], "w", encoding="utf-8"), ensure_ascii=False)
