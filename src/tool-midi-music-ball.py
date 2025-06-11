from __future__ import annotations

import fix_workpath as _

import time
import math
import random
import platform
import ctypes
from os import popen
from sys import argv
from threading import Thread

import midi_parse

import wcv2matlike
import webcv
import needrelease
import tempdir
import utils
import cv2
from dxsmixer import mixer
from exitfunc import exitfunc
from graplib_webview import *

if len(argv) < 3:
    print("Usage: tool-midi-music-ball <sf2-file> <midi-file> [--render-video <video-file>] [--video-fps <fps>]=60 [--video-width <width>]=1920 [--video-height <height>]=1080 [--render-video-buffer-size <buffer-size>]=45")
    print("Tip: Must add fluidsynth and ffmpeg to PATH")
    raise SystemExit

is_render_video = "--render-video" in argv
video_path = argv[argv.index("--render-video") + 1] if is_render_video else None
video_fps = float(argv[argv.index("--video-fps") + 1]) if "--video-fps" in argv else 60
video_width = int(argv[argv.index("--video-width") + 1]) if "--video-width" in argv else 1920
video_height = int(argv[argv.index("--video-height") + 1]) if "--video-height" in argv else 1080
render_video_buffer_size = int(argv[argv.index("--render-video-buffer-size") + 1]) if "--render-video-buffer-size" in argv else 45
spwaning_baffle = True

if is_render_video:
    argv.extend((
        "--size",
        str(video_width), str(video_height),
    ))

with open(argv[2], "rb") as f:
    midi = midi_parse.MidiFile(f.read())

msgs = [msg for track in midi.tracks for msg in track if msg["type"] == "note_on" and msg["velocity"] > 0]

if not msgs:
    raise SystemExit("No note_on message in midi file")

msgs = list({msg["sec_time"]: msg for msg in msgs}.values())
msgs.sort(key=lambda msg: msg["sec_time"])

for i, msg in enumerate(msgs):
    if i != 0:
        msg["delta"] = msg["sec_time"] - msgs[i - 1]["sec_time"]
    else:
        msg["delta"] = msg["sec_time"]

class Vector2:
    def __init__(self, x: float = 0.0, y: float = 0.0):
        self.x = x
        self.y = y

    def __add__(self, other: Vector2):
        return Vector2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Vector2):
        return Vector2(self.x - other.x, self.y - other.y)
    
    def __mul__(self, other: Vector2):
        return Vector2(self.x * other, self.y * other) if not isinstance(other, Vector2) else Vector2(self.x * other.x, self.y * other.y)

    def __truediv__(self, other: Vector2):
        return Vector2(self.x / other, self.y / other) if not isinstance(other, Vector2) else Vector2(self.x / other.x, self.y / other.y)

    def __repr__(self):
        return f"Vector2({self.x}, {self.y})"
    
    def __iter__(self):
        yield self.x
        yield self.y
    
    def copy(self):
        return Vector2(self.x, self.y)

history_ball_positions: list[tuple[float, Vector2]]
def reset_state():
    global ball_position
    global ball_speed, ball_radius, ball_color
    global ball_face, ball_last_collide_time, ball_time
    global midi_msg_i
    global camera_position
    global history_ball_positions
    global camera_width
    global pre_collide_time
    global rd_face_random_pool_index
    
    ball_position = Vector2()
    ball_speed = 20.0
    ball_radius = 0.2
    ball_color = "rgb(255, 255, 255)"
    ball_face = 45
    ball_last_collide_time = 0.0
    ball_time = 0.0
    midi_msg_i = 0
    camera_position = Vector2()
    history_ball_positions = []
    camera_width = 15.0
    pre_collide_time = 0.0
    rd_face_random_pool_index = -1

reset_state()
baffles: list[tuple[Vector2, float, str, float]] = []

rd_face_method = 1
rd_face_random_pool = [random.randint(1, 2) for _ in range(100_0000)]

def rd_face_method_creater():
    global rd_face_method
    
    rd_face_method = 1 if rd_face_method == 2 else 2
    return rd_face_method

def rd_face_method_creater():
    global rd_face_random_pool_index

    rd_face_random_pool_index += 1
    if rd_face_random_pool_index >= len(rd_face_random_pool):
        rd_face_random_pool_index = 0
        
    return rd_face_random_pool[rd_face_random_pool_index]

# rd_face_method_creater = lambda: 1

def main():
    global spwaning_baffle
    
    tool_tempdir = tempdir.createTempDir()
    need_reset_cp = platform.system() == "Windows" and ctypes.windll.kernel32.GetConsoleWindow()
    
    if need_reset_cp:
        raw_cp = ctypes.windll.kernel32.GetConsoleOutputCP()
            
    popen(f"fluidsynth -ni \"{argv[1]}\" \"{argv[2]}\" -F \"{tool_tempdir}\\temp.wav\"").read()
     
    if need_reset_cp:
        ctypes.windll.kernel32.SetConsoleOutputCP(raw_cp)
    
    mixer.music.load(f"{tool_tempdir}/temp.wav")
    
    if is_render_video:
        t = 0
        while t <= midi.second_length:
            update(1 / video_fps)
            t += 1 / video_fps
            
        reset_state()
        spwaning_baffle = False
        
        writer = cv2.VideoWriter(
            f"{tool_tempdir}/temp.mp4",
            cv2.VideoWriter.fourcc(*"mp4v"),
            video_fps,
            (video_width, video_height),
            True
        )
        needrelease.add(writer.release)
        
        def writeFrame(frames: list[bytes]):
            for data in frames:
                matlike = utils.bytes2matlike(data, video_width, video_height)
                writer.write(matlike)
        
        wcv2matlike.callback = writeFrame
        httpd, port = wcv2matlike.createServer()
        
        root.run_js_code(f"initUploadFrame({render_video_buffer_size}, 'http://127.0.0.1:{port}/');")
        
        t = 0.0
        while t <= midi.second_length:
            update(1 / video_fps)
            render()
            root.wait_jspromise("uploadFrame();")
            t += 1 / video_fps
            print(f"\r{midi_msg_i}/{len(msgs)}", end="")
        
        root.wait_jspromise("upload_all_frames(true);")
        
        httpd.shutdown()
        writer.release()
        needrelease.remove(writer.release)
        
        popen(f"ffmpeg -i \"{tool_tempdir}/temp.mp4\" -i \"{tool_tempdir}/temp.wav\" -vcodec copy -acodec copy \"{video_path}\" -y").read()
        root.destroy()
    else:
        lt = time.perf_counter()
        mixer.music.play()
        while True:
            update(time.perf_counter() - lt)
            lt = time.perf_counter()
            render()

def update(dt: float):
    global ball_position, camera_position
    global ball_face, midi_msg_i, ball_time
    global ball_last_collide_time
    
    ball_time += dt
    msg = msgs[min(midi_msg_i, len(msgs) - 1)]
    
    rd_face = False
    while ball_time - ball_last_collide_time + pre_collide_time >= msg["delta"]:
        if not rd_face:
            match rd_face_method_creater():
                case 1:
                    ball_face = (180 - ball_face) % 360
                    
                    if 0 <= ball_face < 90:
                        make_ball_change_face_baffle_rotate = 90
                    elif 90 <= ball_face < 180:
                        make_ball_change_face_baffle_rotate = -90
                    elif 180 <= ball_face < 270:
                        make_ball_change_face_baffle_rotate = -90
                    else:
                        make_ball_change_face_baffle_rotate = 90
                        
                case 2:
                    ball_face = (360 - ball_face) % 360
                    
                    if 0 <= ball_face < 90:
                        make_ball_change_face_baffle_rotate = 180
                    elif 90 <= ball_face < 180:
                        make_ball_change_face_baffle_rotate = 180
                    elif 180 <= ball_face < 270:
                        make_ball_change_face_baffle_rotate = 0
                    else:
                        make_ball_change_face_baffle_rotate = 0
        
        rd_face = True
                
        ball_last_collide_time += msg["delta"]
        midi_msg_i += 1
        if midi_msg_i >= len(msgs):
            break
        msg = msgs[midi_msg_i]
    
    ball_position += Vector2(
        math.cos(math.radians(ball_face)) * ball_speed * dt,
        math.sin(math.radians(ball_face)) * ball_speed * dt,
    )
    
    if rd_face and spwaning_baffle:
        baffles.append((ball_position.copy(), make_ball_change_face_baffle_rotate, random.choice((
            "skyblue",
            "pink",
            "orange",
            "green",
            "red",
            "yellow",
            "purple",
            "cyan",
            "lime",
            "magenta",
        )), ball_time))
    
    camera_position += (ball_position - camera_position) * min(5 * dt, 1.0)
    
    history_ball_positions.append((ball_time, ball_position.copy()))

def p2p(pos: Vector2):
    return (pos - camera_lt) / camera_size * Vector2(w, h)

def s2s(size: float):
    return size / camera_width * w

def render():
    global camera_lt
    global history_ball_positions
    
    clearCanvas(wait_execute=True)
    
    camera_lt = camera_position - camera_size / 2
    ball_scrpos = p2p(ball_position)
    ball_scrrad = s2s(ball_radius)
        
    drawCircle(tuple(ball_scrpos), ball_scrrad * 2, ball_scrrad, ball_color, wait_execute=True)
    
    history_ball_at = 0.5
    for t, pos in reversed(history_ball_positions):
        if ball_time - t > history_ball_at:
            break
        
        p = (ball_time - t) / history_ball_at
        p = p - (1.0 - p) ** 3
        
        ctxSave(wait_execute=True)
        ctxMutGlobalAlpha(1.0 - p, wait_execute=True)
        drawCircle(
            tuple(p2p(pos)),
            ball_scrrad * 2,
            ball_scrrad,
            ball_color,
            wait_execute = True
        )
        ctxRestore(wait_execute=True)
        
    history_baffle_at = 0.8
    for baffleball_pos, baffle_face, baffle_color, baffle_time in reversed(baffles):
        pt = ball_time - baffle_time
        if pt > history_baffle_at:
            break
        
        if pt < -history_baffle_at:
            continue
        
        baffle_pos = utils.rotate_point(*p2p(Vector2(*baffleball_pos)), baffle_face + 90, s2s(ball_radius * 2))
        baffle_rx = 3
        baffle_line_pos = (
            *utils.rotate_point(*baffle_pos, baffle_face, ball_scrrad * baffle_rx),
            *utils.rotate_point(*baffle_pos, baffle_face, -ball_scrrad * baffle_rx),
        )
        p = (
            (pt / history_baffle_at)
            if pt >= 0
            else ((-pt) / history_baffle_at)
        )
        p = p - (1.0 - p) ** 3
        
        ctxSave(wait_execute=True)
        ctxMutGlobalAlpha(1.0 - p, wait_execute=True)
        
        utils.shadowDrawer.root = root
        with utils.shadowDrawer(baffle_color, (w + h) / 200):
            drawLine(
                *baffle_line_pos,
                (w + h) * 0.004,
                baffle_color,
                wait_execute = True
            )
        
        ctxRestore(wait_execute=True)
    
    history_ball_positions = [x for x in history_ball_positions if ball_time - x[0] < history_ball_at]
    
    root.run_js_wait_code()

root = webcv.WebCanvas(
    width = 1, height = 1,
    x = -webcv.screen_width, y = -webcv.screen_height,
    title = "tool-midi-music-ball",
    debug = "--debug" in argv,
    resizable = False,
    renderdemand = True, renderasync = True,
)

def init():
    global webdpr
    global w, h
    global camera_size

    w, h, webdpr, _, _ = root.init_window_size_and_position(0.6)
    
    camera_size = Vector2(camera_width, camera_width * h / w)
    
    webdpr = root.run_js_code("window.devicePixelRatio;")
    if webdpr != 1.0:
        root.run_js_code(f"lowquality_scale = {1.0 / webdpr};")

    root.run_js_code(f"resizeCanvas({w}, {h}, {{willReadFrequently: true}});")
    
    Thread(target=main, daemon=True).start()
    root.wait_for_close()
    atexit_run()

def atexit_run():
    tempdir.clearTempDir()
    needrelease.run()
    exitfunc(0)

Thread(target=root.init, args=(init, ), daemon=True).start()
root.start()
atexit_run()
