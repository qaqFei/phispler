import json
import random
from sys import argv

import librosa

import const

if len(argv) < 3:
    print("Usage: tool-autosoundpicking <soundFile> <outputFile> [value=0.3]")
    raise SystemExit

data, sr = librosa.load(argv[1], sr=None)
cv = float(argv[3]) if len(argv) > 3 else 0.3

def pcs():
    lv = 0.0
    lt = -1.0
    for i, v in enumerate(data):
        if i != 0 and v - lv >= cv:
            t = i / sr
            dt = t - lt
            if dt > 0.03:
                match random.randint(1, 3):
                    case 1:
                        yield (t, 0.08)
                    case 2:
                        yield (t, -0.08)
                    case 3:
                        yield (t, 0.20)
                        yield (t, -0.20)
                lt = t
        
        if v > 0:
            lv = v

result = {
    "formatVersion": 3,
    "offset": 0.0,
    "judgeLineList": [
        {
            "bpm": 1.875,
            "notesAbove": [
                {
                    "type": 1,
                    "time": t,
                    "holdTime": 0.0,
                    "positionX": px / const.PGR_UW,
                    "speed": 1.0,
                    "floorPosition": 2.2 * t
                }
                for t, px in pcs()
            ],
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

with open(argv[2], "w", encoding="utf-8") as f:
    json.dump(result, f)
