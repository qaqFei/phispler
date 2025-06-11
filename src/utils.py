from __future__ import annotations

import typing
import random
import logging
import time
import re
import socket
from sys import argv
from os import popen
from os.path import isfile
from dataclasses import dataclass

from PIL import Image

import const
import phira_respack
import tempdir
import webcv
import graplib_webview
from light_utils import *

note_id = -1
random_block_num = eval(argv[argv.index("--random-block-num") + 1]) if "--random-block-num" in argv else 4
rpe_texture_scalemethod = argv[argv.index("--rpe-texture-scalemethod") + 1] if "--rpe-texture-scalemethod" in argv else "by-width"

if rpe_texture_scalemethod not in ("by-width", "by-height"):
    logging.warning(f"Unknown scale method: {rpe_texture_scalemethod}, using 'by-width' instead.")
    rpe_texture_scalemethod = "by-width"

def Get_A_New_NoteId():
    global note_id
    note_id += 1
    return note_id

def newRandomBlocks() -> tuple[tuple[float, float], ...]:
    return tuple(
        (random.uniform(0.0, 360.0), random.uniform(185.0, 265.0))
        for _ in range(random_block_num)
    )

def createDownBlockImageGrd():
    grd = Image.new("RGBA", (1, 5), (0, 0, 0, 0))
    grd.putpixel((0, 4), (0, 0, 0, 204))
    grd.putpixel((0, 3), (0, 0, 0, 128))
    grd.putpixel((0, 2), (0, 0, 0, 64))
    return grd

def getNewPort():
    port = const.BASE_PORT
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind(("", port))
            s.close()
            return port
        except OSError:
            port += 1

bae_bs = 2.15
class begin_animation_eases_class:
    @staticmethod
    def im_ease(x):
        if x <= (1 / bae_bs): return 0.0
        x -= (1 / bae_bs); x /= (1 - (1 / bae_bs))
        a = max(0, 1.4 * x - 0.25) + 0.3
        b = min(a, 1.0)
        return b ** 7
    
    @staticmethod
    def background_ease(x):
        x *= 4
        if x >= 1.0: return 1.0
        if x <= 0.0: return 0.0
        return 1 - (abs(x - 1)) ** 3
    
    @staticmethod
    def tip_alpha_ease(x): #emm... linear
        return min(max(0.0, 3 * x - 0.25), 1.0)
    
    @staticmethod
    def info_data_ease(x):
        if x >= 1.0: return 1.0
        if x <= 0.0: return 0.0
        return 1 - (1 - x) ** 3
    
    @staticmethod
    def background_block_color_alpha_ease(x):
        if x >= 1.0: return 1.0
        if x <= 0.0: return 0.0
        return (1 - x ** 2) ** 0.5

class finish_animation_eases_class:
    @staticmethod
    def all_ease(x):
        if x <= 0.0: return 0.0
        if x >= 1.0: return 1.0
        k = 1 - x
        return 1 - k ** 10
    
    @staticmethod
    def score_alpha_ease(x):
        k = 0.125
        x -= k
        x *= (1 / (1 - k))
        x *= 5.0
        if x <= 0.0: return 0.0
        if x >= 1.0: return 1.0
        return x ** 2

    @staticmethod
    def level_size_ease(x):
        k = 3.0
        return max(0.5 - (k * max(x - 1 / 6, 0.0)) ** 4, 0.0) + 1.0
    
    @staticmethod
    def level_alpha_ease(x):
        k = 0.25
        x -= k
        x *= (1 / (1 - k))
        x *= 5.0
        if x <= 0.0: return 0.0
        if x >= 1.0: return 1.0
        return x ** 2
    
    @staticmethod
    def playdata_alpha_ease(x):
        k = 0.25
        x -= k
        x *= (1 / (1 - k))
        x *= 5.0
        if x <= 0.0: return 0.0
        if x >= 1.0: return 1.0
        return x ** 2
    
    @staticmethod
    def userinfo_alpha_ease(x):
        k = 0.1875
        x -= k
        x *= (1 / (1 - k))
        x *= 5.0
        if x <= 0.0: return 0.0
        if x >= 1.0: return 1.0
        return x ** 2
    
    @staticmethod
    def button_ease(x):
        if x <= 0.0: return 0.0
        if x >= 1.0: return 1.0
        return 1 - (1 - x) ** 3

begin_animation_eases = begin_animation_eases_class()
finish_animation_eases = finish_animation_eases_class()

match rpe_texture_scalemethod:
    case "by-width":
        def conimgsize(w: int, h: int, sw: int, sh: int):
            if w == 0: return 0, 0
            rw = w / const.RPE_WIDTH * sw
            return rw, rw / w * h
        
    case "by-height":
        def conimgsize(w: int, h: int, sw: int, sh: int):
            if h == 0: return 0, 0
            rh = h / const.RPE_HEIGHT * sh
            return rh / h * w, rh

# thanks for HLMC (https://github.com/2278535805)
def rpe_text_tween(sv: str, ev: str, t: float, isfill: bool) -> str:
    if "%P%" in sv and "%P%" in ev:
        sv, ev = sv.replace("%P%", ""), ev.replace("%P%", "")
        if isfill: return sv
        
        try: sv, ev = float(sv), float(ev)
        except ValueError: return "0"
        
        v = sv + t * (ev - sv)
        return f"{v:.0f}" if int(sv) == sv and int(ev) == ev else f"{v:.3f}"
            
    elif not sv and not ev:
        return ""
    elif not ev:
        return rpe_text_tween(ev, sv.replace("%P%", ""), 1.0 - t, isfill)
    elif not sv:
        return ev[:int(t * len(ev))]
    
    else:
        xl, yl = len(sv), len(ev)
        ml = min(xl, yl)
        if sv[:ml] == ev[:ml]:
            take_num = int(round((yl - xl) * t)) + xl
            return sv + ev[xl:take_num]
        else:
            return sv.replace("%P%", "")

def bytes2matlike(data: bytes, w: int, h: int):
    import numpy
    
    return numpy.frombuffer(data, dtype=numpy.uint8).reshape((h, w, 3))

def easeAlpha(p: float):
    if 0.0 <= p <= 0.4: 
        return 1.0 - (1.0 - 2 * p * (0.5 / 0.4)) ** 2
    elif 0.4 <= p <= 0.8:
        return 1.0
    else:
        return (2.0 - 2.0 * ((p - 0.8) * (0.5 / 0.2) + 0.5)) ** 2

def fixorp(p: float):
    return max(0.0, min(1.0, p))

def rect2drect_l(rect: tuple[float], deg: float):
    dpower = getDPower(*getSizeByRect(rect), deg)
    w = rect[2] - rect[0]
    return (
        (rect[0] + w * dpower, rect[1]),
        (rect[2], rect[1]),
        (rect[2], rect[3]),
        (rect[0], rect[3]),
        (rect[0] + w * dpower, rect[1])
    )

def rect2drect(rect: tuple[float], deg: float):
    dpower = getDPower(*getSizeByRect(rect), deg)
    w = rect[2] - rect[0]
    return (
        (rect[0] + w * dpower, rect[1]),
        (rect[2], rect[1]),
        (rect[2] - w * dpower, rect[3]),
        (rect[0], rect[3]),
        (rect[0] + w * dpower, rect[1])
    )

def sliderValueP(value: float, values: tuple[tuple[float, float]]):
    ranges = [(values[i - 1][0], values[i][0], values[i - 1][1], values[i][1]) for i in range(len(values)) if i != 0]
    for r in ranges:
        if r[2] <= value <= r[3]:
            return (value - r[2]) / (r[3] - r[2]) * (r[1] - r[0]) + r[0]
    return 0.0 if value < values[0][1] else 1.0

def sliderValueValue(p: float, values: tuple[tuple[float, float]]):
    ranges = [(values[i - 1][0], values[i][0], values[i - 1][1], values[i][1]) for i in range(len(values)) if i != 0]
    for r in ranges:
        if r[0] <= p <= r[1]:
            return (p - r[0]) / (r[1] - r[0]) * (r[3] - r[2]) + r[2]
    return ranges[0][2] if p < ranges[0][0] else ranges[-1][3]

def checkOffset(now_t: float, raw_audio_length: float, mixer):
    # must not use set_pos to reset music
    offset_judge_range = (1 / 60) * 4
    
    if mixer.music.get_busy() and abs(music_offset := now_t - mixer.music.get_pos()) >= offset_judge_range:
        print(now_t, mixer.music.get_pos(), music_offset)
        if abs(music_offset) < raw_audio_length * 1000 * 0.75:
            logging.warning(f"mixer offset > {offset_judge_range:.5f}s, reseted chart time. (offset = {int(music_offset * 1000)}ms)")
            return music_offset
        
    return 0.0

def video2h264(video: str):
    import cv2
    cap = cv2.VideoCapture(video)
    size = (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
    probe = popen(f"ffprobe -i \"{video}\" -show_streams -v error").read()
    
    if "codec_name=h264" in probe:
        return open(video, "rb").read(), size
    
    tid = random.randint(0, 2 << 31)
    fp = f"{tempdir.createTempDir()}/{tid}.mp4"
    codecs = ["libx264", "h264_amf", "h264_mf", "h264_nvenc", "h264_qsv"]
    codecs.reverse()
    
    for c in codecs:
        popen(f"ffmpeg -loglevel quiet -hwaccel auto -i \"{video}\" -an -c:v {codecs} -crf 23 \"{fp}\" -y").read()
        if not isfile(fp): continue
        result = open(fp, "rb").read()
        if not result: continue
        return result, size

    logging.error("failed to convert video to h264")
    return open(video, "rb").read(), size

def getShaderDefault(shader: str):
    result = {}
    for line in shader.split("\n"):
        if line.startswith("uniform") and "//" in line and line.count("%") >= 2:
            try:
                name = line.split(";")[0].split(" ")[-1]
                default = list(map(float, line.split("//")[1].replace(" ", "").split("%")[1].split(",")))
                if len(default) == 1: default = default[0]
                result[name] = default
            except Exception as e:
                logging.error(f"shader default parse error: {e}")
    return result

def replaceForLoops(shader: str):
    return shader # emm, TODO: fix this

    def replace(match: re.Match[str]):
        init_part = match.group(2)
        condition = match.group(3)
        increment = match.group(4)
        body = match.group(5)
        print(init_part, condition, increment, body)
        new = f"{{{init_part}; for (int _i = 0; _i < 64; _i++) {{{replaceForLoops(body)}\n{increment}; if (!({condition})) break;}}}}"
        return new
    return re.sub(r"(for\s*\((.*?);(.*?);(.*?)\)\s*{([^}]*?)})", replace, shader, flags=re.DOTALL)

def fixShader(shader: str):
    shader = "\n".join(line for line in shader.split("\n") if not line.strip().startswith("#version"))
    shader = replaceForLoops(shader)
    
    return shader

class PhigrosPlayManager:
    def __init__(self, noteCount: int):
        self.events: list[typing.Literal["P", "G", "B", "M"]] = []
        self.event_offsets: list[float] = [] # the note click offset (s)
        self.noteCount = noteCount
    
    def addEvent(self, event: typing.Literal["P", "G", "B", "M"], offset: typing.Optional[float] = None): # Perfect, Good, Bad, Miss
        self.events.append(event)
        if offset is not None: # offset is only good judge.
            self.event_offsets.append(offset)
    
    def getLineColor(self) -> tuple[int, int, int]:
        if "B" in self.events or "M" in self.events:
            return (255, 255, 255)
        if "G" in self.events:
            return phira_respack.globalPack.goodRGB
        return phira_respack.globalPack.perfectRGB

    def getCombo(self):
        cut = 0
        for e in reversed(self.events):
            if e == "P" or e == "G":
                cut += 1
            else:
                return cut
        return cut
    
    def getAcc(self): # 实时 Acc
        if not self.events: return 1.0
        acc = 0.0
        allcut = len(self.events)
        for e in self.events:
            if e == "P":
                acc += 1.0 / allcut
            elif e == "G":
                acc += 0.65 / allcut
        return acc
    
    def getAccOfAll(self):
        acc = 0.0
        for e in self.events:
            if e == "P":
                acc += 1.0 / self.noteCount
            elif e == "G":
                acc += 0.65 / self.noteCount
        return acc
    
    def getMaxCombo(self):
        r = 0
        cut = 0
        for e in reversed(self.events):
            if e == "P" or e == "G":
                cut += 1
            else:
                r = max(r, cut)
                cut = 0
        return max(r, cut)
    
    def getScore(self):
        return self.getAccOfAll() * 900000 + self.getMaxCombo() / self.noteCount * 100000
    
    def getPerfectCount(self):
        return self.events.count("P")
    
    def getGoodCount(self):
        return self.events.count("G")
    
    def getBadCount(self):
        return self.events.count("B")
    
    def getMissCount(self):
        return self.events.count("M")
    
    def getEarlyCount(self):
        return len(list(filter(lambda x: x > 0, self.event_offsets)))
    
    def getLateCount(self):
        return len(list(filter(lambda x: x < 0, self.event_offsets)))
    
    def getLevelString(self):
        score = self.getScore()
        return pgrGetLevel(score, self.getBadCount() == 0 and self.getMissCount() == 0)

def pgrGetLevel(score: float, isFullCombo: bool):
    if isFullCombo and score == 1000000: return "AP"
    elif isFullCombo: return "FC"

    if 0 <= score < 700000:
        return "F"
    elif 700000 <= score < 820000:
        return "C"
    elif 820000 <= score < 880000:
        return "B"
    elif 880000 <= score < 920000:
        return "A"
    elif 920000 <= score < 960000:
        return "S"
    elif 960000 <= score < 1000000:
        return "V"
    elif 1000000 <= score:
        return "AP"
        
    return "F" if score < 0 else "AP"
    
def PPLM_vaildKey(key: str) -> bool:
    return key.lower() in const.ALL_LETTER

class PPLM_ProxyBase:
    def __init__(self, cobj: typing.Any) -> None: ...
    
    def get_lines(self) -> list[typing.Any]: ...
    def get_all_pnotes(self) -> list[typing.Any]: ...
    def remove_pnote(self, n: typing.Any) -> None: ...
    
    def nproxy_stime(self, n: typing.Any) -> float: ...
    def nproxy_etime(self, n: typing.Any) -> float: ...
    def nproxy_hcetime(self, n: typing.Any) -> float: ...
    
    def nproxy_typein(self, n: typing.Any, ts: tuple[typing.Any]) -> bool: ...
    def nproxy_typeis(self, n: typing.Any, t: typing.Any) -> bool: ...
    def nproxy_typeisnot(self, n: typing.Any, t: typing.Any) -> bool: return not self.nproxy_typeis(n, t)
    def nproxy_phitype(self, n: typing.Any) -> typing.Any: ...
    
    def nproxy_nowpos(self, n: typing.Any) -> tuple[float, float]: ...
    def nproxy_nowrotate(self, n: typing.Any) -> float: ...
    def nproxy_effects(self, n: typing.Any) -> const.ClickEffectType: ...
    
    def nproxy_get_pclicked(self, n: typing.Any) -> bool: ...
    def nproxy_set_pclicked(self, n: typing.Any, state: bool) -> None: ...
    
    def nproxy_get_wclick(self, n: typing.Any) -> bool: ...
    def nproxy_set_wclick(self, n: typing.Any, state: bool) -> None: ...
    
    def nproxy_get_pclick_offset(self, n: typing.Any) -> float: ...
    def nproxy_set_pclick_offset(self, n: typing.Any, offset: float) -> None: ...
    
    def nproxy_get_ckstate(self, n: typing.Any) -> typing.Any: ...
    def nproxy_set_ckstate(self, n: typing.Any, state: typing.Any) -> None: ...
    def nproxy_get_ckstate_ishit(self, n: typing.Any) -> bool: ...
    
    def nproxy_get_cksound_played(self, n: typing.Any) -> bool: ...
    def nproxy_set_cksound_played(self, n: typing.Any, state: bool) -> None: ...
    
    def nproxy_get_missed(self, n: typing.Any) -> bool: ...
    def nproxy_set_missed(self, n: typing.Any, state: bool) -> None: ...
    
    def nproxy_get_holdjudged(self, n: typing.Any) -> bool: ...
    def nproxy_set_holdjudged(self, n: typing.Any, state: bool) -> None: ...
    
    def nproxy_get_holdjudged_tomanager(self, n: typing.Any) -> bool: ...
    def nproxy_set_holdjudged_tomanager(self, n: typing.Any, state: bool) -> None: ...
    
    def nproxy_get_last_testholdmiss_time(self, n: typing.Any) -> float: ...
    def nproxy_set_last_testholdmiss_time(self, n: typing.Any, time: float) -> None: ...
    
    def nproxy_get_safe_used(self, n: typing.Any) -> bool: ...
    def nproxy_set_safe_used(self, n: typing.Any, state: bool) -> None: ...
    
    def nproxy_get_holdclickstate(self, n: typing.Any) -> typing.Any: ...
    def nproxy_set_holdclickstate(self, n: typing.Any, state: typing.Any) -> None: ...
    
    def nproxy_get_pbadtime(self, n: typing.Any) -> float: ...
    def nproxy_set_pbadtime(self, n: typing.Any, time: float) -> None: ...
    
    def nproxy_posinjudge(self, n: typing.Any, x: float, y: float) -> bool: ...

@dataclass
class PPLM_PC_ClickEvent: time: float
@dataclass
class PPLM_PC_ReleaseEvent: time: float

@dataclass
class PPLM_MOB_Touch:
    time: float
    x: float
    y: float
    i: int
    
    clickused: bool = False
    released: bool = False
    release_time: float = float("nan")
    # last_update_time: float = float("nan")

    # def __post_init__(self):
        # self.last_update_time = time.time()
    
    def update(self, t: float, x: float, y: float) -> list[tuple[float, tuple[float, float]]]:
        self.x = x
        self.y = y
        return [(time.time(), (self.x, self.y))]

class PhigrosPlayLogicManager:
    def __init__(
            self,
            pplm_proxy: PPLM_ProxyBase,
            ppps: PhigrosPlayManager,
            enable_cksound: bool,
            psound: typing.Callable[[str], typing.Any],
            mobjudge_range: float,
            w: int, h: int,
            is_chall: bool = False
        ) -> None:
        
        self.pp = pplm_proxy
        self.ppps = ppps
        self.enable_cksound = enable_cksound
        self.psound = psound
        self.mobjudge_range = mobjudge_range
        self.w, self.h = w, h
        self.enable_mob: bool = False
        self.njr = const.NOTE_JUDGE_RANGE if not is_chall else const.NOTE_JUDGE_RANGE_CHALL
        
        self.pc_clicks: list[PPLM_PC_ClickEvent] = []
        self.pc_keymap: dict[str, bool] = {i: False for i in const.ALL_LETTER}
        
        self.mob_touches: list[PPLM_MOB_Touch] = []
        self.mob_flicks: list[tuple[float, tuple[float, float]]] = []
        
        self.clickeffects: const.ClickEffectType = []
        self.badeffects: const.BadEffectType = []
        # self.misseffects: const.MissEffectType = []
    
    def bind_events(self, root: webcv.WebCanvas):
        root.run_js_code("_PhigrosPlay_KeyDown = makePlayKeyEvent((e) => {pywebview.api.call_attr('PhigrosPlay_KeyDown', e.key)}, false);")
        root.run_js_code("_PhigrosPlay_KeyUp = makePlayKeyEvent((e) => {pywebview.api.call_attr('PhigrosPlay_KeyUp', e.key)}, false);")
        root.run_js_code("_PhigrosPlay_TouchStart = (e) => pywebview.api.call_attr('PhigrosPlay_TouchStart', ...fixEventPosition(e.changedTouches[0].clientX, e.changedTouches[0].clientY), e.changedTouches[0].identifier);")
        root.run_js_code("_PhigrosPlay_TouchMove = (e) => pywebview.api.call_attr('PhigrosPlay_TouchMove', ...fixEventPosition(e.changedTouches[0].clientX, e.changedTouches[0].clientY), e.changedTouches[0].identifier);")
        root.run_js_code("_PhigrosPlay_TouchEnd = (e) => pywebview.api.call_attr('PhigrosPlay_TouchEnd', e.changedTouches[0].identifier);")
        root.run_js_code("window.addEventListener('keydown', _PhigrosPlay_KeyDown);")
        root.run_js_code("window.addEventListener('keyup', _PhigrosPlay_KeyUp);")
        root.run_js_code("window.addEventListener('touchstart', _PhigrosPlay_TouchStart);")
        root.run_js_code("window.addEventListener('touchmove', _PhigrosPlay_TouchMove);")
        root.run_js_code("window.addEventListener('touchend', _PhigrosPlay_TouchEnd);")
    
    def unbind_events(self, root: webcv.WebCanvas):
        root.run_js_code("window.removeEventListener('keydown', _PhigrosPlay_KeyDown);")
        root.run_js_code("window.removeEventListener('keyup', _PhigrosPlay_KeyUp);")
        root.run_js_code("window.removeEventListener('touchstart', _PhigrosPlay_TouchStart);")
        root.run_js_code("window.removeEventListener('touchmove', _PhigrosPlay_TouchMove);")
        root.run_js_code("window.removeEventListener('touchend', _PhigrosPlay_TouchEnd);")
    
    def pc_click(self, t: float, key: str) -> None:
        if not PPLM_vaildKey(key): return
        self.pc_keymap[key] = True
        self.pc_clicks.append(PPLM_PC_ClickEvent(time=t))
        
    def pc_release(self, t: float, key: str) -> None:
        if not PPLM_vaildKey(key): return
        self.pc_keymap[key] = False
    
    def _process_clickjudge(
        self,
        t: float, n: typing.Any,
        offset: float,
        can_use_safe_notes: list[typing.Any],
        judgetime: float
    ):
        abs_offset = abs(offset)
        
        if 0.0 <= abs_offset <= self.njr.PERFECT:
            state = const.NOTE_STATE.PERFECT
            
            self.pp.nproxy_set_ckstate(n, state)
            
            if self.pp.nproxy_typeis(n, const.NOTE_TYPE.HOLD):
                self.pp.nproxy_set_holdjudged(n, True)
                self.pp.nproxy_set_holdclickstate(n, state)
            else:
                self.ppps.addEvent("P")
                
        elif self.njr.PERFECT < abs_offset <= self.njr.GOOD:
            state = const.NOTE_STATE.GOOD
            self.pp.nproxy_set_ckstate(n, state)
            
            if self.pp.nproxy_typeis(n, const.NOTE_TYPE.HOLD):
                self.pp.nproxy_set_holdjudged(n, True)
                self.pp.nproxy_set_holdclickstate(n, state)
            else:
                self.ppps.addEvent("G", offset)
        
        elif self.njr.GOOD < abs_offset <= self.njr.BAD: # only tap can goto there
            if can_use_safe_notes and offset < 0.0:
                drag, _ = can_use_safe_notes[0]
                if not self.pp.nproxy_get_wclick(drag):
                    self.pp.nproxy_set_wclick(drag, True)
                self.pp.nproxy_set_safe_used(drag, True)
                return
            
            self.pp.nproxy_set_pbadtime(n, judgetime)
            self.pp.nproxy_set_ckstate(n, const.NOTE_STATE.BAD)
            self.ppps.addEvent("B")
            self.badeffects.append((
                judgetime,
                self.pp.nproxy_nowrotate(n),
                self.pp.nproxy_nowpos(n)
            ))
        
        if self.pp.nproxy_get_ckstate(n) != const.NOTE_STATE.MISS:
            self.pp.nproxy_set_pclick_offset(n, offset)
            self.pp.nproxy_set_pclicked(n, True)
        
        if self.pp.nproxy_get_ckstate_ishit(n):
            e = self.pp.nproxy_effects(n).pop(0)
            npos = self.pp.nproxy_nowpos(n)
            self.clickeffects.append((
                self.pp.nproxy_get_ckstate(n) == const.NOTE_STATE.PERFECT,
                t,
                *e[1:-1],
                
                (eval(f"lambda w, h: ({npos[0]} * w, {npos[1]} * h)"), *e[-1][1:])
                if self.pp.nproxy_typeis(n, const.NOTE_TYPE.HOLD) and self.pp.nproxy_stime(n) >= t
                else e[-1]
            ))
            
            if self.pp.nproxy_typeis(n, const.NOTE_TYPE.HOLD):
                self.pp.nproxy_set_last_testholdmiss_time(n, t)
    
    def pc_update(self, t: float) -> None:
        pnotes = self.pp.get_all_pnotes()
        
        keydown = any(self.pc_keymap.values())
        
        for i in pnotes.copy():
            if ( # drag / flick range judge
                keydown and
                not self.pp.nproxy_get_wclick(i) and
                self.pp.nproxy_typein(i, (const.NOTE_TYPE.DRAG, const.NOTE_TYPE.FLICK)) and
                abs((self.pp.nproxy_stime(i) - t)) <= self.njr.GOOD
            ):
                self.pp.nproxy_set_wclick(i, True)
            
            if ( # drag / flick it is time to judge
                self.pp.nproxy_get_wclick(i) and
                not self.pp.nproxy_get_pclicked(i) and
                self.pp.nproxy_stime(i) <= t
            ):
                self.pp.nproxy_set_pclicked(i, True)
                self.pp.nproxy_set_ckstate(i, const.NOTE_STATE.PERFECT)
                self.ppps.addEvent("P")
                self.clickeffects.append((True, t, *self.pp.nproxy_effects(i).pop(0)[1:]))
            
            if ( # play click sound
                self.pp.nproxy_get_pclicked(i) and
                not self.pp.nproxy_get_cksound_played(i) and
                self.pp.nproxy_get_ckstate_ishit(i)
            ):
                if self.enable_cksound:
                    self.psound(self.pp.nproxy_phitype(i))
                self.pp.nproxy_set_cksound_played(i, True)
            
            if ( # miss judge
                not self.pp.nproxy_get_pclicked(i) and
                not self.pp.nproxy_get_missed(i) and
                self.pp.nproxy_stime(i) - t < -self.njr.MISS
            ):
                self.pp.nproxy_set_missed(i, True)
                self.ppps.addEvent("M")
            
            if ( # hold holding judge
                keydown and
                self.pp.nproxy_typeis(i, const.NOTE_TYPE.HOLD) and
                self.pp.nproxy_get_pclicked(i) and
                self.pp.nproxy_get_ckstate_ishit(i) and
                self.pp.nproxy_etime(i) - 0.2 >= t
            ):
                self.pp.nproxy_set_last_testholdmiss_time(i, t)
            
            if ( # hold holding miss judge
                not keydown and
                self.pp.nproxy_typeis(i, const.NOTE_TYPE.HOLD) and
                self.pp.nproxy_get_pclicked(i) and
                self.pp.nproxy_get_ckstate_ishit(i) and
                self.pp.nproxy_etime(i) - 0.2 >= t and
                self.pp.nproxy_get_last_testholdmiss_time(i) + 0.16 <= t
            ):
                self.pp.nproxy_set_ckstate(i, const.NOTE_STATE.MISS)
                self.pp.nproxy_set_missed(i, True)
                self.ppps.addEvent("M")
            
            if ( # hold add hit event to manager
                self.pp.nproxy_typeis(i, const.NOTE_TYPE.HOLD) and
                self.pp.nproxy_get_holdjudged(i) and # if judged is true, hold state is perfect/good/ miss(miss at clicking)
                not self.pp.nproxy_get_holdjudged_tomanager(i) and
                self.pp.nproxy_hcetime(i) <= t
            ):
                self.pp.nproxy_set_holdjudged_tomanager(i, True)
                state = self.pp.nproxy_get_ckstate(i)
                if state == const.NOTE_STATE.PERFECT:
                    self.ppps.addEvent("P")
                elif state == const.NOTE_STATE.GOOD:
                    self.ppps.addEvent("G", self.pp.nproxy_get_pclick_offset(i))
            
            if ( # add hold effects
                self.pp.nproxy_typeis(i, const.NOTE_TYPE.HOLD) and
                self.pp.nproxy_get_ckstate_ishit(i) and
                self.pp.nproxy_etime(i) >= t
            ):
                for effect in self.pp.nproxy_effects(i):
                    if effect[0] <= t:
                        self.clickeffects.append((self.pp.nproxy_get_ckstate(i) == const.NOTE_STATE.PERFECT, t, *effect[1:]))
                        self.pp.nproxy_effects(i).remove(effect)
                    else:
                        break
            
            if self.pp.nproxy_typeisnot(i, const.NOTE_TYPE.HOLD) and self.pp.nproxy_stime(i) - t < - self.njr.MISS * 2:
                self.pp.remove_pnote(i)
            elif self.pp.nproxy_typeis(i, const.NOTE_TYPE.HOLD) and self.pp.nproxy_etime(i) - t < - self.njr.MISS * 2:
                self.pp.remove_pnote(i)
            elif self.pp.nproxy_stime(i) > t + self.njr.BAD * 2:
                break
        
        while self.pc_clicks:
            cke = self.pc_clicks.pop()
            
            can_judge_notes = []
            can_use_safe_notes = []
            
            for i in pnotes:
                if (
                    not self.pp.nproxy_get_pclicked(i) and
                    self.pp.nproxy_typein(i, (const.NOTE_TYPE.TAP, const.NOTE_TYPE.HOLD)) and
                    abs((offset := (self.pp.nproxy_stime(i) - cke.time))) <= (
                        self.njr.BAD \
                            if self.pp.nproxy_typeis(i, const.NOTE_TYPE.TAP) else \
                                self.njr.GOOD
                    )
                ):
                    can_judge_notes.append((i, offset))
                
                if (
                    self.pp.nproxy_typein(i, (const.NOTE_TYPE.DRAG, const.NOTE_TYPE.FLICK)) and
                    not self.pp.nproxy_get_safe_used(i) and
                    abs((offset := (self.pp.nproxy_stime(i) - cke.time))) <= self.njr.GOOD
                ):
                    can_use_safe_notes.append((i, offset))

                if self.pp.nproxy_stime(i) > cke.time + self.njr.BAD * 2:
                    break
            
            can_judge_notes.sort(key = lambda x: abs(x[1]))
            can_use_safe_notes.sort(key = lambda x: x[1])
            
            if not can_judge_notes: continue
            
            n, offset = can_judge_notes[0]
            self._process_clickjudge(t, n, offset, can_use_safe_notes, cke.time)

    def _getmobt_byid(self, i: int):
        for t in self.mob_touches:
            if t.i == i: return t
        return None
    
    def _removemobt_byid(self, i: int):
        touch = self._getmobt_byid(i)
        if touch is None: return
        self.mob_touches.remove(touch)
    
    def mob_touchstart(self, t: float, x: float, y: float, i: int):
        print(t)
        self._removemobt_byid(i)
        self.mob_touches.append(PPLM_MOB_Touch(t, x, y, i))

    def mob_touchmove(self, t: float, x: float, y: float, i: int):
        touch = self._getmobt_byid(i)
        if touch is None: return
        
        self.mob_flicks.extend(touch.update(t, x, y))
    
    def mob_touchend(self, i: int):
        touch = self._getmobt_byid(i)
        if touch is None: return
        
        touch.released = True
        touch.release_time = time.time()
    
    def _mobjudge_polygon(self, pos: tuple[float, float], rotate: float):
        rotate -= 90
        r = self.w + self.h
        s, e = rotate_point(*pos, rotate, r), rotate_point(*pos, rotate, -r)
        return (
            rotate_point(*s, rotate - 90, self.mobjudge_range / 2),
            rotate_point(*s, rotate + 90, self.mobjudge_range / 2),
            rotate_point(*e, rotate + 90, self.mobjudge_range / 2),
            rotate_point(*e, rotate - 90, self.mobjudge_range / 2)
        )

    def _topxpos(self, pos: tuple[float, float]):
        return (pos[0] * self.w, pos[1] * self.h)
    
    def mob_update(self, t: float):
        pnotes = self.pp.get_all_pnotes()
        
        for touch in self.mob_touches.copy():
            if touch.released and time.time() - touch.release_time > self.njr.GOOD:
                self.mob_touches.remove(touch)
        
        for mf in self.mob_flicks.copy():
            if time.time() - mf[0] > self.njr.GOOD:
                self.mob_flicks.remove(mf)
        
        for i in pnotes.copy():
            nowrotate = self.pp.nproxy_nowrotate(i)
            innoterange = any(
                pointInPolygon(self._mobjudge_polygon(
                    self._topxpos(self.pp.nproxy_nowpos(i)), nowrotate
                ), self._topxpos((touch.x, touch.y)))
                for touch in self.mob_touches
            )
            innoterange_hold = any(
                (pointInPolygon(self._mobjudge_polygon(
                    self._topxpos(self.pp.nproxy_nowpos(i)), nowrotate
                ), self._topxpos((touch.x, touch.y))) if not touch.released else False)
                for touch in self.mob_touches
            )
            
            if ( # drag range judge
                innoterange and
                not self.pp.nproxy_get_wclick(i) and
                self.pp.nproxy_typeis(i, const.NOTE_TYPE.DRAG) and
                abs((self.pp.nproxy_stime(i) - t)) <= self.njr.GOOD
            ):
                self.pp.nproxy_set_wclick(i, True)
            
            if (
                not self.pp.nproxy_get_wclick(i) and
                self.pp.nproxy_typeis(i, const.NOTE_TYPE.FLICK) and
                abs((self.pp.nproxy_stime(i) - t)) <= self.njr.GOOD
            ):
                for mf in self.mob_flicks.copy():
                    if (time.time() - mf[0]) > self.njr.GOOD:
                        continue
                    
                    if pointInPolygon(self._mobjudge_polygon(
                        self._topxpos(self.pp.nproxy_nowpos(i)), nowrotate
                    ), self._topxpos(mf[1])):
                        self.pp.nproxy_set_wclick(i, True)
                        self.mob_flicks.remove(mf)
                        break
                
            if ( # hold holding judge
                innoterange_hold and
                self.pp.nproxy_typeis(i, const.NOTE_TYPE.HOLD) and
                self.pp.nproxy_get_pclicked(i) and
                self.pp.nproxy_get_ckstate_ishit(i) and
                self.pp.nproxy_etime(i) - 0.2 >= t
            ):
                self.pp.nproxy_set_last_testholdmiss_time(i, t)
            
            if self.pp.nproxy_stime(i) > t + self.njr.BAD * 2:
                break
        
        for touch in self.mob_touches:
            if touch.clickused: continue
            touch.clickused = True
            
            can_judge_notes = []
            can_use_safe_notes = []
            
            for i in pnotes:
                nowrotate = self.pp.nproxy_nowrotate(i)
                innoterange = pointInPolygon(self._mobjudge_polygon(
                    self._topxpos(self.pp.nproxy_nowpos(i)), nowrotate
                ), self._topxpos((touch.x, touch.y)))
            
                if (
                    innoterange and
                    not self.pp.nproxy_get_pclicked(i) and
                    self.pp.nproxy_typein(i, (const.NOTE_TYPE.TAP, const.NOTE_TYPE.HOLD)) and
                    abs((offset := (self.pp.nproxy_stime(i) - touch.time))) <= (
                        self.njr.BAD \
                            if self.pp.nproxy_typeis(i, const.NOTE_TYPE.TAP) else \
                                self.njr.GOOD
                    )
                ):
                    can_judge_notes.append((i, offset))
                
                if (
                    innoterange and
                    self.pp.nproxy_typein(i, (const.NOTE_TYPE.DRAG, const.NOTE_TYPE.FLICK)) and
                    not self.pp.nproxy_get_safe_used(i) and
                    abs((offset := (self.pp.nproxy_stime(i) - touch.time))) <= self.njr.GOOD
                ):
                    can_use_safe_notes.append((i, offset))

                if self.pp.nproxy_stime(i) > touch.time + self.njr.BAD * 2:
                    break
    
            can_judge_notes.sort(key = lambda x: abs(x[1]))
            can_use_safe_notes.sort(key = lambda x: x[1])
            
            if not can_judge_notes: continue
            
            n, offset = can_judge_notes[0]
            self._process_clickjudge(t, n, offset, can_use_safe_notes, touch.time)
            
class FramerateCalculator:
    def __init__(self):
        self._frame_count = 0
        self._frame_lastt = time.perf_counter()
        self._frame_checklimit = 25
        self.framerate = -1
    
    def frame(self):
        self._frame_count += 1
        
        if self._frame_count >= self._frame_checklimit:
            uset = time.perf_counter() - self._frame_lastt
            self.framerate = (self._frame_count / uset) if uset else float("inf")
            self._frame_count = 0
            self._frame_lastt = time.perf_counter()
            
            if self.framerate != float("inf"):
                self._frame_checklimit = self.framerate * 0.1

_TimeoutTaskManagerT = typing.TypeVar("_T")
class TimeoutTaskManager(typing.Generic[_TimeoutTaskManagerT]):
    """
    add_task function t arg must be monotonically incremental 
    """
    
    def __init__(self):
        self.datas = []
        self.valid: typing.Callable[[_TimeoutTaskManagerT], bool] = lambda x: True
        
    def add_task(self, t: float, o: _TimeoutTaskManagerT):
        if self.valid(o):
            self.datas.append((t, o))
    
    def get_task(self, t: float):
        result = []
        
        for i in self.datas.copy():
            tt, o = i
            if tt <= t:
                result.append(o)
                self.datas.remove(i)
            break
            
        return result

class shadowDrawer:
    root: webcv.WebCanvas
    
    def __init__(self, color: str, blur: float, offsetX: float = 0.0, offsetY: float = 0.0):
        self.color = color
        self.blur = blur
        self.offsetX = offsetX
        self.offsetY = offsetY
    
    def __enter__(self):
        self.root.run_js_code(f"ctx.setShadow('{self.color}', {self.blur}, {self.offsetX}, {self.offsetY});", wait_execute=True)
    
    def __exit__(self, *_):
        graplib_webview.ctxRestore(wait_execute=True)
    
    enter = __enter__
    exit = __exit__
