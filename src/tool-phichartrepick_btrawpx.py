import noprocessfp_warn as _

import json
from sys import argv

import librosa

if len(argv) < 3:
    print("Usage: tool-phichartrepick_btrawpx <input> <audio> <output>")
    raise SystemExit

with open(argv[1], "r", encoding="utf-8") as f:
    phic = json.load(f)
    
data, sr = librosa.load(argv[2], sr=None)
REPICKRANGE = 0.05

def getrangefre(start: float, end: float):
    count = 0
    last = 0.0
    for i in range(int(start * sr), int(end * sr)):
        v = data[i]
        
        if (last <= 0.0 and v >= 0.0) or (last >= 0.0 and v <= 0.0):
            count += 1
            
        last = v
    return (count if count != 0 else 1) / (end - start) / 2

def processNotes(notes: list, T: float) -> list:
    result = []
    
    for note in notes:
        sec = note["time"] * T
        
        if note["type"] == 3 and note["holdTime"] == 0.0:
            note["type"] = 1
        
        if note["type"] != 3:
            dt = 1 / getrangefre(sec - REPICKRANGE, sec + REPICKRANGE)
            t = sec
            et = sec + REPICKRANGE
            while t < et:
                result.append({**note, "time": t / T, "type": note["type"]})
                t += dt
        else:
            ht = note["holdTime"] * T
            holdet = sec + ht
            dt_s = 1 / getrangefre(sec - REPICKRANGE, sec + REPICKRANGE)
            dt_e = 1 / getrangefre(holdet - REPICKRANGE, holdet + REPICKRANGE)
            t = sec
            while t < holdet:
                dt = (t - sec) / ht * (dt_e - dt_s) + dt_s
                result.append({**note, "time": t / T, "type": 3, "holdTime": dt})
                t += dt
    
    return result

for line in phic["judgeLineList"]:
    line["notesAbove"] = processNotes(line["notesAbove"], 1.875 / line["bpm"])
    line["notesBelow"] = processNotes(line["notesBelow"], 1.875 / line["bpm"])

json.dump(phic, open(argv[3], "w", encoding="utf-8"), ensure_ascii=False)
