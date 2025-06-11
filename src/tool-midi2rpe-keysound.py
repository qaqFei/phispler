import json
from fractions import Fraction
from sys import argv

import const
import midi_parse

if len(argv) < 3:
    print("Usage: tool-midi2rpe-keysound <midiFile> <outputFile>")
    raise SystemExit

print("tip: please unzip ./resources/midi2rpe_keysound_res.zip to chart.")
mid = midi_parse.MidiFile(open(argv[1], "rb").read())

def pcs():
    onmsgs = [(msg["sec_time"], msg["note"]) for track in mid.tracks for msg in track if msg["type"] == "note_on"]
    
    onmsgs.sort(key = lambda x: x[0])
    min_note, max_note = min(onmsgs, key=lambda x: x[1])[1], max(onmsgs, key=lambda x: x[1])[1]
    
    last = (float("nan"), float("nan"), -1)
    for t, n in onmsgs:
        r = t, (n + 1 - (max_note - min_note) / 2 - min_note) / (max_note - min_note) * const.RPE_WIDTH * 0.8, n
        if r != last:
            yield r
        last = r

def toFraction(x: float):
    fra = Fraction(x % 1.0).limit_denominator((2 << 30) - 1)
    return [int(x), fra.numerator, fra.denominator]

result = {
    "BPMList": [
        {
            "bpm": 60.0,
            "startTime": [0, 0, 1]
        }
    ],
    "META": {
        "RPEVersion": 140, "background": "",
        "charter": "", "composer": "",
        "id": "", "level": "",
        "name": "", "offset": 0, "song": ""
    },
    "judgeLineGroup": ["Default"],
    "judgeLineList": [{
        "Group": 0,
        "Name": "Untitled",
        "Texture": "line.png",
        "bpmfactor": 1.0,
        "father": -1,
        "isCover": 1,
        "zOrder": 0,
        "notes": [{
            "above": 1, "alpha": 255, "isFake": 0, "size": 1.0,
            "visibleTime": 999999.0, "yOffset": 0.0,
            "type": 1,
            "startTime": toFraction(t), "endTime": toFraction(t),
            "positionX": x, "speed": 1.0,
            "hitsound": f"{n}.mp3"
        } for t, x, n in pcs()],
        "eventLayers": [
            {
                "alphaEvents": [{"linkgroup": 0, "bezier": 0, "bezierPoints": [0.0, 0.0, 0.0, 0.0], "easingLeft": 0.0, "easingRight": 1.0, "easingType": 1, "startTime": [0, 0, 1], "endTime": [1, 0, 1], "start": 255, "end": 255}],
                "moveXEvents": [{"linkgroup": 0, "bezier": 0, "bezierPoints": [0.0, 0.0, 0.0, 0.0], "easingLeft": 0.0, "easingRight": 1.0, "easingType": 1, "startTime": [0, 0, 1], "endTime": [1, 0, 1], "start": 0, "end": 0}],
                "moveYEvents": [{"linkgroup": 0, "bezier": 0, "bezierPoints": [0.0, 0.0, 0.0, 0.0], "easingLeft": 0.0, "easingRight": 1.0, "easingType": 1, "startTime": [0, 0, 1], "endTime": [1, 0, 1], "start": -270, "end": -270}],
                "rotateEvents": [{"linkgroup": 0, "bezier": 0, "bezierPoints": [0.0, 0.0, 0.0, 0.0], "easingLeft": 0.0, "easingRight": 1.0, "easingType": 1, "startTime": [0, 0, 1], "endTime": [1, 0, 1], "start": 0, "end": 0}],
                "speedEvents": [{"linkgroup": 0, "bezier": 0, "bezierPoints": [0.0, 0.0, 0.0, 0.0], "easingLeft": 0.0, "easingRight": 1.0, "easingType": 1, "startTime": [0, 0, 1], "endTime": [1, 0, 1], "start": 10, "end": 10}],
            },
            *((None, ) * 4)
        ],
        "alphaControl": [{"alpha": 1.0, "easing": 1, "x": 0.0}, {"alpha": 1.0, "easing": 1, "x": 9999999.0}],
        "extended": {"inclineEvents": [{"bezier": 0, "bezierPoints": [0.0, 0.0, 0.0, 0.0], "easingLeft": 0.0, "easingRight": 1.0, "easingType": 0, "end": 0.0, "endTime": [1, 0, 1], "linkgroup": 0, "start": 0.0, "startTime": [0, 0, 1]}]},
        "posControl": [{"easing": 1, "pos": 1.0, "x": 0.0}, {"easing": 1, "pos": 1.0, "x": 9999999.0}],
        "sizeControl": [{"easing": 1, "size": 1.0, "x": 0.0}, {"easing": 1, "size": 1.0, "x": 9999999.0}],
        "skewControl": [{"easing": 1, "skew": 0.0, "x": 0.0}, {"easing": 1, "skew": 0.0, "x": 9999999.0}],
        "yControl": [{"easing": 1, "x": 0.0, "y": 1.0}, {"easing": 1, "x": 9999999.0, "y": 1.0}],
    }],
    "multiLineString": "",
    "multiScale": 1.0
}

with open(argv[2], "w", encoding="utf-8") as f:
    json.dump(result, f)
