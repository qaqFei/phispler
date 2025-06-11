import json
from sys import argv

import const
import midi_parse

if len(argv) < 3:
    print("Usage: tool-midi2phi-nur <midiFile> <outputFile> [default_note_length=0.1]")
    raise SystemExit

DEFAULT_NOTELENGTH = 0.1 if len(argv) < 4 else float(argv[3])

class MidiNoteBin:
    def __init__(self):
        self.bin: dict[int, tuple[float, int]] = {}
        self.result: list[tuple[float, float, int]] = []
    
    def add(self, msg: dict, t: float):
        msghash = hash((msg["channel"], msg["note"]))
        if msghash in self.bin:
            ont, note = self.bin.pop(msghash)
            self.result.append((ont, ont + DEFAULT_NOTELENGTH, note))

        self.bin[msghash] = (t, msg["note"])
    
    def off(self, msg: dict, t: float):
        msghash = hash((msg["channel"], msg["note"]))
        if msghash not in self.bin: return
        
        ont, note = self.bin.pop(msghash)
        self.result.append((ont, t, note))
    
    def flush(self):
        for ont, note in self.bin.values():
            self.result.append((ont, ont + DEFAULT_NOTELENGTH, note))
        self.bin.clear()

mid = midi_parse.MidiFile(open(argv[1], "rb").read())
notebin = MidiNoteBin()

for track in mid.tracks:
    for msg in track:
        if msg["type"] == "note_on": notebin.add(msg, msg["sec_time"])
        elif msg["type"] == "note_off": notebin.off(msg, msg["sec_time"])

notebin.flush()
notebin.result.sort(key=lambda x: x[0])
min_note, max_note = min(notebin.result, key=lambda x: x[-1])[-1], max(notebin.result, key=lambda x: x[-1])[-1]

def pcs():
    for sec, et, n in notebin.result:
        hz = 440 * (2 ** ((n - 69) / 12))
        dt = 1 / hz
        t = sec
        while t < et:
            yield t, (n + 1 - (max_note - min_note) / 2 - min_note) / (max_note - min_note) / const.PGR_UW * 0.8
            t += dt

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

result["judgeLineList"][0]["notesAbove"].sort(key=lambda x: x["time"])
print(f"length: {result["judgeLineList"][0]["notesAbove"][-1]["time"]} s")

with open(argv[2], "w", encoding="utf-8") as f:
    json.dump(result, f)
