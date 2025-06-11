import tkinter as tk
import sys
import json
import time
from os.path import dirname, join as joinpath
from ctypes import windll

from PIL import Image, ImageTk

import phichart
import utils
from dxsmixer_win import mixer
from exitfunc import exitfunc

if len(sys.argv) < 3:
    print("tool-tkplayer <audio-file> <chart-file> [im_scale=1.0]")
    raise SystemExit

ims = float(sys.argv[3]) if len(sys.argv) >= 4 else 1.0
font_path = "./rescources/font.ttf"

while windll.gdi32.RemoveFontResourceA(font_path):
    ...

windll.gdi32.AddFontResourceA(font_path)

mixer.music.load(sys.argv[1])
chart = phichart.load(json.load(open(sys.argv[2], "r", encoding="utf-8")))

for line in chart.sorted_lines.copy():
    if line.isAttachUI:
        chart.sorted_lines.remove(line)

def close():
    exitfunc(0)

windows = [tk.Tk() for _ in chart.sorted_lines]
immap = {}

for win in windows:
    win.attributes("-fullscreen", True)
    win.attributes("-disabled", True)
    win.attributes("-topmost", True)
    win.attributes("-transparentcolor", "black")
    w, h = 1280, 720
    sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
    win.geometry(f"{w}x{h}+{int(sw / 2 - w / 2)}+{int(sh / 2 - h / 2)}")
    cv = tk.Canvas(win, width=w, height=h, bg="black", highlightthickness=0)
    cv.pack()
    setattr(win, "cv", cv)
    
for i, line in enumerate(chart.sorted_lines):
    if line.isTextureLine:
        im = Image.open(joinpath(dirname(sys.argv[2]), line.texture))
        print("loading", line.texture)
        immap[i] = ImageTk.PhotoImage(im.resize((
            int(im.width / 1350 * w * ims),
            int(im.height / 900 * h * ims)
        )), master=windows[i])

nowLineWidth, nowLineHeight = (
    w * chart.options.lineWidthUnit[0] + h * chart.options.lineWidthUnit[1],
    w * chart.options.lineHeightUnit[0] + h * chart.options.lineHeightUnit[1]
)

cache_map: dict[int, tuple] = {}

for i, im in immap.items():
    cv: tk.Canvas = getattr(windows[i], "cv")
    cv.create_image(0, 0, image=im, anchor="nw")
    windows[i].update()
    cv.delete("all")
    windows[i].update()

mixer.music.play()
fps_calc = utils.FramerateCalculator()
target_fps = 120

while True:
    st = time.perf_counter()
    t = mixer.music.get_pos()
    
    for i, (line, win) in enumerate(zip(chart.sorted_lines, windows)):
        (
            linePos,
            lineAlpha,
            lineRotate,
            
            lineScaleX,
            lineScaleY,
            lineText,
            lineColor
        ) = line.getState(t, (255, 236, 159))
        
        linePos = (linePos[0] * w, linePos[1] * h)
        lineDrawPos = (
            *utils.rotate_point(*linePos, lineRotate, nowLineWidth / 2 * lineScaleX),
            *utils.rotate_point(*linePos, lineRotate, -nowLineWidth / 2 * lineScaleX)
        )
        
        cache_data_collect = (linePos, lineAlpha, lineRotate, lineScaleX, lineScaleY, lineText, lineColor)
        
        if i not in cache_map or (
            cache_map[i] != cache_data_collect
        ):
            last_data = cache_map.get(i, None)
            cache_map[i] = cache_data_collect
        
            cv: tk.Canvas = getattr(win, "cv")
            cv.delete("all")
            
            if lineText is not None:
                cv.create_text(*linePos, text=lineText, font=("Source Han Sans & Saira Hybrid", int((w + h) / 75 * (lineScaleX + lineScaleY) / 2)), fill="#%02x%02x%02x" % tuple(map(int, lineColor)))
            elif line.isTextureLine:
                if lineAlpha > 0.0 and lineScaleX * lineScaleY > 0.0:
                    cv.create_image(*linePos, image=immap[i], anchor="center")
            else:
                if nowLineHeight * lineScaleY > 0.0:
                    cv.create_line(
                        *lineDrawPos,
                        width=nowLineHeight * lineScaleY,
                        fill="#%02x%02x%02x" % tuple(map(int, lineColor))
                    )
            
            if last_data is None or last_data[1] != lineAlpha:
                win.attributes("-alpha", lineAlpha)
            
            win.update()
    
    fps_calc.frame()
    print(f"{fps_calc.framerate:.2f} FPS")
    time.sleep(max(0, 1 / target_fps - (time.perf_counter() - st)))
        