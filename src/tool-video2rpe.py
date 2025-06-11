import json
from sys import argv
from PIL import Image

import cv2

import tool_example_rpechart

if len(argv) < 3:
    print("Usage: tool-video2rpe <input video> <output rpe chart>")
    raise SystemExit

w, h = 64, 36
video = cv2.VideoCapture(argv[1])
vwidth, vheight = int(video.get(cv2.CAP_PROP_FRAME_WIDTH)), int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
vp = vwidth / vheight
if vp >= w / h:
    vheight = int(w / vp)
    vwidth = w
else:
    vwidth = int(h * vp)
    vheight = h

tpos = lambda x, y: (1350 * (x - 1 / 2), 900 * (1 / 2 - y))
getindex = lambda x, y: x * h + y

def getLine(x: float, y: float, o: int):
    l = tool_example_rpechart.line.copy()
    l["zOrder"] = o
    
    l["eventLayers"][0]["moveXEvents"][0]["start"] = x
    l["eventLayers"][0]["moveXEvents"][0]["end"] = x
    l["eventLayers"][0]["moveYEvents"][0]["end"] = y
    l["eventLayers"][0]["moveYEvents"][0]["end"] = y
    
    l["extended"]["colorEvents"] = []
    l["extended"]["textEvents"] = [tool_example_rpechart.ne("■", "■", [0, 0, 1], [1, 0, 1])]
    return l

rpeChart = tool_example_rpechart.chart.copy()
rpeChart["BPMList"][0]["bpm"] = 60 * int(video.get(cv2.CAP_PROP_FPS))

for x in range(w):
    for y in range(h):
        rpeChart["judgeLineList"].append(getLine(*tpos(x / w, y / h), getindex(x, y)))

def appendColor(line, color, st, et):
    line["extended"]["colorEvents"].append(tool_example_rpechart.ne(color, color, [et, 0, 1], [st, 0, 1]))

fcut = 0
while True:
    ret, frame = video.read()
    if not ret: break
    pilFrame = Image.fromarray(frame[:, :, ::-1])
    newPilFrame = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    newPilFrame.paste(pilFrame.resize((vwidth, vheight)), (int((w - vwidth) / 2), int((h - vheight) / 2)))
    for x in range(w):
        for y in range(h):
            r, g, b, a = newPilFrame.getpixel((x, y))
            if a != 0:
                line = rpeChart["judgeLineList"][getindex(x, y)]
                if not line["extended"]["colorEvents"]:
                    appendColor(line, (r, g, b), fcut, fcut + 1)
                else:
                    laste = line["extended"]["colorEvents"][-1]
                    if laste["end"] == [r, g, b]:
                        laste["endTime"][0] = fcut + 1
                    else:
                        appendColor(line, (r, g, b), fcut, fcut + 1)
    fcut += 1
    print(fcut)

video.release()
with open(argv[2], "w", encoding="utf-8") as f:
    json.dump(rpeChart, f, ensure_ascii=False, separators=(",", ":"))
