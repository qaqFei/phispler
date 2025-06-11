# this module loads quickly

import math
import typing
import threading
import random
import struct
from os import listdir
from os.path import isfile, abspath

import const
import rpe_easing

def rotate_point(x, y, θ, r) -> tuple[float, float]:
    xo = r * math.cos(math.radians(θ))
    yo = r * math.sin(math.radians(θ))
    return x + xo, y + yo

def unpack_pos(number: int) -> tuple[int, int]:
    return (number - number % 1000) // 1000, number % 1000

def linear_interpolation(
    t: float,
    st: float, et: float,
    sv: float, ev: float
) -> float:
    if t == st: return sv
    return (t - st) / (et - st) * (ev - sv) + sv

def easing_interpolation(
    t: float,
    st: float, et: float,
    sv: float, ev: float,
    f: typing.Callable[[float], float]
):
    if t == st: return sv
    return f((t - st) / (et - st)) * (ev - sv) + sv

def is_intersect(
    line_1: tuple[
        tuple[float, float],
        tuple[float, float]
    ],
    line_2: tuple[
        tuple[float, float],
        tuple[float, float]
    ]
) -> bool:
    return not (
        max(line_1[0][0], line_1[1][0]) < min(line_2[0][0], line_2[1][0]) or
        max(line_2[0][0], line_2[1][0]) < min(line_1[0][0], line_1[1][0]) or
        max(line_1[0][1], line_1[1][1]) < min(line_2[0][1], line_2[1][1]) or
        max(line_2[0][1], line_2[1][1]) < min(line_1[0][1], line_1[1][1])
    )

def batch_is_intersect(
    lines_group_1: list[tuple[
        tuple[float, float],
        tuple[float, float]
    ]],
    lines_group_2: list[tuple[
        tuple[float, float],
        tuple[float, float]
    ]]
):
    for i in lines_group_1:
        for j in lines_group_2:
            yield is_intersect(i, j)

def pointInPolygon(ploygon: list[tuple[float, float]], point: tuple[float, float]):
    n = len(ploygon)
    j = n - 1
    res = False
    for i in range(n):
        if (
            (ploygon[i][1] > point[1]) != (ploygon[j][1] > point[1])
            and (
                point[0] < (
                    (ploygon[j][0] - ploygon[i][0])
                    * (point[1] - ploygon[i][1])
                    / (ploygon[j][1] - ploygon[i][1])
                    + ploygon[i][0]
                )
            )
        ):
            res = not res
        j = i
    return res

def getScreenRect(w: int, h: int):
    return [
        ((0, 0), (w, 0)), ((0, 0), (0, h)),
        ((w, 0), (w, h)), ((0, h), (w, h))
    ]

def getScreenPoints(w: int, h: int):
    return [(0, 0), (w, 0), (w, h), (0, h)]

def polygon2lines(p: list[tuple[float, float]]):
    return [(p[i], p[i + 1]) for i in range(-1, len(p) - 1)]

def polygonIntersect(p1: list[tuple[float, float]], p2: list[tuple[float, float]]):
    return (
        any(batch_is_intersect(polygon2lines(p1), polygon2lines(p2)))
        or any(pointInPolygon(p1, i) for i in p2)
        or any(pointInPolygon(p2, i) for i in p1)
    )

def linesInScreen(w: int, h: int, lines: list[tuple[float, float]]):
    return any(batch_is_intersect(
        lines, getScreenRect(w, h)
    )) or any(pointInScreen(j, w, h) for i in lines for j in i)

def polygonInScreen(w: int, h: int, polygon: list[tuple[float, float]]):
    return polygonIntersect(getScreenPoints(w, h), polygon)

def noteCanRender(
    w: int, h: int,
    note_max_size_half: float,
    x: float, y: float,
    hold_points: tuple[
        tuple[float, float],
        tuple[float, float],
        tuple[float, float],
        tuple[float, float]
    ] | None = None
) -> bool: # is type == hold, note_max_size_half is useless
    if hold_points is None: # type != hold
        lt = (x - note_max_size_half, y - note_max_size_half)
        rt = (x + note_max_size_half, y - note_max_size_half)
        rb = (x + note_max_size_half, y + note_max_size_half)
        lb = (x - note_max_size_half, y + note_max_size_half)
    else:
        lt, rt, rb, lb = hold_points
    
    return polygonInScreen(w, h, [lt, rt, rb, lb])

def lineInScreen(w: int|float, h: int|float, line: tuple[float]):
    return linesInScreen(w, h, [((*line[:2], ), (*line[2:], ), )])

def TextureLine_CanRender(
    w: int, h: int,
    texture_max_size_half: float,
    x: float, y: float
) -> bool:
    lt = (x - texture_max_size_half, y - texture_max_size_half)
    rt = (x + texture_max_size_half, y - texture_max_size_half)
    rb = (x + texture_max_size_half, y + texture_max_size_half)
    lb = (x - texture_max_size_half, y + texture_max_size_half)
    
    return polygonInScreen(w, h, [lt, rt, rb, lb])
    
def pointInScreen(point: tuple[float, float], w: int, h: int) -> bool:
    return 0 <= point[0] <= w and 0 <= point[1] <= h

def noteLineOutOfScreen(
    x: float, y: float,
    noteAtJudgeLinePos: tuple[float, float],
    fp: float,
    lineRotate: float,
    lineLength: float,
    lineToNoteRotate: float,
    w: int, h: int,
    note_max_size_half: float
):
    plpttdllotne_line = (
        *rotate_point(x, y, lineRotate, lineLength / 2),
        *rotate_point(x, y, lineRotate + 180, lineLength / 2)
    )
    
    plpttdllotne_cpoint_addfp = rotate_point(
        *noteAtJudgeLinePos,
        lineToNoteRotate,
        fp + 1.0 # add 1.0 px
    )
    
    moved_line = tuple(map(lambda x, y: x + y, plpttdllotne_line, (note_max_size_half, ) * 4))
    
    return (
        not lineInScreen(
            w + note_max_size_half * 2,
            h + note_max_size_half * 2,
            moved_line
        ) and (
            getLineLength(*plpttdllotne_cpoint_addfp, w / 2, h / 2)
            - getLineLength(x, y, w / 2, h / 2)
        ) > 0.0
    )

def runByThread(f, needjoin: bool = False):
    def wrapper(*args, **kwargs):
        t = threading.Thread(target=f, args=args, kwargs=kwargs, daemon=True)
        t.start()
        if needjoin: t.join()
    return wrapper

def conrpepos(pos: tuple[float, float]):
    return (
        (pos[0] + const.RPE_WIDTH / 2) / const.RPE_WIDTH,
        1.0 - (pos[1] + const.RPE_HEIGHT / 2) / const.RPE_HEIGHT
    )
        
def fmtTime(t: int|float) -> str:
    if t < 0.0: t = 0.0
    m, s = t // 60, t % 60
    m, s = int(m), int(s)
    return f"{m}:{s:>2}".replace(" ", "0")

def compute_intersection(
    x0: float, y0: float,
    x1: float, y1: float,
    x2: float, y2: float,
    x3: float, y3: float
):
    a1 = y1 - y0
    b1 = x0 - x1
    c1 = x1 * y0 - x0 * y1
    a2 = y3 - y2
    b2 = x2 - x3
    c2 = x3 * y2 - x2 * y3
    try:
        return (b2 * c1 - b1 * c2) / (a1 * b2 - a2 * b1), (a1 * c2 - a2 * c1) / (a1 * b2 - a2 * b1)
    except ZeroDivisionError:
        return x0, y0

def getDPower(width: float, height: float, deg: float):
    if width == 0.0: return 1.0
    sw = height / math.tan(math.radians(deg))
    return sw / width
    
    l1 = 0, 0, width, 0
    l2 = 0, height, *rotate_point(0, height, deg, (width ** 2 + height ** 2) ** 0.5)
    try:
        return compute_intersection(*l1, *l2)[0] / width
    except ZeroDivisionError:
        return 1.0

def getSizeByRect(rect: tuple[float, float, float, float]):
    return rect[2] - rect[0], rect[3] - rect[1]

def getCenterPointByRect(rect: tuple[float, float, float, float]):
    return (rect[0] + rect[2]) / 2, (rect[1] + rect[3]) / 2
    
def getAllFiles(path: str) -> list[str]:
    path = path.replace("\\", "/")
    if "/" in (path[-1], path[:-1]):
        path = path[:-1]
    files = []
    for item in listdir(path):
        item = item.replace("\\", "/")
        if isfile(f"{path}/{item}"):
            files.append(f"{path}/{item}")
        else:
            files.extend(getAllFiles(f"{path}/{item}"))
    return files

def getLineLength(x0: float, y0: float, x1: float, y1: float):
    return ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5

def gtpresp(p: str):
    result =  f"./phigros_assets/{p}".replace("\\", "/")
    while "//" in result: result = result.replace("//", "/")
    return result

def inrect(x: float, y: float, rect: tuple[float, float, float, float]) -> bool:
    return rect[0] <= x <= rect[2] and rect[1] <= y <= rect[3]

def indrect(x: float, y: float, rect: tuple[float, float, float, float], dpower: typing.Optional[float] = None):
    if rect[0] == rect[2] or rect[1] == rect[3]: return False
    
    if dpower is None:
        dpower = getDPower(*getSizeByRect(rect), 75)
        
    x += (1.0 - (y - rect[1]) / (rect[3] - rect[1])) * (dpower * (rect[2] - rect[0]))
    return inrect(x, y, rect)

def xxyy_rect2_xywh(rect: tuple[float, float, float, float]):
    return rect[0], rect[1], rect[2] - rect[0], rect[3] - rect[1]

def xywh_rect2_xxyy(rect: tuple[float, float, float, float]):
    return rect[0], rect[1], rect[0] + rect[2], rect[1] + rect[3]

def isfloatable(s: str):
    try: float(s); return True
    except: return False

def isallnum(lst: list[str], l: typing.Optional[int] = None):
    return (len(lst) >= l or l is None) and all(map(lambda x: isfloatable(x), lst))

def createBezierFunction(ps: list[float]) -> typing.Callable[[float], float]:
    f = lambda t: sum([ps[i] * (1 - t) ** (len(ps) - i - 1) * t ** i for i in range(len(ps))])
    setattr(f, "_ease_func_type", 1)
    setattr(f, "_ease_func_data", ps)
    return f

def createCuttingEasingFunction(f: typing.Callable[[float], float], l: float, r: float):
    if l > r:
        retf = lambda t: t
    else:
        s, e = f(l), f(r)
        retf = lambda t: (f(t * (r - l) + l) - s) / (e - s)
    
    setattr(retf, "_ease_func_type", 2)
    setattr(retf, "_ease_func_data", (f, (l, r)))
    return retf

def pec2rpe_findevent_bytime(es: list[dict], t: float, default: float):
    if not es: return default
    
    ets = list(map(lambda x: abs(x["endTime"][0] - t), es))
    return es[ets.index(min(ets))]["end"]

def pec2rpe(pec: str):
    errs = []
    peclines = pec.replace(" #", "\n#").replace(" &", "\n&").split("\n")
    result = { # if some key and value is not exists, in loading rpe chart, it will be set to default value.
        "META": {},
        "BPMList": [],
        "judgeLineList": [],
        "isPec": True
    }
    
    result["META"]["offset"] = float(peclines.pop(0)) - 150
    
    peclines = list(
        map(
            lambda x: list(filter(lambda x: x, x)),
            map(lambda x: x.split(" "), peclines)
        )
    )
    
    pecbpms = list(filter(lambda x: x and x[0] == "bp" and isallnum(x[1:], 2), peclines))
    pecnotes = list(filter(lambda x: x and x[0] in ("n1", "n2", "n3", "n4") and isallnum(x[1:], 5 if x[0] != "n2" else 6), peclines))
    pecnotespeeds = list(filter(lambda x: x and x[0] == "#" and isallnum(x[1:], 1), peclines))
    pecnotesizes = list(filter(lambda x: x and x[0] == "&" and isallnum(x[1:], 1), peclines))
    peccps = list(filter(lambda x: x and x[0] == "cp" and isallnum(x[1:], 4), peclines))
    peccds = list(filter(lambda x: x and x[0] == "cd" and isallnum(x[1:], 3), peclines))
    peccas = list(filter(lambda x: x and x[0] == "ca" and isallnum(x[1:], 3), peclines))
    peccvs = list(filter(lambda x: x and x[0] == "cv" and isallnum(x[1:], 3), peclines))
    peccms = list(filter(lambda x: x and x[0] == "cm" and isallnum(x[1:], 6), peclines))
    peccrs = list(filter(lambda x: x and x[0] == "cr" and isallnum(x[1:], 5), peclines))
    peccfs = list(filter(lambda x: x and x[0] == "cf" and isallnum(x[1:], 4), peclines))
    
    pecbpms.sort(key = lambda x: float(x[1]))
    
    notezip = list(zip(pecnotes, pecnotespeeds, pecnotesizes))
    notezip.sort(key = lambda x: float(x[0][2]))
    
    peccps.sort(key = lambda x: float(x[1]))
    peccds.sort(key = lambda x: float(x[1]))
    peccas.sort(key = lambda x: float(x[1]))
    peccvs.sort(key = lambda x: float(x[1]))
    peccms.sort(key = lambda x: float(x[1]))
    peccrs.sort(key = lambda x: float(x[1]))
    peccfs.sort(key = lambda x: float(x[1]))
    
    rpex = lambda x: (x / 2048 - 0.5) * const.RPE_WIDTH
    rpey = lambda y: (y / 1400 -  0.5) * const.RPE_HEIGHT
    rpes = lambda s: s / 1400 * const.RPE_HEIGHT
    lines = {}
    
    checkLine = lambda k: [
        (
            lines.update({k: {
                "eventLayers": [{
                    "speedEvents": [],
                    "moveXEvents": [],
                    "moveYEvents": [],
                    "rotateEvents": [],
                    "alphaEvents": []
                }],
                "notes": []
            }}),
            result["judgeLineList"].append(lines[k])
        ) if k not in lines else None,
    ]
    
    for e in pecbpms:
        try:
            result["BPMList"].append({
                "startTime": [float(e[1]), 0, 1],
                "bpm": float(e[2])
            })
        except Exception as e:
            errs.append(e)
    
    for e, sp, si in notezip:
        try:
            et = None
            if e[0] == "n2": et = [float(e.pop(3)), 0, 1]
            ntype = {"n1": 1, "n2": 2, "n3": 3, "n4": 4}[e[0]]
            k = int(e[1])
            st = [float(e[2]), 0, 1]
            x = float(e[3])
            if et is None: et = st.copy()
            above = int(e[4])
            fake = bool(int(e[5]))
            speed = float(sp[1])
            size = float(si[1])
            
            checkLine(k)
            lines[k]["notes"].append({
                "type": ntype,
                "startTime": st,
                "endTime": et,
                "positionX": x / 2048 * const.RPE_WIDTH,
                "above": above,
                "isFake": fake,
                "speed": speed,
                "size": size
            })
        except Exception as e:
            errs.append(e)
    
    for e in peccps:
        try:
            k = int(e[1])
            t = [float(e[2]), 0, 1]
            x = float(e[3])
            y = float(e[4])
            
            checkLine(k)
            lines[k]["eventLayers"][0]["moveXEvents"].append({
                "startTime": t, "endTime": t,
                "start": rpex(x), "end": rpex(x),
                "easingType": 1
            })
            lines[k]["eventLayers"][0]["moveYEvents"].append({
                "startTime": t, "endTime": t,
                "start": rpey(y), "end": rpey(y),
                "easingType": 1
            })
        except Exception as e:
            errs.append(e)

    for e in peccds:
        try:
            k = int(e[1])
            t = [float(e[2]), 0, 1]
            v = float(e[3])
            
            checkLine(k)
            lines[k]["eventLayers"][0]["rotateEvents"].append({
                "startTime": t, "endTime": t,
                "start": v, "end": v,
                "easingType": 1
            })
        except Exception as e:
            errs.append(e)
    
    for e in peccas:
        try:
            k = int(e[1])
            t = [float(e[2]), 0, 1]
            v = float(e[3])

            checkLine(k)
            lines[k]["eventLayers"][0]["alphaEvents"].append({
                "startTime": t, "endTime": t,
                "start": v, "end": v,
                "easingType": 1
            })
        except Exception as e:
            errs.append(e)
    
    for e in peccvs:
        try:
            k = int(e[1])
            t = [float(e[2]), 0, 1]
            v = float(e[3])

            checkLine(k)
            lines[k]["eventLayers"][0]["speedEvents"].append({
                "startTime": t, "endTime": t,
                "start": rpes(v), "end": rpes(v),
                "easingType": 1
            })
        except Exception as e:
            errs.append(e)
    
    for e in peccms:
        try:
            k = int(e[1])
            st = [float(e[2]), 0, 1]
            et = [float(e[3]), 0, 1]
            ex = float(e[4])
            ey = float(e[5])
            ease = int(e[6])
            
            checkLine(k)
            mxes = lines[k]["eventLayers"][0]["moveXEvents"]
            myes = lines[k]["eventLayers"][0]["moveYEvents"]
            sx = pec2rpe_findevent_bytime(mxes, st[0], rpex(ex))
            sy = pec2rpe_findevent_bytime(myes, st[0], rpey(ey))

            mxes.append({
                "startTime": st, "endTime": et,
                "start": sx, "end": rpex(ex),
                "easingType": ease
            })
            myes.append({
                "startTime": st, "endTime": et,
                "start": sy, "end": rpey(ey),
                "easingType": ease
            })
        except Exception as e:
            errs.append(e)
    
    for e in peccrs:
        try:
            k = int(e[1])
            st = [float(e[2]), 0, 1]
            et = [float(e[3]), 0, 1]
            ev = float(e[4])
            ease = int(e[5])

            checkLine(k)
            res = lines[k]["eventLayers"][0]["rotateEvents"]
            sv = pec2rpe_findevent_bytime(res, st[0], ev)

            res.append({
                "startTime": st, "endTime": et,
                "start": sv, "end": ev,
                "easingType": ease
            })
        except Exception as e:
            errs.append(e)
    
    for e in peccfs:
        try:
            k = int(e[1])
            st = [float(e[2]), 0, 1]
            et = [float(e[3]), 0, 1]
            ev = float(e[4])

            checkLine(k)
            aes = lines[k]["eventLayers"][0]["alphaEvents"]
            sv = pec2rpe_findevent_bytime(aes, st[0], ev)

            aes.append({
                "startTime": st, "endTime": et,
                "start": sv, "end": ev,
                "easingType": 1
            })
        except Exception as e:
            errs.append(e)
    
    return result, errs

def samefile(a: str, b: str):
    a, b = abspath(a), abspath(b)
    a, b = a.replace("\\", "/"), b.replace("\\", "/")
    while "//" in a: a = a.replace("//", "/")
    while "//" in b: b = b.replace("//", "/")
    return a == b

def findfileinlist(fn: str, lst: list[str]):
    for i, f in enumerate(lst):
        if samefile(fn, f):
            return i
    return None

def fileinlist(fn: str, lst: list[str]):
    return findfileinlist(fn, lst) is not None

timeoutMap = {}
def setTimeout(func: typing.Callable, wait: float):
    toid = random.randint(0, 2 << 31)
    cancel = False
    
    def f():
        if cancel: return
        func()
        try: timeoutMap.pop(toid)
        except: pass
    
    def doc():
        nonlocal cancel
        cancel = True
    
    threading.Timer(wait, f).start()
    timeoutMap[toid] = doc
    return toid

def clearTimeout(toid: int):
    if toid in timeoutMap:
        timeoutMap[toid]()

def debounce(wait: float):
    def decorator(func: typing.Callable):
        def warpper(*args, **kwargs):
            clearTimeout(warpper.toid)
            warpper.toid = setTimeout(lambda: func(*args, **kwargs), wait)
        
        warpper.toid = None
        
        return warpper
    
    return decorator

def getCoverSize(imw: int, imh: int, w: int, h: int):
    im_ratio = imw / imh
    ratio = w / h

    if ratio > im_ratio:
        return w, w / im_ratio
    else:
        return im_ratio * h, h

def getPosFromCoverSize(w: float, h: float, rectw: float, recth: float):
    return (rectw - w) / 2, (recth - h) / 2

class ByteWriter:
    def __init__(self):
        self.data = bytearray()

    def write(self, data: bytes|bytearray):
        self.data.extend(data)
    
    def writeChar(self, data: int):
        self.write(struct.pack("<b", data))
    
    def writeInt(self, data: int):
        self.write(struct.pack("<i", data))
    
    def writeULong(self, data: int):
        self.write(struct.pack("<Q", data))

    def writeFloat(self, data: float):
        self.write(struct.pack("<f", data))
    
    def writeBool(self, data: bool):
        self.write(struct.pack("<?", data))
    
    def writeString(self, data: str):
        self.writeBytes(data.encode("utf-8"))
    
    def writeBytes(self, data: bytes|bytearray):
        self.writeInt(len(data))
        self.write(data)
    
    def writeEaseFunc(self, f: typing.Callable[[float], float]):
        t = getattr(f, "_ease_func_type", 0)
        self.writeChar(t)
        
        if t == 0:
            self.writeChar(rpe_easing.ease_funcs.index(f))
        elif t == 1:
            d = getattr(f, "_ease_func_data")
            self.writeInt(len(d))
            for i in d: self.writeFloat(i)
        elif t == 2:
            d = getattr(f, "_ease_func_data")
            self.writeEaseFunc(d[0])
            self.writeFloat(d[1][0])
            self.writeFloat(d[1][1])
        else:
            assert False, "Invalid ease func type"
    
    def writeOptionalShort(self, data: typing.Optional[int]):
        self.writeBool(data is not None)
        if data is not None:
            self.writeChar(data)
    
    def writeOptionalInt(self, data: typing.Optional[int]):
        self.writeBool(data is not None)
        if data is not None:
            self.writeInt(data)

    def writeOptionalFloat(self, data: typing.Optional[float]):
        self.writeBool(data is not None)
        if data is not None:
            self.writeFloat(data)

    def writeOptionalBool(self, data: typing.Optional[bool]):
        self.writeBool(data is not None)
        if data is not None:
            self.writeBool(data)

    def writeOptionalString(self, data: typing.Optional[str]):
        self.writeBool(data is not None)
        if data is not None:
            self.writeString(data)

    def writeOptionalBytes(self, data: typing.Optional[bytes|bytearray]):
        self.writeBool(data is not None)
        if data is not None:
            self.writeBytes(data)
    
    def getData(self):
        return self.data

class ByteReader:
    def __init__(self, data: bytes|bytearray):
        self.data = data
        self.pos = 0

    def read(self, length: int):
        data = self.data[self.pos:self.pos + length]
        self.pos += length
        return data
    
    def seek(self, offset: int, whence: int = 0):
        if whence == 0:
            self.pos = offset
        elif whence == 1:
            self.pos += offset
        elif whence == 2:
            self.pos = len(self.data) + offset
        else:
            raise ValueError("Invalid whence")
    
    def readChar(self):
        return struct.unpack("<b", self.read(1))[0]
    
    def readInt(self):
        return struct.unpack("<i", self.read(4))[0]

    def readUInt(self):
        return struct.unpack("<I", self.read(4))[0]
    
    def readULong(self):
        return struct.unpack("<Q", self.read(8))[0]
    
    def readFloat(self):
        return struct.unpack("<f", self.read(4))[0]

    def readBool(self):
        return struct.unpack("<?", self.read(1))[0]

    def readString(self):
        return self.readBytes().decode("utf-8")

    def readBytes(self):
        length = self.readInt()
        return self.read(length)

    def readEaseFunc(self):
        t = self.readChar()
        
        if t == 0:
            return rpe_easing.ease_funcs[self.readChar()]
        elif t == 1:
            d = [self.readFloat() for _ in range(self.readInt())]
            return createBezierFunction(d)
        elif t == 2:
            f = self.readEaseFunc()
            p = (self.readFloat(), self.readFloat())
            return createCuttingEasingFunction(f, *p)
        else:
            raise ValueError("Invalid ease func type")

    def readOptionalShort(self):
        return self.readChar() if self.readBool() else None

    def readOptionalInt(self):
        return self.readInt() if self.readBool() else None

    def readOptionalFloat(self):
        return self.readFloat() if self.readBool() else None

    def readOptionalBool(self):
        return self.readBool() if self.readBool() else None

    def readOptionalString(self):
        return self.readString() if self.readBool() else None

    def readOptionalBytes(self):
        return self.readBytes() if self.readBool() else None

def unfold_list(data: list[list]):
    result = []
    for i in data:
        if isinstance(i, list):
            result.extend(unfold_list(i))
        else:
            result.append(i)
    return result

ValueEventT = typing.TypeVar("ValueEventT")
class ValueEvent(typing.Generic[ValueEventT]):
    def __init__(self):
        self.e = threading.Event()
    
    def set(self, value: ValueEventT):
        self.value = value
        self.e.set()

    def wait(self) -> ValueEventT:
        self.e.wait()
        return self.value

class ThreadLockFuncType(typing.Protocol, typing.Callable):
    lock: threading.Lock

def thread_lock_func(func: typing.Optional[typing.Callable] = None, lock: typing.Optional[threading.Lock] = None):
    if lock is None:
        lock = threading.Lock()
        
    if func is not None:
        def wrapper(*args, **kwargs):
            with lock:
                return func(*args, **kwargs)
        
        wrapper.lock = lock
        wrapper: ThreadLockFuncType = wrapper
        return wrapper
    else:
        def decorator(func: typing.Callable):
            return thread_lock_func(func, lock)

        return decorator

IterRemovableListT = typing.TypeVar("IterRemovableListT")

class Node(typing.Generic[IterRemovableListT]):
    __slots__ = ("value", "prev", "next")
    def __init__(self, value: IterRemovableListT):
        self.value = value
        self.prev: typing.Optional[Node[IterRemovableListT]] = None
        self.next: typing.Optional[Node[IterRemovableListT]] = None

class IterRemovableList(typing.Generic[IterRemovableListT]):
    def __init__(self, lst: list[IterRemovableListT]):
        self.head: typing.Optional[Node[IterRemovableListT]] = None
        self.tail: typing.Optional[Node[IterRemovableListT]] = None
        self._build_linked_list(lst)
        self.current: typing.Optional[Node[IterRemovableListT]] = None

    def _build_linked_list(self, lst: list[IterRemovableListT]) -> None:
        prev_node = None
        for item in lst:
            new_node = Node(item)
            if not self.head:
                self.head = new_node
            if prev_node:
                prev_node.next = new_node
                new_node.prev = prev_node
            prev_node = new_node
        self.tail = prev_node

    def __iter__(self) -> typing.Iterator[tuple[IterRemovableListT, typing.Callable[[], None]]]:
        self.current = self.head
        return self

    def __next__(self) -> tuple[IterRemovableListT, typing.Callable[[], None]]:
        if self.current is None:
            raise StopIteration
        
        current_node = self.current
        self.current = current_node.next
        
        def remove_callback() -> None:
            prev_node = current_node.prev
            next_node = current_node.next
            
            if prev_node:
                prev_node.next = next_node
            else:
                self.head = next_node
            
            if next_node:
                next_node.prev = prev_node
            else:
                self.tail = prev_node
        
        return current_node.value, remove_callback

def UnityCurve(curves: list[dict], t: float):
    if not curves: return 0
    
    curves = sorted(curves, key=lambda x: x["time"])
    
    if t <= curves[0]["time"]: return curves[0]["value"]
    if t >= curves[-1]["time"]: return curves[-1]["value"]
    
    for i in range(len(curves) - 1):
        c = curves[i]
        if c["time"] <= t <= curves[i + 1]["time"]:
            left = i
            break
    
    k0 = curves[left]
    k1 = curves[left + 1]
    dt = k1["time"] - k0["time"]
    tNorm = 0 if dt == 0 else (t - k0["time"]) / dt # 归一化时间参数
    
    # 三次埃尔米特基函数
    t2 = tNorm ** 2
    t3 = t2 * tNorm
    h00 = 2 * t3 - 3 * t2 + 1
    h10 = t3 - 2 * t2 + tNorm
    h01 = -2 * t3 + 3 * t2
    h11 = t3 - t2
    
    # 实际影响的斜率
    m0 = 3 * k0["outSlope"] * k0["outWeight"] # 出方向加权斜率
    m1 = 3 * k1["inSlope"] * k1["inWeight"]   # 入方向加权斜率
    
    return (
        h00 * k0["value"] +
        h10 * m0 +        # 不再需要乘以dt
        h01 * k1["value"] +
        h11 * m1
    )

def nums_interp(nums1: typing.Iterable[float], nums2: typing.Iterable[float], p: float) -> map:
    return map(lambda x1, x2: x1 + (x2 - x1) * p, nums1, nums2)
