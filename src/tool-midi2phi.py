import json
from sys import argv

import const
import midi_parse

if len(argv) < 3:
    print("Usage: tool-midi2phi <midiFile> <outputFile>")
    raise SystemExit

mid = midi_parse.MidiFile(open(argv[1], "rb").read())

def pcs():
    onmsgs = [(msg["sec_time"], msg["note"]) for track in mid.tracks for msg in track if msg["type"] == "note_on"]
    
    onmsgs.sort(key = lambda x: x[0])
    min_note, max_note = min(onmsgs, key=lambda x: x[1])[1], max(onmsgs, key=lambda x: x[1])[1]
    
    last = (float("nan"), float("nan"))
    for t, n in onmsgs:
        r = t, (n + 1 - (max_note - min_note) / 2 - min_note) / (max_note - min_note) / const.PGR_UW * 0.8
        if r != last:
            yield r
        last = r

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
                    "positionX": x,
                    "speed": 1.0,
                    "floorPosition": 2.2 * t
                }
                for t, x in pcs()
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
