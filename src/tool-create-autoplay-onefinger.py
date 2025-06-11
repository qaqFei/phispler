import fix_workpath as _

import json
from sys import argv
from random import uniform

import cv2
import numpy
from PIL import Image

import phichart
import const
import utils
from rpe_easing import ease_funcs

if len(argv) < 4:
    print("Usage: tool-createAutoplayOneFingerVideo <videoFile> <chartFile> <outputVideoFilePath>")
    raise SystemExit

videoFile = argv[1]
chartFile = argv[2]
outputVideoFilePath = argv[3]

with open(chartFile, "r", encoding="utf-8") as f:
    jsonData = json.load(f)

chartObj = phichart.load(jsonData)
moveDatas = []

for line in chartObj.lines:
    for note in line.notes:
        moveDatas.extend(map(lambda x: {
            "time": x[0],
            "pos": x[2][0](1.0, 1.0)
        }, note.effect_times))
        
        if note.type == const.NOTE_TYPE.FLICK:
            e = moveDatas[-1]
            moveDatas.append({
                "time": e["time"] + 0.05,
                "pos": (e["pos"][0], e["pos"][1] - 0.1)
            })

moveDatas.sort(key = lambda x: x["time"])

moveTimeCount = {}
for e in moveDatas:
    if e["time"] not in moveTimeCount:
        moveTimeCount[e["time"]] = 0
    moveTimeCount[e["time"]] += 1
MorebetsData = [e for e in moveDatas if moveTimeCount[e["time"]] > 1]
for e in MorebetsData:
    e["time"] += uniform(-0.08, 0.08)

moveDatas.append({
    "time": -1.0,
    "pos": (0.5, 0.5)
})
moveDatas.sort(key = lambda x: x["time"])
moveEvents = []
for i, e in enumerate(moveDatas):
    if i != len(moveDatas) - 1:
        ne = moveDatas[i + 1]
        moveEvents.append({
            "st": e["time"],
            "et": ne["time"],
            "sp": e["pos"],
            "ep": ne["pos"]
        })

def gfingerp(sec: float) -> tuple[float, float]:
    for e in moveEvents:
        if e["st"] <= sec < e["et"]:
            return (
                utils.easing_interpolation(sec, e["st"], e["et"], e["sp"][0], e["ep"][0], ease_funcs[9]),
                utils.easing_interpolation(sec, e["st"], e["et"], e["sp"][1], e["ep"][1], ease_funcs[9])
            )
    return moveEvents[-1]["ep"]

videoCap = cv2.VideoCapture(videoFile)
w, h = int(videoCap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(videoCap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = videoCap.get(cv2.CAP_PROP_FPS)
optWriter = cv2.VideoWriter(outputVideoFilePath, cv2.VideoWriter.fourcc(*'mp4v'), fps, (w, h), True)

finger = Image.open("./resources/finger.png")
finger = finger.resize((int(w * 0.4), int(w * 0.4 / finger.width * finger.height)))

try:
    sec = 0.0
    while True:
        ret, frame = videoCap.read()
        if not ret or frame is None:
            break
        sec += 1 / fps
        im = Image.fromarray(frame[:, :, ::-1])
        x, y = gfingerp(sec)
        im.paste(finger, tuple(map(int, (
            x * w - finger.width / 2,
            y * h
        ))), finger)
        frame = numpy.array(im)
        optWriter.write(frame[:, :, ::-1])
        print(f"\r{sec:.2f}", end="")
except Exception as e:
    print(repr(e))

videoCap.release()
