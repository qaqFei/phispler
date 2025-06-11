import json
import random
from sys import argv
from fractions import Fraction

import webcv

if len(argv) < 3:
    print("Usage: tool-lrcinrpe <input> <lrc> <output> [split=False]")
    raise SystemExit

split = argv[4] == "True" if len(argv) >= 5 else False

class LrcParser:
    def __init__(self, lrc: str):
        self.lines = lrc.split("\n")
        self.times: list[float, str] = []
        self.offset = 0.0
        
        for index, line in enumerate(self.lines):
            tag, line = self._readtag(line)
            if tag is None: continue
            if tag.startswith("offset:"):
                self.offset = float(tag[7:])
            
            try:
                ns = list(map(int, tag.replace(".", ":").split(":")))
                time = ns[0] * 60 + ns[1] + ns[2] / 100
                self.times.append([time, line, True, line])
            except Exception:
                pass
        
        
        if split:
            new = []
            for i, (time, line, _, _) in enumerate(self.times):
                dur = min(len(line) * 0.2, (self.times[i + 1][0] - time) if i != len(self.times) - 1 else 1e9)
                for j in range(len(line)):
                    t = time + j / len(line) * dur
                    new.append([t, line[:(j + 1)], j == 0, line])
            self.times[:] = new
                
        self.times.sort(key=lambda x: x[0])
    
    def _readtag(self, line: str):
        if not line: return None, ""
        tagcontent = []
        count = 0
        for i, s in enumerate(line):
            if s == "[": count += 1
            elif s == "]": count -= 1
            else: tagcontent.append(s)
            if count == 0:
                break
        return "".join(tagcontent), line[i + 1:]
    
    def dooffset(self):
        for i in range(len(self.times)):
            self.times[i][0] += self.offset
    
with open(argv[1], "r", encoding="utf-8") as f:
    rpe = json.load(f)

with open(argv[2], "r", encoding="utf-8") as f:
    lrc = LrcParser(f.read())

def f2b(x: list[int]):
    return x[0] + x[1] / x[2]

def sec2f(x: float):
    beat = 0.0
    for i, e in enumerate(rpe["BPMList"]):
        if i != len(rpe["BPMList"]) - 1:
            et_beat = f2b(rpe["BPMList"][i + 1]["startTime"]) - f2b(e["startTime"])
            et_sec = et_beat * (60 / e["bpm"])
            
            if x >= et_sec:
                beat += et_beat
                x -= et_sec
            else:
                beat += x / (60 / e["bpm"])
                break
        else:
            beat += x / (60 / e["bpm"])
            
    fra = Fraction(beat % 1.0).limit_denominator((2 << 30) - 1)
    return [int(beat), fra.numerator, fra.denominator]

createEvent = lambda st, et, sv,  ev, eas: {
    "linkgroup": 0,
    "bezier": 0,
    "bezierPoints": [0.0, 0.0, 0.0, 0.0],
    "easingLeft": 0.0,
    "easingRight": 1.0,
    "easingType": eas,
    "end": ev,
    "start": sv,
    "startTime": st,
    "endTime": et
}
lrc.offset += rpe["META"]["offset"]
lrc.dooffset()
lrcline = {
    "Group": 0,
    "Name": "Untitled",
    "Texture": "line.png",
    "alphaControl": [
        {"alpha": 1.0, "easing": 1, "x": 0.0},
        {"alpha": 1.0, "easing": 1, "x": 9999999.0}
    ],
    "bpmfactor": 1.0,
    "eventLayers": [{
        "alphaEvents": [],
        "moveXEvents": [],
        "moveYEvents": [],
        "rotateEvents": [],
        "speedEvents": [createEvent([0, 0, 1], [1, 0, 1], 10.0, 10.0, 1)],
    }],
    "extended": {
        "inclineEvents": [createEvent([0, 0, 1], [1, 0, 1], 0.0, 0.0, 0)],
        "colorEvents": [],
        "textEvents": []
    },
    "father": -1,
    "isCover": 1,
    "notes": [],
    "zOrder": 0
}

eventchoices = [
    {
        "sx": -0.5, "ex": -0.45,
        "sy": 0.35, "ey": 0.35,
        "a_e": 4, "p_e": 8,
        "dx": 0.5
    },
    {
        "sx": 0.5, "ex": 0.45,
        "sy": 0.35, "ey": 0.35,
        "a_e": 4, "p_e": 8,
        "dx": -0.5
    }
]

colors = [
    [127, 255, 212],
    [84, 255, 159],
    [0, 191, 255],
    [255, 215, 0],
    [255, 106, 106],
    [255, 165, 0],
    [255, 105, 180],
    [255, 48, 48],
    [72, 118, 255]
]

def gettextwidth(text: str):
    return window.run_js_code(f"ctx.measureText({repr(text)}).width")

window = webcv.WebCanvas(width=0, height=0, x=0, y=0, hidden=True)
window.run_js_code("ctx = document.createElement('canvas').getContext('2d'); ctx.font = '40.5px Arial';")
animtime = 0.5
layer = lrcline["eventLayers"][0]

lastcolor = [255, 255, 255]
for i, (time, line, ref, alltext) in enumerate(lrc.times):
    print(time, line)
    nt = lrc.times[i + 1][0] if i != len(lrc.times) - 1 else 1e9
    dur = nt - time
    at = min(dur, animtime + 0.1) - 0.1 if dur > 0.1 else dur
    st, et = sec2f(time), sec2f(time + at)
    if ref:
        ec = eventchoices[random.randint(0, len(eventchoices) - 1)]
        color = colors[random.randint(0, len(colors) - 1)]
    textsize = gettextwidth(alltext)
    dx = textsize * ec["dx"]
    if ref:
        layer["alphaEvents"].append(createEvent(st, et, 0.0, 255.0, ec["a_e"]))
        layer["moveXEvents"].append(createEvent(st, et, ec["sx"] * 1350 + dx, ec["ex"] * 1350 + dx, ec["p_e"]))
        layer["moveYEvents"].append(createEvent(st, et, ec["sy"] * 900, ec["ey"] * 900, ec["p_e"]))
        lrcline["extended"]["colorEvents"].append(createEvent(st, et, lastcolor, color, 8))
    lrcline["extended"]["textEvents"].append(createEvent(st, et, line, line, 1))
    lastcolor = color
    
rpe["judgeLineList"].append(lrcline)
json.dump(rpe, open(argv[3], "w", encoding="utf-8"), ensure_ascii=False)
