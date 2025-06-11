import tkinter as tk
import sys
import json

import phichart
import utils
import dxsound_win as dxsound
from dxsmixer_win import mixer
from exitfunc import exitfunc

if len(sys.argv) < 3:
    print("tool-beat-analysis <audio-file> <chart-file> [speed=1.0]")
    raise SystemExit

speed = float(sys.argv[3]) if len(sys.argv) >= 4 else 1.0
dxsound.speed = speed

mixer.music.load(sys.argv[1])
mixer.music.set_volume(0.4)
chart = phichart.load(json.load(open(sys.argv[2], "r", encoding="utf-8")))
dxsound.speed = 1.0
metronome = dxsound.directSound("./resources/metronome.wav")
metronome_lowv = dxsound.directSound("./resources/metronome.wav")
metronome_lowv.set_volume(0.15)

def close():
    exitfunc(0)

def mainloop():
    bpm = chart.options.globalBpmList[0].bpm if chart.options.globalBpmList is not None else chart.lines[0].bpms[0].bpm
    note_times_rawlist = [j.time for i in chart.lines for j in i.notes if not j.isFake]
    note_times = utils.IterRemovableList(note_times_rawlist)
    lineunit = (4, 10)
    maxtime = mixer.music.get_length() * speed
    maxbeat = maxtime / (60 / bpm)
    beat2y = lambda beat: beat * h * (1 / lineunit[1])
    
    mixer.music.play()
    root.deiconify()
    last_beat = -1.0
    while True:
        canvas.delete("all")
        now_t = mixer.music.get_pos() * speed
        now_beat = now_t / (60 / bpm)
        top_y = -beat2y(now_beat) + h / 2
        
        if last_beat // 1 != now_beat // 1:
            metronome_lowv.play()
        
        now_draw_beat = 0
        while now_draw_beat <= maxbeat:
            y = beat2y(now_draw_beat) + top_y
            
            if 0 <= y <= h:
                canvas.create_line(0, y, w, y, fill="black", width=1)
                
            if now_draw_beat < now_beat < now_draw_beat + 1:
                canvas.create_line(
                    w * (now_beat - now_draw_beat), y,
                    w * (now_beat - now_draw_beat), beat2y(now_draw_beat + 1) + top_y,
                    fill="skyblue", width=4
                )
                
            now_draw_beat += 1
        
        for i in range(1, lineunit[0]):
            canvas.create_line(w // lineunit[0] * i, 0, w // lineunit[0] * i, h, fill="red", width=1)
        
        for note_t, remove_this in note_times:
            if now_t > note_t:
                metronome.play()
                remove_this()
        
        for note_t in note_times_rawlist:
            beat = note_t / (60 / bpm)
            y = beat2y(beat // 1) + top_y + h * (1 / lineunit[1]) / 2
            x = w * (beat % 1)
            canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill="black")
        
        last_beat = now_beat
        root.update()

root = tk.Tk()
root.withdraw()
root.title("Beat Analysis")
size = 0.5
w, h = (
    int(root.winfo_screenwidth() * size),
    int(root.winfo_screenheight() * size),
)
root.geometry(f"{w}x{h}")
root.resizable(False, False)
root.protocol("WM_DELETE_WINDOW", close)

canvas = tk.Canvas(root, width=w, height=h, highlightthickness=0, bg="white")
canvas.pack()

mainloop()
