from __future__ import annotations

import typing
import logging
import math
import random
import dataclasses

import const
import rpe_easing
import utils
import tempdir

type eventValueType = float|str|tuple[float, float, float]

initialized_events: dict[int, int] = {}

getpos_cache: dict[int, tuple[float, float]] = {}
last_getpos_cache_time = -float("inf")

getev_cachei: dict[int, int] = {}
last_getev_cachei_time = -float("inf")

def check_getpos_cache(t: float):
    global last_getpos_cache_time
    
    if last_getpos_cache_time != t:
        last_getpos_cache_time = t
        getpos_cache.clear()

def _init_events(es: list[LineEvent], *, is_speed: bool = False, is_text: bool = False, default: eventValueType = 0.0):
    if not es: return
    
    es_hash = hash((hash((
        e.startTime,
        e.endTime,
        e.start,
        e.end,
        e.isFill
    )) for e in es))
    
    if id(es) in initialized_events and initialized_events[id(es)] == es_hash:
        return
    
    initialized_events[id(es)] = es_hash
    
    es.sort(key = lambda e: e.startTime)
    
    aes = []
    for i, e in enumerate(es):
        if i != len(es) - 1:
            ne = es[i + 1]
            if e.endTime < ne.startTime:
                aes.append(LineEvent(
                    startTime = e.endTime,
                    endTime = ne.startTime,
                    start = e.end,
                    end = e.end,
                    isFill = True
                ))
            elif e.endTime > ne.startTime:
                logging.warning(f"Event overlap: {e} {ne}")
    
    es.extend(aes)
    es.sort(key = lambda e: e.startTime)
    es.append(LineEvent(
        startTime = es[-1].endTime,
        endTime = es[-1].endTime + const.INFBEAT,
        start = es[-1].end,
        end = es[-1].end,
        isFill = True
    ))
    
    es.insert(0, LineEvent(
        startTime = -const.INFBEAT,
        endTime = es[0].startTime,
        start = default,
        end = default,
        isFill = True
    ))
    
    if not is_text:
        for i, e in enumerate(es):
            if i != 0 and es[i - 1].end == e.start and e.start == e.end:
                e.isFill = True
    
    if is_speed:
        fp = 0.0
        for e in es:
            e.floorPosotion = fp
            fp += (e.start + e.end) * (e.endTime - e.startTime) / 2

def findevent(es: list[LineEvent], t: float) -> tuple[typing.Optional[LineEvent], int]:
    if not es:
        return (None, 0)
    
    l, r = 0, len(es) - 1
    
    while l <= r:
        m = (l + r) // 2
        e = es[m]
        st, et = e.startTime, e.endTime
        if st <= t < et: return (e, m)
        elif st > t: r = m - 1
        else: l = m + 1
    
    i = (len(es) - 1) if t >= es[-1].endTime else 0
    return es[i], i

def split_notes(notes: list[Note]) -> list[utils.IterRemovableList[Note]]:
    tempmap: dict[int, list[Note]] = {}
    
    for n in notes:
        h = hash((n.speed, n.yOffset, n.isAbove))
        if h not in tempmap: tempmap[h] = []
        tempmap[h].append(n)
    
    return list(map(utils.IterRemovableList, tempmap.values()))

def _beat2num(beat: list[int]):
    return beat[0] + beat[1] / beat[2]
    
def geteasing_func(t: int):
    try:
        if not isinstance(t, int): t = 1
        t = 1 if t < 1 else (len(rpe_easing.ease_funcs) if t > len(rpe_easing.ease_funcs) else t)
        return rpe_easing.ease_funcs[int(t) - 1]
    except Exception as e:
        logging.warning(f"geteasing_func error: {e}")
        return rpe_easing.ease_funcs[0]
            
class ChartFormat:
    unset = -1
    phi = 1
    rpe = 2
    
    notetype_map: dict[object, dict[int, int]] = {
        phi: {1: 1, 2: 2, 3: 3, 4: 4}, # standard
        rpe: {1: 1, 2: 3, 3: 4, 4: 2}
    }
    
    @staticmethod
    def load_phi(data: dict):
        def _time_coverter(json_line: dict, t: float):
            return t * (1.875 / json_line.get("bpm", 140.0))
        
        def _pos_coverter_x(x: float):
            return x * const.PGR_UW
        
        def _pos_coverter_y(y: float):
            return y * const.PGR_UH
        
        def _put_note(*, json_line: dict, line: JudgeLine, json_note: dict, isAbove: bool):
            if not isinstance(json_note, dict):
                logging.warning(f"Invalid note type: {type(json_note)}")
                return
            
            note_type = ChartFormat.notetype_map[result.type].get(json_note.get("type", 1), const.NOTE_TYPE.TAP)
            speed = json_note.get("speed", 0.0)
            
            note = Note(
                type = note_type,
                time = _time_coverter(json_line, json_note.get("time", 0.0)),
                holdTime = _time_coverter(json_line, json_note.get("holdTime", 0.0)),
                positionX = _pos_coverter_x(json_note.get("positionX", 0.0)),
                speed = _pos_coverter_y(speed) if note_type == const.NOTE_TYPE.HOLD else speed,
                isAbove = isAbove
            )
            
            line.notes.append(note)
        
        def _put_events(es: list[LineEvent], json_es: list[dict], converter: typing.Callable[[float], float], startkey: str = "start", endkey: str = "end"):
            for json_e in json_es:
                if not isinstance(json_e, dict):
                    logging.warning(f"Invalid event type: {type(json_e)}")
                    continue
                
                es.append(LineEvent(
                    startTime = _time_coverter(json_line, json_e.get("startTime", 0.0)),
                    endTime = _time_coverter(json_line, json_e.get("endTime", 0.0)),
                    start = converter(json_e.get(startkey, 0.0)),
                    end = converter(json_e.get(endkey, 0.0))
                ))
        
        formatVersion = data.get("formatVersion", 0)
        if formatVersion not in (1, 3):
            logging.warning(f"Unsupported phi chart format version: {formatVersion}")
            formatVersion = 3
        
        result = CommonChart()
        result.type = ChartFormat.phi
        
        result.offset = data.get("offset", 0.0)
        result.options.lineWidthUnit = (0.0, 5.76)
        result.options.lineHeightUnit = (0.0, const.LINEWIDTH.PHI)
        
        for line_i, json_line in enumerate(data.get("judgeLineList", [])):
            json_line: dict
            
            line = JudgeLine()
            line.index = line_i
            line.bpms.append(BPMEvent(0.0, json_line.get("bpm", 140.0)))
            
            for i, json_note in enumerate(json_line.get("notesAbove", [])):
                _put_note(
                    json_line = json_line,
                    line = line,
                    json_note = json_note,
                    isAbove = True
                )
                line.notes[-1].masterIndex = i
            
            for i, json_note in enumerate(json_line.get("notesBelow", [])):
                _put_note(
                    json_line = json_line,
                    line = line,
                    json_note = json_note,
                    isAbove = False
                )
                line.notes[-1].masterIndex = i
            
            if formatVersion == 1:
                for json_e in json_line.get("judgeLineMoveEvents", []):
                    json_e: dict
                    
                    json_e["start"], json_e["start2"] = utils.unpack_pos(json_e.get("start", 0))
                    json_e["end"], json_e["end2"] = utils.unpack_pos(json_e.get("end", 0))
            
            elayer = EventLayerItem()
            _put_events(elayer.alphaEvents, json_line.get("judgeLineDisappearEvents", []), lambda x: x)
            _put_events(elayer.moveXEvents, json_line.get("judgeLineMoveEvents", []), lambda x: x)
            _put_events(elayer.moveYEvents, json_line.get("judgeLineMoveEvents", []), lambda y: 1.0 - y, "start2", "end2")
            _put_events(elayer.rotateEvents, json_line.get("judgeLineRotateEvents", []), lambda r: -r)
            _put_events(elayer.speedEvents, json_line.get("speedEvents", []), _pos_coverter_y, "value", "value")
            line.eventLayers.append(elayer)
            
            result.lines.append(line)

        result.init()
        return result
    
    @staticmethod
    def load_rpe(data: dict):
        def _beat2sec(line: JudgeLine, beat: list[int, int, int]):
            return line.beat2sec(_beat2num(beat))
        
        def _pos_converter_x(x: float):
            return (x + const.RPE_WIDTH / 2) / const.RPE_WIDTH
        
        def _pos_converter_y(y: float):
            return 1.0 - (y + const.RPE_HEIGHT / 2) / const.RPE_HEIGHT
        
        def _converter_x(x: float):
            return x / const.RPE_WIDTH

        def _converter_y(y: float):
            return y / const.RPE_HEIGHT
        
        is_pec = data.get("isPec", False)
        rpe_meta: dict = data.get("META", {})
        
        result = CommonChart()
        result.type = ChartFormat.rpe
        
        result.offset = rpe_meta.get("offset", 0.0) / 1000
        
        result.options.alwaysLineOpenAnimation = False
        
        if not is_pec:
            result.options.holdCoverAtHead = False
            
        result.options.holdIndependentSpeed = False
        result.options.lineWidthUnit = (4000 / 1350, 0.0)
        result.options.lineHeightUnit = (0.0, const.LINEWIDTH.RPE)
        
        result.options.res_ext_song = rpe_meta.get("song", "")
        result.options.res_ext_background = rpe_meta.get("background", "")
        
        result.options.meta_ext_name = rpe_meta.get("name", "UK")
        result.options.meta_ext_composer = rpe_meta.get("composer", "UK")
        result.options.meta_ext_level = rpe_meta.get("level", "UK")
        result.options.meta_ext_charter = rpe_meta.get("charter", "UK")
    
        def _put_events(es: list[LineEvent], json_es: list[dict], converter: typing.Callable[[eventValueType], eventValueType] = lambda x: x, default: eventValueType = 0.0):
            for json_e in json_es:
                if not isinstance(json_e, dict):
                    logging.warning(f"Unsupported event type: {type(json_e)}")
                    continue
                
                easingType = json_e.get("easingType", 1)
                bezier = json_e.get("bezier", False)
                bezierPoints = json_e.get("bezierPoints", [0.0])
                easingFunc = geteasing_func(easingType) if not bezier else utils.createBezierFunction(bezierPoints)
                easingLeft = max(0.0, min(1.0, json_e.get("easingLeft", 0.0)))
                easingRight = max(0.0, min(1.0, json_e.get("easingRight", 1.0)))
                
                if easingLeft != 0.0 or easingRight != 1.0:
                    easingFunc = utils.createCuttingEasingFunction(easingFunc, easingLeft, easingRight)
            
                es.append(LineEvent(
                    startTime = _beat2sec(line, json_e.get("startTime", [0, 0, 1])),
                    endTime = _beat2sec(line, json_e.get("endTime", [0, 0, 1])),
                    start = converter(json_e.get("start", default)),
                    end = converter(json_e.get("end", default)),
                    ease = easingFunc
                ))

        def _create_bpm_list(bpmfactor: float = 1.0):
            result = []
            
            for bpm_json in data.get("BPMList", []):
                bpm_json: dict
                
                result.append(BPMEvent(
                    _beat2num(bpm_json.get("startTime", [0, 0, 1])),
                    bpm_json.get("bpm", 140.0) / bpmfactor
                ))
            
            return result
        
        result.options.globalBpmList = _create_bpm_list()
        
        for line_i, json_line in enumerate(data.get("judgeLineList", [])):
            json_line: dict

            line = JudgeLine()
            line.index = line_i
            
            texture = json_line.get("Texture", "line.png")
            if texture != "line.png":
                line.isTextureLine = True
                line.texture = texture
            
            if json_line.get("isGif", False):
                line.isGifLine = True
            
            attachUI = json_line.get("attachUI", None)
            if attachUI is not None:
                line.isAttachUI = True
                line.attachUI = attachUI
            
            line.father = json_line.get("father", -1)
            line.zOrder = json_line.get("zOrder", 0)
            line.enableCover = json_line.get("isCover", 1) == 1
            
            line.bpms.extend(_create_bpm_list(json_line.get("bpmfactor", 1.0)))
            
            for i, json_note in enumerate(json_line.get("notes", [])):
                if not isinstance(json_note, dict):
                    logging.warning(f"Unsupported note type: {type(json_note)}")
                    continue
                
                note_type = ChartFormat.notetype_map[result.type].get(json_note.get("type", 1), const.NOTE_TYPE.TAP)
                note_start_time = _beat2sec(line, json_note.get("startTime", [0, 0, 1]))
                note_end_time = _beat2sec(line, json_note.get("endTime", [0, 0, 1]))
                
                note = Note(
                    type = note_type,
                    time = note_start_time,
                    holdTime = note_end_time - note_start_time,
                    positionX = _converter_x(json_note.get("positionX", 0.0)),
                    speed = json_note.get("speed", 1.0),
                    isAbove = json_note.get("above", 1) == 1,
                    isFake = json_note.get("isFake", 0) == 1,
                    yOffset = _converter_y(json_note.get("yOffset", 0.0)),
                    visibleTime = json_note.get("visibleTime", None),
                    width = json_note.get("size", 1.0),
                    alpha = json_note.get("alpha", 255.0) / 255.0,
                    hitsound = json_note.get("hitsound", None),
                )
                
                note.masterIndex = i
                line.notes.append(note)
            
            for el_json in json_line.get("eventLayers", []):
                if el_json is None:
                    continue
                
                el_json: dict
                elayer = EventLayerItem()
                _put_events(elayer.alphaEvents, el_json.get("alphaEvents", []), lambda a: a / 255.0)
                _put_events(elayer.moveXEvents, el_json.get("moveXEvents", []))
                _put_events(elayer.moveYEvents, el_json.get("moveYEvents", []))
                _put_events(elayer.rotateEvents, el_json.get("rotateEvents", []))
                _put_events(elayer.speedEvents, el_json.get("speedEvents", []), lambda x: x * 120 / const.RPE_HEIGHT)
                line.eventLayers.append(elayer)
            
            extended = json_line.get("extended", None)
            if extended is not None:
                _put_events(line.extendEvents.colorEvents, extended.get("colorEvents", []), tuple, (255, 255, 255))
                _put_events(line.extendEvents.scaleXEvents, extended.get("scaleXEvents", []), default=1.0)
                _put_events(line.extendEvents.scaleYEvents, extended.get("scaleYEvents", []), default=1.0)
                _put_events(line.extendEvents.textEvents, extended.get("textEvents", []), default="")
                _put_events(line.extendEvents.gifEvents, extended.get("gifEvents", []), default=10.0)
            
            result.lines.append(line)

        result.init()
        return result
    
    @staticmethod
    def load_pec(data: str):
        return ChartFormat.load_rpe(utils.pec2rpe(data))
    
    @staticmethod
    def get_type_string(t: int):
        return {
            getattr(ChartFormat, k): k
            for k in ("unset", "phi", "rpe")
        }[t]

@dataclasses.dataclass
class Note:
    type: int = const.NOTE_TYPE.TAP
    time: float = 0.0
    holdTime: float = 0.0
    positionX: float = 0.0
    speed: float = 1.0
    
    isAbove: bool = True
    isFake: bool = False
    yOffset: float = 0.0
    visibleTime: typing.Optional[float] = None
    width: float = 1.0
    alpha: float = 1.0
    hitsound: typing.Optional[str] = None
    
    alwaysHasHoldHead: typing.Optional[bool] = None
    
    def __post_init__(self):
        self.ishold = self.type == const.NOTE_TYPE.HOLD
        self.morebets = False
        self.holdEndTime = self.time + self.holdTime
        self.giveComboTime = self.time if not self.ishold else max(self.time, self.holdEndTime - 0.2)
        self.hitsound_reskey = self.type if self.hitsound is None else hash(tuple(map(ord, self.hitsound)))
        self.type_string = const.TYPE_STRING_MAP[self.type]
        self.rotate_add = 0 if self.isAbove else 180
        self.draworder = const.NOTE_RORDER_MAP[self.type]
        
        if not hasattr(self, "masterIndex"):
            self.masterIndex = -1
            
        self.nowpos = (0.0, 0.0)
        self.nowrotate = 0.0
        
        self.state: int = const.NOTE_STATE.MISS
        self.player_clicked: bool = False
        self.player_click_offset: float = 0.0
        self.player_click_sound_played: bool = False
        self.player_will_click: bool = False
        self.player_missed: bool = False
        self.player_badtime: float = float("nan")
        self.player_holdmiss_time: float = float("inf")
        self.player_last_testholdismiss_time: float = -float("inf")
        self.player_holdjudged: bool = False
        self.player_holdclickstate: int = const.NOTE_STATE.MISS
        self.player_holdjudged_tomanager: bool = False
        self.player_holdjudge_tomanager_time: float = float("nan")
        self.player_judge_safe_used: bool = False
        self.player_bad_posandrotate: typing.Optional[tuple[tuple[float, float], float]] = None
   
    def init(self, master: JudgeLine):
        self.isontime = False
        
        self.master = master
        self.floorPosition = self.master.getFloorPosition(self.time)
        self.holdLength = (
            self.master.getRangeFloorPosition(self.time, self.time + self.holdTime)
            if not self.master.master.options.holdIndependentSpeed
            else self.holdTime * self.speed
        ) if self.ishold else 0.0
        
        dub_text = "_dub" if self.morebets else ""
        if not self.ishold:
            self.img_keyname = f"{self.type_string}{dub_text}"
            self.imgname = f"Note_{self.img_keyname}"
        else:
            self.img_keyname = f"{self.type_string}_Head{dub_text}"
            self.imgname = f"Note_{self.img_keyname}"
            
            self.img_body_keyname = f"{self.type_string}_Body{dub_text}"
            self.imgname_body = f"Note_{self.img_body_keyname}"
            
            self.img_end_keyname = f"{self.type_string}_End{dub_text}"
            self.imgname_end = f"Note_{self.img_end_keyname}"
        
        self.effect_times = []
        self.effect_times.append((
            self.time,
            utils.newRandomBlocks(),
            self.getNoteClickPos(self.time)
        ))
        
        if self.ishold:
            t = self.time
            while t <= self.holdEndTime:
                t += 1 / self.master.getBpm(self.time) * 30
                if t > self.holdEndTime: break
                
                self.effect_times.append((
                    t,
                    utils.newRandomBlocks(),
                    self.getNoteClickPos(t)
                ))
        
        self.player_effect_times = self.effect_times.copy()
    
    def fast_init(self):
        self.isontime = False
    
    def getNoteClickPos(self, time: float) -> tuple[typing.Callable[[int, int], tuple[float, float]], float]:
        linePos = self.master.master.options.posConverter(self.master.getPos(time))
        lineRotate = sum(self.master.getEventsValue(el.rotateEvents, time) for el in self.master.eventLayers)
        
        cached: bool = False
        cachedata: typing.Optional[tuple[float, float]] = None
        
        def callback(w: int, h: int):
            nonlocal cached, cachedata
            
            if cached: return cachedata
            cached, cachedata = True, utils.rotate_point(
                linePos[0] * w, linePos[1] * h,
                lineRotate, self.positionX * w
            )
            
            return cachedata
        
        return callback, lineRotate

@dataclasses.dataclass
class LineEvent:
    startTime: float = 0.0
    endTime: float = 0.0
    start: eventValueType = 0.0
    end: eventValueType = 0.0
    ease: typing.Callable[[float], float] = rpe_easing.ease_funcs[0]
    
    isFill: bool = False
    floorPosotion: typing.Optional[float] = None # only for speed event
    
    def __post_init__(self):
        if isinstance(self.start, int|float):
            self.get = lambda t: utils.easing_interpolation(t, self.startTime, self.endTime, self.start, self.end, self.ease)
        elif isinstance(self.start, str):
            self.get = lambda t: utils.rpe_text_tween(self.start, self.end, utils.easing_interpolation(t, 0.0, 1.0, 0.0, 1.0, self.ease), self.isFill)
        elif isinstance(self.start, typing.Iterable):
            self.get = lambda t: tuple(utils.easing_interpolation(t, self.startTime, self.endTime, self.start[i], self.end[i], self.ease) for i in range(len(self.start)))
        else:
            raise ValueError(f"Invalid event value type: {type(self.start)}")
    
    def speed_get(self, t: float):
        return (t - self.startTime) * (self.start + self.get(t)) / 2

@dataclasses.dataclass
class EventLayerItem:
    alphaEvents: list[LineEvent] = dataclasses.field(default_factory=list)
    moveXEvents: list[LineEvent] = dataclasses.field(default_factory=list)
    moveYEvents: list[LineEvent] = dataclasses.field(default_factory=list)
    rotateEvents: list[LineEvent] = dataclasses.field(default_factory=list)
    speedEvents: list[LineEvent] = dataclasses.field(default_factory=list)
    
    def init(self):
        _init_events(self.alphaEvents)
        _init_events(self.moveXEvents)
        _init_events(self.moveYEvents)
        _init_events(self.rotateEvents)
        _init_events(self.speedEvents, is_speed=True)

@dataclasses.dataclass
class ExtendEventsItem:
    colorEvents: list[LineEvent] = dataclasses.field(default_factory=list)
    scaleXEvents: list[LineEvent] = dataclasses.field(default_factory=list)
    scaleYEvents: list[LineEvent] = dataclasses.field(default_factory=list)
    textEvents: list[LineEvent] = dataclasses.field(default_factory=list)
    gifEvents: list[LineEvent] = dataclasses.field(default_factory=list)
    
    def init(self):
        _init_events(self.colorEvents, default=(255, 255, 255))
        _init_events(self.scaleXEvents, default=1.0)
        _init_events(self.scaleYEvents, default=1.0)
        _init_events(self.textEvents, is_text=True, default="")
        _init_events(self.gifEvents, is_speed=True)

@dataclasses.dataclass
class BPMEvent:
    time: float = 0.0
    bpm: float = 140.0

@dataclasses.dataclass
class JudgeLine:
    bpms: list[BPMEvent] = dataclasses.field(default_factory=list)
    notes: list[Note] = dataclasses.field(default_factory=list)
    eventLayers: list[EventLayerItem] = dataclasses.field(default_factory=list)
    extendEvents: ExtendEventsItem = dataclasses.field(default_factory=ExtendEventsItem)
    father: typing.Optional[int] = None
    zOrder: int = 0
    
    isTextureLine: bool = False
    isGifLine: bool = False
    texture: typing.Optional[str] = None
    
    isAttachUI: bool = False
    attachUI: typing.Optional[str] = None
    
    enableCover: bool = True
    
    def __post_init__(self):
        self.playingFloorPosition = 0.0
        self.index = -1
    
    def preinit(self, master: CommonChart):
        self.master = master
        
        if self.father == -1:
            self.father = None
        
        self.fatherLine: JudgeLine = master.lines[self.father] if self.father is not None else None
            
        self.notes.sort(key=lambda note: note.time)
        
        for el in self.eventLayers:
            el.init()
        
        self.extendEvents.init()
    
    def init_notegroups(self):
        self.renderNotes = split_notes(self.notes)
        self.effectNotes = utils.IterRemovableList([i for i in self.notes if not i.isFake])
    
    def init(self):
        for note in self.notes:
            note.init(self)
            
        self.init_notegroups()
    
    def fast_init(self):
        self.preinit(self.master)
        
        for note in self.notes:
            note.fast_init()

        self.init_notegroups()
        
    def getFloorPosition(self, t: float):
        fp = 0.0
        
        for el in self.eventLayers:
            e, _ = findevent(el.speedEvents, t)
            if e is not None:
                fp += e.floorPosotion + e.speed_get(t)
        
        return fp
    
    def getRangeFloorPosition(self, s: float, e: float):
        return self.getFloorPosition(e) - self.getFloorPosition(s)

    def getEventsValue(self, es: list[LineEvent], t: float, default: eventValueType = 0.0):
        global last_getev_cachei_time
        
        if not es:
            return default
        
        esid = id(es)
        
        if last_getev_cachei_time > t:
            getev_cachei.clear()
        
        if (i := getev_cachei.get(esid)) is None:
            e, i = findevent(es, t)
        else:
            while not es[i].startTime <= t <= es[i].endTime:
                i += 1
            
            e = es[i]
            
        getev_cachei[esid] = i
        last_getev_cachei_time = t
        return e.get(t)
    
    def getPos(self, t: float):
        check_getpos_cache(t)
        
        if (linePos := getpos_cache.get(id(self))) is not None:
            return linePos
        
        linePos = (
            sum(self.getEventsValue(el.moveXEvents, t) for el in self.eventLayers),
            sum(self.getEventsValue(el.moveYEvents, t) for el in self.eventLayers)
        )
        
        if self.fatherLine is not None:
            fatherPos = self.fatherLine.getPos(t)
            fatherRotate = sum(self.fatherLine.getEventsValue(el.rotateEvents, t) for el in self.fatherLine.eventLayers)
            
            if fatherRotate % 360 == 0.0:
                return list(map(lambda v1, v2: v1 + v2, fatherPos, linePos))
            
            return list(map(lambda v1, v2: v1 + v2, fatherPos,
                utils.rotate_point(
                    0.0, 0.0,
                    90 - (math.degrees(math.atan2(*linePos)) + fatherRotate),
                    utils.getLineLength(*linePos, 0.0, 0.0)
                )
            ))
        
        getpos_cache[id(self)] = linePos
        
        return linePos
    
    def getState(self, t: float, defaultColor: tuple[int, int, int]):
        lineAlpha = sum(self.getEventsValue(el.alphaEvents, t) for el in self.eventLayers) if t >= 0.0 or self.isAttachUI else 0.0
        lineRotate = sum(self.getEventsValue(el.rotateEvents, t) for el in self.eventLayers)
        lineScaleX = self.getEventsValue(self.extendEvents.scaleXEvents, t, 1.0) if lineAlpha > 0.0 else 1.0
        lineScaleY = self.getEventsValue(self.extendEvents.scaleYEvents, t, 1.0) if lineAlpha > 0.0 else 1.0
        lineText = self.getEventsValue(self.extendEvents.textEvents, t, "") if lineAlpha > 0.0 and self.extendEvents.textEvents else None
        lineColor = (
            (255, 255, 255)
            if (
                self.isTextureLine or
                self.isAttachUI or
                self.extendEvents.textEvents
            ) else
            defaultColor
        )
        linePos = self.getPos(t)
        
        if lineAlpha > 0.0 and self.extendEvents.colorEvents:
            lineColor = self.getEventsValue(self.extendEvents.colorEvents, t, lineColor)
        
        return (
            self.master.options.posConverter(linePos),
            lineAlpha,
            lineRotate,
            
            lineScaleX,
            lineScaleY,
            lineText,
            lineColor
        )
    
    def sec2beat(self, t: float, bpms: typing.Optional[list[BPMEvent]] = None):
        if bpms is None:
            bpms = self.bpms
            
        if len(bpms) == 1:
            return t / (60 / bpms[0].bpm)
        
        beat = 0.0
        for i, e in enumerate(bpms):
            if i != len(bpms) - 1:
                et_beat = bpms[i + 1].time - e.time
                et_sec = et_beat * (60 / e.bpm)
                
                if t >= et_sec:
                    beat += et_beat
                    t -= et_sec
                else:
                    beat += t / (60 / e.bpm)
                    break
            else:
                beat += t / (60 / e.bpm)
        
        return beat
    
    def beat2sec(self, t: float, bpms: typing.Optional[list[BPMEvent]] = None):
        if bpms is None:
            bpms = self.bpms
            
        if len(bpms) == 1:
            return t * (60 / bpms[0].bpm)

        sec = 0.0
        for i, e in enumerate(bpms):
            if i != len(bpms) - 1:
                et_beat = bpms[i + 1].time - e.time
                
                if t >= et_beat:
                    sec += et_beat * (60 / e.bpm)
                    t -= et_beat
                else:
                    sec += t * (60 / e.bpm)
                    break
            else:
                sec += t * (60 / e.bpm)

        return sec
    
    def getBpm(self, t: float):
        if len(self.bpms) == 1:
            return self.bpms[0].bpm
        
        for i, e in enumerate(self.bpms):
            if i != len(self.bpms) - 1:
                et_beat = self.bpms[i + 1].time - e.time
                et_sec = et_beat * (60 / e.bpm)

                if t >= et_sec:
                    t -= et_sec
                else:
                    return e.bpm
            else:
                return e.bpm
        
        return -1.0

class BinaryFlagsGeneric:
    def __init__(self):
        self.val = 0b01
    
    def next(self):
        ret = self.val
        self.val <<= 1
        return ret

class CommonChartOptionFeatureFlags:
    generic = BinaryFlagsGeneric()
    
    """
    在官谱中, hold 的 spped 为 0 时, 不渲染
    """
    ZERO_SPPED_HOLD_HIDDEN = generic.next()
    
    """
    在官谱中, note 的 floorPosition > h * 2 时, 不渲染
    """
    HIGH_NOTE_FP_HIDDEN = generic.next()
    
    """
    在 rpe 中, 当 line 的 alpha < 0 时, 该线的 note 不渲染
    """
    NEG_LINE_ALPHA_HIDDEN = generic.next()
    
    """
    是否需要纠正 extra 的 bpm 列表
    """
    NEED_FIX_EXTRA_BPMS = generic.next()
    
    PRELOADED_FEATURE_FLAGS = {
        ChartFormat.phi: (
            ZERO_SPPED_HOLD_HIDDEN |
            HIGH_NOTE_FP_HIDDEN |
            0
        ),
        ChartFormat.rpe: (
            NEG_LINE_ALPHA_HIDDEN |
            NEED_FIX_EXTRA_BPMS |
            0
        ),
    }

posCoverters = {
    ChartFormat.unset: lambda pos: pos,
    ChartFormat.phi: lambda pos: pos,
    ChartFormat.rpe: utils.conrpepos
}

@dataclasses.dataclass
class CommonChartOptions:
    holdIndependentSpeed: bool = True
    holdCoverAtHead: bool = True
    rpeVersion: int = -1
    alwaysLineOpenAnimation: bool = True
    featureFlags: int = 0
    globalBpmList: typing.Optional[list[BPMEvent]] = None
    
    enableOverlappedNoteOptimization: bool = True
    overlappedNoteOptimizationLimit: int = 5
    
    viewRatio: float = 16 / 9
    
    lineWidthUnit: tuple[float, float] = (0.0, 0.0)
    lineHeightUnit: tuple[float, float] = (0.0, 0.0)
    
    posConverter: typing.Callable[[tuple[float, float]], tuple[float, float]] = posCoverters[ChartFormat.unset]
    
    res_ext_song: typing.Optional[str] = None
    res_ext_background: typing.Optional[str] = None
    
    meta_ext_name: typing.Optional[str] = None
    meta_ext_composer: typing.Optional[str] = None
    meta_ext_level: typing.Optional[str] = None
    meta_ext_charter: typing.Optional[str] = None
    
    def has_feature(self, flag: int):
        return (self.featureFlags & flag) != 0

@dataclasses.dataclass
class CommonChart:
    offset: float = 0.0
    lines: list[JudgeLine] = dataclasses.field(default_factory=list)
    extra: typing.Optional[Extra] = None
    
    options: CommonChartOptions = dataclasses.field(default_factory=CommonChartOptions)
    type: int = ChartFormat.unset
    
    dumpVersion: int = 4
    
    def init(self):
        self.combotimes = []
        
        self.options.featureFlags |= CommonChartOptionFeatureFlags.PRELOADED_FEATURE_FLAGS[self.type]
        self.options.posConverter = posCoverters[self.type]
        
        self.all_notes = [j for i in self.lines for j in i.notes]
        self.all_notes.sort(key=lambda note: note.time)
        
        self.playerNotes = [i for i in self.all_notes if not i.isFake]
        self.note_num = len(self.playerNotes)
        
        self.checkMorebets()
        self.initCombotimes()
        
        for line in self.lines:
            line.preinit(self)
        
        for line in self.lines:
            line.init()
        
        self.sorted_lines = sorted(self.lines, key=lambda line: line.zOrder)
    
    def fast_init(self):
        "for editor"
        
        self.combotimes = []
        self.note_num = len([i for i in self.all_notes if not i.isFake])
        
        self.checkMorebets()
        self.initCombotimes()
        
        for line in self.lines:
            line.fast_init()
        
        self.sorted_lines = sorted(self.lines, key=lambda line: line.zOrder)
    
    def init_extra(self):
        if self.options.has_feature(CommonChartOptionFeatureFlags.NEED_FIX_EXTRA_BPMS):
            self.extra.bpm = self.options.globalBpmList.copy()
    
    def checkMorebets(self):
        last_note = None
        for note in self.all_notes:
            if last_note is not None and last_note.time == note.time:
                last_note.morebets = True
                note.morebets = True
            
            last_note = note
    
    def initCombotimes(self):
        self.combotimes.extend(note.giveComboTime for note in self.all_notes if not note.isFake)
    
    def getCombo(self, t: float):
        l, r = 0, len(self.combotimes)
        while l < r:
            m = (l + r) // 2
            if self.combotimes[m] <= t: l = m + 1
            else: r = m
        return l
    
    def is_phi(self): return self.type == ChartFormat.phi
    def is_rpe(self): return self.type == ChartFormat.rpe
    
    def dump(self):
        registered_dataclasses: dict[typing.Any, list[tuple[str, typing.Callable[[typing.Any], typing.Any]]]] = {}
        
        def _get_field_default(field: dataclasses.Field):
            return field.default if field.default is not dataclasses.MISSING else field.default_factory()
        
        def _register_dataclasses(types: list[tuple[type, list[tuple[str, typing.Callable[[typing.Any], typing.Any]]]]]):
            writer.writeInt(len(types))
            
            for t, fields in types:
                writer.writeString(t.__name__)
                writer.writeInt(len(fields))
                dataclass_fields = getattr(t, "__dataclass_fields__", None)
                assert dataclass_fields is not None, "not a dataclass"
                
                for field_name, *_ in fields:
                    writer.writeString(field_name)
                
                registered_dataclasses[t] = fields
        
        def _write_dataclass(obj: typing.Any):
            fields = getattr(obj, "__dataclass_fields__", None)
            
            assert fields is not None, "not a dataclass"
            assert type(obj) in registered_dataclasses, "not registered dataclass"
            
            bin_flag = 0
            write_func_calls = []
            need_write_fields = registered_dataclasses[type(obj)]
            
            for i, (field_name, write_func, *default) in enumerate(need_write_fields):
                value = getattr(obj, field_name)
                if field_name in fields:
                    if value != (_get_field_default(fields[field_name]) if not default else default[0]):
                        bin_flag += 1
                        write_func_calls.append((write_func, value))
                else:
                    bin_flag += 1
                    write_func_calls.append((write_func, value))
                
                if i != len(need_write_fields) - 1:
                    bin_flag <<= 1
            
            writer.write(bin_flag.to_bytes((len(need_write_fields) - 1) // 8 + 1))
            
            for write_func, value in write_func_calls:
                write_func(value)
            
        def _write_eventval(value: eventValueType):
            valtype = {float: 0, int: 0, str: 1, tuple: 2}[type(value)]
            writer.writeChar(valtype)
            if valtype == 0: writer.writeFloat(value)
            elif valtype == 1: writer.writeString(value)
            elif valtype == 2:
                writer.writeInt(len(value))
                for i in value: writer.writeFloat(i)
            
        def _write_events(es: list[LineEvent]):
            es = [e for e in es if not e.isFill]
            writer.writeInt(len(es))
            for e in es:
                _write_dataclass(e)
        
        def _write_optional_bpmlist(bpms: typing.Optional[list[BPMEvent]]):
            writer.writeBool(bpms is not None)
            if bpms is not None:
                writer.writeInt(len(bpms))
                for e in bpms:
                    writer.writeFloat(e.time)
                    writer.writeFloat(e.bpm)
        
        def _write_line_sizeunit(unit: tuple[float, float]):
            writer.writeFloat(unit[0])
            writer.writeFloat(unit[1])
            
        writer = utils.ByteWriter()
        writer.writeInt(self.dumpVersion)
        writer.writeFloat(self.offset)
        
        _register_dataclasses([
            (Note, [
                ("type", writer.writeChar),
                ("time", writer.writeFloat),
                ("holdTime", writer.writeFloat),
                ("positionX", writer.writeFloat),
                ("speed", writer.writeFloat),
                ("isAbove", writer.writeBool),
                ("isFake", writer.writeBool),
                ("yOffset", writer.writeFloat),
                ("visibleTime", writer.writeOptionalFloat),
                ("width", writer.writeFloat),
                ("alpha", writer.writeFloat),
                ("hitsound", writer.writeOptionalString),
                ("alwaysHasHoldHead", writer.writeOptionalBool),
                ("masterIndex", writer.writeInt, -1)
            ]),
            (JudgeLine, [
                ("father", writer.writeOptionalInt),
                ("zOrder", writer.writeInt),
                ("isTextureLine", writer.writeBool),
                ("isGifLine", writer.writeBool),
                ("texture", writer.writeOptionalString),
                ("isAttachUI", writer.writeBool),
                ("attachUI", writer.writeOptionalString),
                ("enableCover", writer.writeBool),
                ("index", writer.writeInt, -1)
            ]),
            (LineEvent, [
                ("startTime", writer.writeFloat),
                ("endTime", writer.writeFloat),
                ("start", _write_eventval),
                ("end", _write_eventval),
                ("ease", writer.writeEaseFunc)
            ]),
            (CommonChartOptions, [
                ("holdIndependentSpeed", writer.writeBool),
                ("holdCoverAtHead", writer.writeBool),
                ("rpeVersion", writer.writeInt),
                ("alwaysLineOpenAnimation", writer.writeBool),
                ("featureFlags", writer.writeULong),
                ("globalBpmList", _write_optional_bpmlist),
                ("enableOverlappedNoteOptimization", writer.writeBool),
                ("overlappedNoteOptimizationLimit", writer.writeInt),
                ("lineWidthUnit", _write_line_sizeunit),
                ("lineHeightUnit", _write_line_sizeunit),
                ("res_ext_song", writer.writeOptionalString),
                ("res_ext_background", writer.writeOptionalString),
                ("meta_ext_name", writer.writeOptionalString),
                ("meta_ext_composer", writer.writeOptionalString),
                ("meta_ext_level", writer.writeOptionalString),
                ("meta_ext_charter", writer.writeOptionalString)
            ])
        ])
        
        writer.writeInt(len(self.lines))
        for line in self.lines:
            writer.writeInt(len(line.bpms))
            for bpm in line.bpms:
                writer.writeFloat(bpm.time)
                writer.writeFloat(bpm.bpm)
            
            writer.writeInt(len(line.notes))
            for note in line.notes:
                _write_dataclass(note)
            
            writer.writeInt(len(line.eventLayers))
            for el in line.eventLayers:
                _write_events(el.alphaEvents)
                _write_events(el.moveXEvents)
                _write_events(el.moveYEvents)
                _write_events(el.rotateEvents)
                _write_events(el.speedEvents)
            
            _write_events(line.extendEvents.colorEvents)
            _write_events(line.extendEvents.scaleXEvents)
            _write_events(line.extendEvents.scaleYEvents)
            _write_events(line.extendEvents.textEvents)
            _write_events(line.extendEvents.gifEvents)
            
            _write_dataclass(line)
        
        _write_dataclass(self.options)
        writer.writeInt(self.type)
        
        return writer.getData()

    @staticmethod
    def loaddump(data: bytes):
        reader = utils.ByteReader(data)
        if (v := reader.readInt()) != CommonChart.dumpVersion:
            raise ValueError(f"bad dump version: {v}(bpc) != {CommonChart.dumpVersion}")
        
        def _read_eventval():
            valtype = reader.readChar()
            if valtype == 0: return reader.readFloat()
            elif valtype == 1: return reader.readString()
            elif valtype == 2:
                return [reader.readFloat() for _ in range(reader.readInt())]
        
        def _read_optional_bpmlist():
            return [
                BPMEvent(reader.readFloat(), reader.readFloat())
                for _ in range(reader.readInt())
            ] if reader.readBool() else None
        
        def _read_line_sizeunit():
            return (reader.readFloat(), reader.readFloat())
            
        registered_dataclasses: dict[typing.Any, list[tuple[str, typing.Callable[[], typing.Any]]]] = {}
        
        dataclasses_namemap = {i.__name__: i for i in (
            Note, LineEvent,
            EventLayerItem,
            ExtendEventsItem,
            BPMEvent, JudgeLine,
            CommonChart, CommonChartOptions
        )}
        
        dataclasses_readmethod_namemap = {
            Note: {
                "type": reader.readChar,
                "time": reader.readFloat,
                "holdTime": reader.readFloat,
                "positionX": reader.readFloat,
                "speed": reader.readFloat,
                "isAbove": reader.readBool,
                "isFake": reader.readBool,
                "yOffset": reader.readFloat,
                "visibleTime": reader.readOptionalFloat,
                "width": reader.readFloat,
                "alpha": reader.readFloat,
                "hitsound": reader.readOptionalString,
                "alwaysHasHoldHead": reader.readOptionalBool,
                "masterIndex": reader.readInt
            },
            JudgeLine: {
                "father": reader.readOptionalInt,
                "zOrder": reader.readInt,
                "isTextureLine": reader.readBool,
                "isGifLine": reader.readBool,
                "texture": reader.readOptionalString,
                "isAttachUI": reader.readBool,
                "attachUI": reader.readOptionalString,
                "enableCover": reader.readBool,
                "index": reader.readInt
            },
            LineEvent: {
                "startTime": reader.readFloat,
                "endTime": reader.readFloat,
                "start": _read_eventval,
                "end": _read_eventval,
                "ease": reader.readEaseFunc
            },
            CommonChartOptions: {
                "holdIndependentSpeed": reader.readBool,
                "holdCoverAtHead": reader.readBool,
                "rpeVersion": reader.readInt,
                "alwaysLineOpenAnimation": reader.readBool,
                "featureFlags": reader.readULong,
                "globalBpmList": _read_optional_bpmlist,
                "enableOverlappedNoteOptimization": reader.readBool,
                "overlappedNoteOptimizationLimit": reader.readInt,
                "lineWidthUnit": _read_line_sizeunit,
                "lineHeightUnit": _read_line_sizeunit,
                "res_ext_song": reader.readOptionalString,
                "res_ext_background": reader.readOptionalString,
                "meta_ext_name": reader.readOptionalString,
                "meta_ext_composer": reader.readOptionalString,
                "meta_ext_level": reader.readOptionalString,
                "meta_ext_charter": reader.readOptionalString,
            }
        }
        
        def _read_registered_dataclasses():
            for _ in range(reader.readInt()):
                cls = dataclasses_namemap[reader.readString()]
                if cls not in dataclasses_readmethod_namemap:
                    raise ValueError(f"no read method for {cls.__name__}")
                
                readmethod_namemap = dataclasses_readmethod_namemap[cls]
                defaults = []
                
                for _ in range(reader.readInt()):
                    field_name = reader.readString()
                    if field_name not in readmethod_namemap:
                        raise ValueError(f"no read method for {cls.__name__}.{field_name}")
                    
                    defaults.append((field_name, readmethod_namemap[field_name]))
                
                registered_dataclasses[cls] = defaults
        
        def _read_dataclass(obj: typing.Any):
            fields = getattr(obj, "__dataclass_fields__", None)
            
            assert fields is not None, "not a dataclass"
            
            if type(obj) not in registered_dataclasses:
                raise ValueError(f"not registered dataclass: {type(obj).__name__}")
            
            need_read_fields = registered_dataclasses[type(obj)]
            bin_flag = bin(int.from_bytes(reader.read((len(need_read_fields) - 1) // 8 + 1)))[2:].zfill(len(need_read_fields))
            
            for i, (field_name, read_func) in enumerate(need_read_fields):
                if bin_flag[i] == "1":
                    setattr(obj, field_name, read_func())
        
        def _read_events():
            result = []
            for _ in range(reader.readInt()):
                e = LineEvent()
                _read_dataclass(e)
                e.__post_init__()
                result.append(e)
            return result
        
        def _read_bpms():
            return [BPMEvent(
                time = reader.readFloat(),
                bpm = reader.readFloat()
            ) for _ in range(reader.readInt())]
        
        result = CommonChart()
        result.offset = reader.readFloat()
        
        _read_registered_dataclasses()
        
        for _ in range(reader.readInt()):
            line = JudgeLine()
            line.bpms = _read_bpms()
            
            for _ in range(reader.readInt()):
                note = Note()
                _read_dataclass(note)
                note.__post_init__()
                line.notes.append(note)
            
            line.eventLayers.extend([EventLayerItem(
                alphaEvents = _read_events(),
                moveXEvents = _read_events(),
                moveYEvents = _read_events(),
                rotateEvents = _read_events(),
                speedEvents = _read_events()
            ) for _ in range(reader.readInt())])
            
            line.extendEvents.colorEvents = _read_events()
            line.extendEvents.scaleXEvents = _read_events()
            line.extendEvents.scaleYEvents = _read_events()
            line.extendEvents.textEvents = _read_events()
            line.extendEvents.gifEvents = _read_events()
            
            _read_dataclass(line)
            
            result.lines.append(line)
        
        _read_dataclass(result.options)
        result.type = reader.readInt()
        
        result.init()
        return result

class PPLMProxy_CommonChart(utils.PPLM_ProxyBase):
    def __init__(self, cobj: CommonChart): self.cobj = cobj
    
    def get_lines(self) -> list[JudgeLine]: return self.cobj.lines
    def get_all_pnotes(self) -> list[Note]: return self.cobj.playerNotes
    def remove_pnote(self, n: Note): self.cobj.playerNotes.remove(n)
    
    def nproxy_stime(self, n: Note): return n.time
    def nproxy_etime(self, n: Note): return n.holdEndTime
    def nproxy_hcetime(self, n: Note): return n.giveComboTime
    
    def nproxy_typein(self, n: Note, ts: tuple[int]): return n.type in ts
    def nproxy_typeis(self, n: Note, t: int): return n.type == t
    def nproxy_phitype(self, n: Note): return n.type
    
    def nproxy_nowpos(self, n: Note): return n.nowpos
    def nproxy_nowrotate(self, n: Note) -> float: return n.nowrotate
    def nproxy_effects(self, n: Note): return n.player_effect_times
    
    def nproxy_get_pclicked(self, n: Note): return n.player_clicked
    def nproxy_set_pclicked(self, n: Note, state: bool): n.player_clicked = state
    
    def nproxy_get_wclick(self, n: Note): return n.player_will_click
    def nproxy_set_wclick(self, n: Note, state: bool): n.player_will_click = state
    
    def nproxy_get_pclick_offset(self, n: Note): return n.player_click_offset
    def nproxy_set_pclick_offset(self, n: Note, offset: float): n.player_click_offset = offset
    
    def nproxy_get_ckstate(self, n: Note): return n.state
    def nproxy_set_ckstate(self, n: Note, state: int): n.state = state
    def nproxy_get_ckstate_ishit(self, n: Note): return n.state in (const.NOTE_STATE.PERFECT, const.NOTE_STATE.GOOD)
    
    def nproxy_get_cksound_played(self, n: Note): return n.player_click_sound_played
    def nproxy_set_cksound_played(self, n: Note, state: bool): n.player_click_sound_played = state
    
    def nproxy_get_missed(self, n: Note): return n.player_missed
    def nproxy_set_missed(self, n: Note, state: bool): n.player_missed = state
    
    def nproxy_get_holdjudged(self, n: Note): return n.player_holdjudged
    def nproxy_set_holdjudged(self, n: Note, state: bool): n.player_holdjudged = state
    
    def nproxy_get_holdjudged_tomanager(self, n: Note): return n.player_holdjudged_tomanager
    def nproxy_set_holdjudged_tomanager(self, n: Note, state: bool): n.player_holdjudged_tomanager = state
    
    def nproxy_get_last_testholdmiss_time(self, n: Note): return n.player_last_testholdismiss_time
    def nproxy_set_last_testholdmiss_time(self, n: Note, time: float): n.player_last_testholdismiss_time = time
    
    def nproxy_get_safe_used(self, n: Note): return n.player_judge_safe_used
    def nproxy_set_safe_used(self, n: Note, state: bool): n.player_judge_safe_used = state
    
    def nproxy_get_holdclickstate(self, n: Note): return n.player_holdclickstate
    def nproxy_set_holdclickstate(self, n: Note, state: int): n.player_holdclickstate = state
    
    def nproxy_get_pbadtime(self, n: Note): return n.player_badtime
    def nproxy_set_pbadtime(self, n: Note, time: float): n.player_badtime = time

def load(data: str) -> CommonChart:
    def _unknow_type():
        raise ValueError("Unknown chart type")
    
    if not isinstance(data, dict):
        _unknow_type()
        
    if "formatVersion" in data:
        return ChartFormat.load_phi(data)
    
    elif "META" in data:
        return ChartFormat.load_rpe(data)
    
    else:
        _unknow_type()

@dataclasses.dataclass
class ExtraVar:
    startTime: float
    endTime: float
    start: float|list[float]
    end: float|list[float]
    easingType: int
    
    def __post_init__(self):
        self.ease = geteasing_func(self.easingType)
        
        if isinstance(self.start, int|float):
            self.get = lambda t: utils.easing_interpolation(t, self.startTime, self.endTime, self.start, self.end, self.ease)
        elif isinstance(self.start, typing.Iterable):
            self.get = lambda t: tuple(utils.easing_interpolation(t, self.startTime, self.endTime, self.start[i], self.end[i], self.ease) for i in range(len(self.start)))
        else:
            raise ValueError(f"Invalid event value type: {type(self.start)}")
    
@dataclasses.dataclass
class ExtraEffect:
    start: float
    end: float
    shader: str
    global_: bool
    vars: dict[str, list[ExtraVar]]
    
    def _init_events(self, es: list[ExtraVar]):
        if not es:
            return

        aes = []
        for i, e in enumerate(es):
            if i != len(es) - 1:
                ne = es[i + 1]
                if e.endTime < ne.startTime:
                    aes.append(ExtraVar(e.endTime, ne.startTime, e.end, e.end, 1))
                    
        es.extend(aes)
        es.sort(key = lambda x: x.startTime)
        es.append(ExtraVar(es[-1].endTime, const.INFBEAT, es[-1].end, es[-1].end, 1))
        
    def __post_init__(self):
        for v in self.vars.values():
            self._init_events(v)

@dataclasses.dataclass
class ExtraVideo:
    path: str
    time: float
    scale: typing.Literal["cropCenter", "inside", "fit"]
    alpha: list[ExtraVar]
    dim: list[ExtraVar]
    
    def __post_init__(self):
        if self.scale not in ("cropCenter", "inside", "fit"):
            logging.warning(f"Invalid scale type {self.scale} for video {self.path}")
            self.scale = "cropCenter"
        
        self.h264data, self.size = utils.video2h264(f"{tempdir.createTempDir()}/{self.path}")
        self.unqique_id = f"extra_video_{random.randint(0, 2 << 31)}"

@dataclasses.dataclass
class Extra:
    bpm: list[BPMEvent]
    effects: list[ExtraEffect]
    videos: list[ExtraVideo]
    
    def getShaderEffect(self, t: float, isglobal: bool):
        beat = JudgeLine.sec2beat(None, t, self.bpm)
        result = []
        
        for e in self.effects:
            if e.global_ != isglobal: continue
            if e.start <= beat < e.end:
                values = {}
                
                for k, v in e.vars.items():
                    ev = JudgeLine.getEventsValue(None, v, beat, v[0].start if v else None)
                    if ev is not None: values.update({k: ev})
                    
                if e.shader in const.EXTRA_DEFAULTS.keys():
                    defvs: dict = const.EXTRA_DEFAULTS[e.shader].copy()
                    defvs.update(values)
                    values = defvs
                    
                result.append((e.shader, values))
                
        return result
    
    def getVideoEffect(self, t: float) -> list[tuple[ExtraVideo, float]]:
        beat = JudgeLine.sec2beat(None, t, self.bpm)
        result = []
        
        for video in self.videos:
            if video.time <= beat:
                result.append((video, t - JudgeLine.beat2sec(None, video.time, self.bpm)))
        
        return result

def loadExtra(extra_json: dict):
    extra = Extra(
        bpm = [
            BPMEvent(
                time = _beat2num(bpme.get("startTime", [0, 0, 1])),
                bpm = bpme.get("bpm", 140)
            )
            for bpme in extra_json.get("bpm", [])
        ],
        effects = [
            ExtraEffect(
                start = _beat2num(ete.get("start", [0, 0, 1])),
                end = _beat2num(ete.get("end", [0, 0, 1])),
                shader = ete.get("shader", "default"),
                global_ = ete.get("global", False),
                vars = {
                    k: [
                        (
                            ExtraVar(
                                startTime = _beat2num(v.get("startTime", [0, 0, 1])),
                                endTime = _beat2num(v.get("endTime", [0, 0, 1])),
                                start = v.get("start", 0),
                                end = v.get("end", 0),
                                easingType = v.get("easingType", 1)
                            ) 
                        )
                        for v in vars
                    ] if isinstance(vars, list) and isinstance(vars[0], dict) else [ExtraVar(
                        startTime = _beat2num(ete.get("start", [0, 0, 1])),
                        endTime = _beat2num(ete.get("end", [0, 0, 1])),
                        start = vars,
                        end = vars,
                        easingType = 1
                    )]
                    for k, vars in ete.get("vars", {}).items()
                }
            )
            for ete in extra_json.get("effects", [])
        ],
        videos = [
            ExtraVideo(
                path = video.get("path", ""),
                time = _beat2num(video.get("time", [0, 0, 1])),
                scale = video.get("scale", "cropCenter"),
                alpha = ([
                    (
                        ExtraVar(
                            startTime = _beat2num(v.get("startTime", [0, 0, 1])),
                            endTime = _beat2num(v.get("endTime", [0, 0, 1])),
                            start = v.get("start", 0),
                            end = v.get("end", 0),
                            easingType = v.get("easingType", 1)
                        ) 
                    )
                    for v in video["alpha"]
                ] if isinstance(video["alpha"], list) and isinstance(video["alpha"][0], dict) else [ExtraVar(
                    startTime = 0.0,
                    endTime = const.INFBEAT,
                    start = video["alpha"],
                    end = video["alpha"],
                    easingType = 1
                )]) if "alpha" in video else 1.0,
                dim = ([
                    (
                        ExtraVar(
                            startTime = _beat2num(v.get("startTime", [0, 0, 1])),
                            endTime = _beat2num(v.get("endTime", [0, 0, 1])),
                            start = v.get("start", 0),
                            end = v.get("end", 0),
                            easingType = v.get("easingType", 1)
                        ) 
                    )
                    for v in video["dim"]
                ] if isinstance(video["dim"], list) and isinstance(video["dim"][0], dict) else [ExtraVar(
                    startTime = 0.0,
                    endTime = const.INFBEAT,
                    start = video["dim"],
                    end = video["dim"],
                    easingType = 1
                )]) if "dim" in video else 1.0,
            )
            for video in extra_json.get("videos", [])
        ]
    )
    
    return extra

def update_note(note: Note):
    note.__post_init__()
    note.master.master.init()

def update_line(line: JudgeLine):
    line.__post_init__()
    line.master.init()

def update_chart(chart: CommonChart):
    chart.__post_init__()
    chart.init()
