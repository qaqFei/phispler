import json
from sys import argv

import librosa

if len(argv) < 3:
    print("Usage: tool-sound2phi-fre <soundFile> <outputFile>")
    raise SystemExit

data, sr = librosa.load(argv[1], sr=None)

def add(t: float):
    result["judgeLineList"][0]["notesAbove"].append({
        "type": 1,
        "time": t,
        "holdTime": 0.0,
        "positionX": 0.0,
        "speed": 1.0,
        "floorPosition": 2.2 * t
    })

result = {
    "formatVersion": 3,
    "offset": 0.0,
    "judgeLineList": [
        {
            "bpm": 1.875,
            "notesAbove": [],
            "notesBelow": [],
            "speedEvents": [
                {
                    "startTime": 0.0,
                    "value": 2.2,
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
        }
    ]
}

def getrangefre(start: float, end: float):
    start = max(start, 0.0)
    end = min(end, length)
    
    count = 0
    last = 0.0
    for i in range(int(start * sr), int(end * sr)):
        try: v = data[i]
        except IndexError: pass
        
        if (last <= 0.0 and v >= 0.0) or (last >= 0.0 and v <= 0.0):
            count += 1
            
        last = v
    return (count if count != 0 else 1) / (end - start) / 2

splitt = 0.05
fretange = splitt / 2
length = len(data) / sr
t = 0.0
dts = [((t := i * splitt), 1 / getrangefre(t - fretange, t + fretange)) for i in range(int(length / splitt))]

for i, (t, dt) in enumerate(dts):
    if i == len(dts) - 1: break
    nowt = t
    et, ndt = dts[i + 1]
    
    while nowt < et:
        add(nowt)
        nowt += (nowt - t) / splitt * (ndt - dt) + dt

with open(argv[2], "w", encoding="utf-8") as f:
    json.dump(result, f)
