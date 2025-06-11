import json
import math
from sys import argv

import librosa

import const

if len(argv) < 3:
    print("Usage: tool-sound2phi <soundFile> <outputFile>")
    raise SystemExit

data, sr = librosa.load(argv[1], sr=None)

def pcs():
    lv = 0.0
    for i, v in enumerate(data):
        if (v > 0.0 and lv < 0.0) or (v < 0.0 and lv > 0.0):
            t = i / sr
            yield (
                t,
                (math.sin(
                    t * 0.2
                ) + 1.0) / 2 * 0.8 - 0.4
            )
            
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
