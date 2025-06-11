from __future__ import annotations

from random import uniform
import dataclasses
import threading
import typing
import time
import uuid

from PIL import Image

import utils
import const
import rpe_easing
import dxsound
from dxsmixer_unix import mixer as unix_mixer

@dataclasses.dataclass
class ClickEvent:
    rect: tuple[float, float, float, float]
    callback: typing.Callable[[int, int], typing.Any]
    once: bool
    tag: typing.Optional[str] = None
    
    def __hash__(self) -> int:
        return id(self)

@dataclasses.dataclass
class MoveEvent:
    callback: typing.Callable[[int, int], typing.Any]
    tag: typing.Optional[str] = None
    
    def __hash__(self) -> int:
        return id(self)
    
@dataclasses.dataclass
class ReleaseEvent:
    callback: typing.Callable[[int, int], typing.Any]
    tag: typing.Optional[str] = None

    def __hash__(self) -> int:
        return id(self)

@dataclasses.dataclass
class EventManager:
    def __init__(self) -> None:
        self.clickEvents: list[ClickEvent] = []
        self.moveEvents: list[MoveEvent] = []
        self.releaseEvents: list[ReleaseEvent] = []
    
    def _callClickCallback(self, e: ClickEvent, x: int, y: int) -> None:
        if utils.inrect(x, y, e.rect):
            e.callback(x, y)
            if e.once:
                self.unregEvent(e)
                
    @utils.runByThread
    def click(self, x: int, y: int) -> None:
        for e in self.clickEvents:
            self._callClickCallback(e, x, y)
            
    @utils.runByThread
    def move(self, x: int, y: int) -> None:
        for e in self.moveEvents:
            e.callback(x, y)
    
    @utils.runByThread
    def release(self, x: int, y: int) -> None:
        for e in self.releaseEvents:
            e.callback(x, y)
    
    def regClickEvent(self, e: ClickEvent):
        self.clickEvents.append(e)
    
    def regMoveEvent(self, e: MoveEvent):
        self.moveEvents.append(e)

    def regReleaseEvent(self, e: ReleaseEvent):
        self.releaseEvents.append(e)
    
    def regClickEventFs(self, callback: typing.Callable[[int, int], typing.Any], once: bool):
        e = ClickEvent((0, 0, float("inf"), float("inf")), callback, once)
        self.regClickEvent(e)
        return e
    
    def regReleaseEventFs(self, callback: typing.Callable[[int, int], typing.Any]):
        e = ReleaseEvent(callback)
        self.regReleaseEvent(e)
        return e
    
    def unregEvent(self, e: ClickEvent):
        for elist in [self.clickEvents, self.moveEvents, self.releaseEvents]:
            try:
                elist.remove(e)
            except ValueError:
                pass
    
    def unregEventByChooseChartControl(self, ccc: ChooseChartControler):
        for e in self.clickEvents:
            if e.callback is ccc.scter_mousedown:
                self.unregEvent(e)
                break
                
        for e in self.releaseEvents:
            if e.callback is ccc.scter_mouseup:
                self.unregEvent(e)
                break
        
        for e in self.moveEvents:
            if e.callback is ccc.scter_mousemove:
                self.unregEvent(e)
                break

@dataclasses.dataclass
class FaculaAnimationManager:
    def __init__(self) -> None:
        self.faculas = []
    
    def main(self):
        self._createFacula()
        self._createFacula()
        while True:
            time.sleep(uniform(0.35, 1.25))
            self._createFacula()
            for facula in self.faculas:
                if facula["endTime"] < time.time():
                    self.faculas.remove(facula)
    
    def getFaculaState(self, facula: dict) -> dict:
        p = (time.time() - facula["startTime"]) / (facula["endTime"] - facula["startTime"]) # cannot use tool_funcs.linear_interpolation, it will return 0.0, i tkink is jit bug?. or f32 precision problem?
        if p <= 0.2:
            ep = 1.0 - (1.0 - (p / 0.2)) ** 2
        elif p <= 0.8:
            ep = 1.0
        else:
            ep = (1.0 - (p - 0.8) / 0.2) ** 2
        
        return {
            "y": facula["sy"] + (facula["ey"] - facula["sy"]) * p,
            "size": ep * facula["size"],
            "alpha": ep
        }
            
    def _createFacula(self):
        sy = uniform(0.0, 1.0)
        self.faculas.append({
            "startTime": time.time(),
            "endTime": time.time() + uniform(5.0, 7.0),
            "x": uniform(0.05, 0.95),
            "sy": sy,
            "ey": sy - uniform(0.5, 0.7),
            "size": uniform(0.7, 1.3)
        })

@dataclasses.dataclass
class SongDifficulty:
    name: str
    level: float
    chart_audio: str
    chart_image: str
    chart_file: str
    charter: str
    
    def __post_init__(self):
        self.strdiffnum = str(int(self.level))
        self.song = None
    
    def unqique_id(self):
        return uuid.uuid5(uuid.NAMESPACE_DNS, str((
            self.chart_audio,
            self.chart_image,
            self.chart_file
        ))).hex
    
@dataclasses.dataclass
class Song:
    name: str
    composer: str
    iller: str
    image: str
    image_lowres: str
    preview: str
    preview_start: float
    preview_end: float
    difficulty: list[SongDifficulty]
    import_archive_alias: typing.Optional[str]
    
    chooseSongs_nameFontSize: float = float("nan")
    currSong_composerFontSize: float = float("nan")
    
    def __post_init__(self):
        self.songId = int(uniform(0.0, 1.0) * (2 << 31))
        self.difficulty = self.difficulty[:4]
        self.level_bar_rightx_max = const.LEVEL_BAR_END_XMAP[len(self.difficulty) - 1]
        
        for diff in self.difficulty:
            diff.song = self
    
    def __eq__(self, value: typing.Any):
        return self is value
    
@dataclasses.dataclass
class Chapter:
    name: str
    cn_name: str
    o_name: str
    image: str
    songs: list[Song]
    all_songs_flag: bool
    im: None|Image.Image = None
    
    def __post_init__(self):
        self.chapterId = int(uniform(0.0, 1.0) * (2 << 31))
        self.scsd_songs = self.songs.copy()
    
    def __hash__(self):
        return id(self)

@dataclasses.dataclass
class Chapters:
    items: list[Chapter]
    aFrom: int = -1
    aTo: int = 0
    aSTime: float = float("-inf")

@dataclasses.dataclass
class Setting:
    offset: int = 0 # ms, -400 ~ 600
    scale: float = 1.0 # 1.0 ~ 1.3
    background_dim: float = 1.0 # 0.2 ~ 1.0 (?)
    enable_click_sound: bool = True
    sound_volume: float = 1.0 # 0.0 ~ 1.0
    ui_volume: float = 1.0 # 0.0 ~ 1.0
    click_sound_volume: float = 1.0 # 0.0 ~ 1.0
    moerbets_auxiliary: bool = True
    fcap_indicator: bool = True
    low_quality: bool = False
    
@dataclasses.dataclass
class SettingState:
    aFrom: int = const.PHIGROS_SETTING_STATE.PLAY
    aTo: int = const.PHIGROS_SETTING_STATE.PLAY
    aSTime: float = float("-inf")
    
    def __post_init__(self):
        self._ease_fast = rpe_easing.ease_funcs[11]
        self._ease_slow = rpe_easing.ease_funcs[12]
        self.atime = 0.65
    
    def getBarWidth(self):
        sv = const.PHIGROS_SETTING_BAR_WIDTH_MAP[self.aFrom]
        ev = const.PHIGROS_SETTING_BAR_WIDTH_MAP[self.aTo]
        if self.aSTime == float("-inf"):
            return ev
        st = self.aSTime
        et = self.aSTime + self.atime
        p = (time.time() - st) / (et - st)
        p = utils.fixorp(p)
        p = self._ease_slow(p)
        return p * (ev - sv) + sv
    
    def getLabelWidth(self):
        sv = const.PHIGROS_SETTING_LABEL_WIDTH_MAP[self.aFrom]
        ev = const.PHIGROS_SETTING_LABEL_WIDTH_MAP[self.aTo]
        if self.aSTime == float("-inf"):
            return ev
        st = self.aSTime
        et = self.aSTime + self.atime
        p = (time.time() - st) / (et - st)
        p = utils.fixorp(p)
        p = self._ease_fast(p)
        return p * (ev - sv) + sv
    
    def getLabelX(self):
        sv = const.PHIGROS_SETTING_LABEL_X_MAP[self.aFrom]
        ev = const.PHIGROS_SETTING_LABEL_X_MAP[self.aTo]
        if self.aSTime == float("-inf"):
            return ev
        st = self.aSTime
        et = self.aSTime + self.atime
        p = (time.time() - st) / (et - st)
        p = utils.fixorp(p)
        p = self._ease_slow(p)
        return p * (ev - sv) + sv
    
    def _lerFromTextColor(self, p: float):
        return (255 * p, ) * 3
    
    def _lerToTextColor(self, p: float):
        return (255 * (1.0 - p), ) * 3
    
    def getTextColor(self, t: int):
        if t not in (self.aFrom, self.aTo):
            return (255, 255, 255)
        elif self.aSTime == float("-inf"):
            return (0, 0, 0) # aFrom and aTo is 1
        else:
            st = self.aSTime
            et = self.aSTime + self.atime
            p = (time.time() - st) / (et - st)
            p = utils.fixorp(p)
            
            # 这里奇怪的算法: 为了视觉上好看和还原一点
            absv = abs(self.aFrom - self.aTo) if self.aFrom != self.aTo else 1.0
            absv += 0.5
            absv **= 1.25
            if t == self.aFrom:
                p = 1.0 - (1.0 - p) ** absv
            else:
                p = 1.0 - (1.0 - p) ** (1 / absv)
                
            return self._lerFromTextColor(p) if self.aFrom == t else self._lerToTextColor(p)
    
    def getTextScale(self, t: int):
        if t not in (self.aFrom, self.aTo):
            return 1.0
        elif self.aSTime == float("-inf"):
            return 1.175
        else:
            st = self.aSTime
            et = self.aSTime + self.atime
            p = (time.time() - st) / (et - st)
            p = utils.fixorp(p)
            p = self._ease_slow(p)
            
            return utils.linear_interpolation(p, 0.0, 1.0, 1.175, 1.0) if self.aFrom == t else utils.linear_interpolation(p, 0.0, 1.0, 1.0, 1.175)
    
    def getShadowRect(self):
        sv = const.PHIGROS_SETTING_SHADOW_XRECT_MAP[self.aFrom]
        ev = const.PHIGROS_SETTING_SHADOW_XRECT_MAP[self.aTo]
        if self.aSTime == float("-inf"):
            return ev
        st = self.aSTime
        et = self.aSTime + self.atime
        p = (time.time() - st) / (et - st)
        p = utils.fixorp(p)
        p = self._ease_slow(p)
        return (
            p * (ev[0] - sv[0]) + sv[0],
            p * (ev[1] - sv[1]) + sv[1]
        )
        
    def changeState(self, state: int):
        self.aFrom, self.aTo = self.aTo, state
        self.aSTime = time.time()
    
    def getSettingDx(self, shadowRectLeft: float, w: int, t: int):
        return (const.PHIGROS_SETTING_SHADOW_XRECT_MAP[t][0] - shadowRectLeft) * w
        
    def render(
        self,
        drawPlaySetting: typing.Callable[[float, float], None],
        drawAccountAndCountSetting: typing.Callable[[float, float], None],
        drawOtherSetting: typing.Callable[[float, float], None],
        shadowRectLeft: float, w: int,
        settingDx: list[float]
    ):
        sp_state = self.aFrom == self.aTo # before user change ui state
        if sp_state:
            self.aFrom = const.PHIGROS_SETTING_STATE.ACCOUNT_AND_COUNT
            self.aTo = const.PHIGROS_SETTING_STATE.PLAY
        
        st = self.aSTime
        et = self.aSTime + self.atime
        p = (time.time() - st) / (et - st) if self.aSTime != float("-inf") else 1.0
        p = utils.fixorp(p)
        p = self._ease_slow(p)
        
        drawPlaySettingDx = self.getSettingDx(shadowRectLeft, w, const.PHIGROS_SETTING_STATE.PLAY)
        drawAccountAndCountSettingDx = self.getSettingDx(shadowRectLeft, w, const.PHIGROS_SETTING_STATE.ACCOUNT_AND_COUNT)
        drawOtherSettingDx = self.getSettingDx(shadowRectLeft, w, const.PHIGROS_SETTING_STATE.OTHER)

        drawPlaySettingAlpha = 0.0 if const.PHIGROS_SETTING_STATE.PLAY not in (self.aFrom, self.aTo) else ((1.0 - p) if self.aFrom == const.PHIGROS_SETTING_STATE.PLAY else p)
        drawAccountAndCountSettingAlpha = 0.0 if const.PHIGROS_SETTING_STATE.ACCOUNT_AND_COUNT not in (self.aFrom, self.aTo) else ((1.0 - p) if self.aFrom == const.PHIGROS_SETTING_STATE.ACCOUNT_AND_COUNT else p)
        drawOtherSettingAlpha = 0.0 if const.PHIGROS_SETTING_STATE.OTHER not in (self.aFrom, self.aTo) else ((1.0 - p) if self.aFrom == const.PHIGROS_SETTING_STATE.OTHER else p)

        drawPlaySetting(drawPlaySettingDx, drawPlaySettingAlpha)
        drawAccountAndCountSetting(drawAccountAndCountSettingDx, drawAccountAndCountSettingAlpha)
        drawOtherSetting(drawOtherSettingDx, drawOtherSettingAlpha)
        settingDx.clear()
        settingDx.extend([drawPlaySettingDx, drawAccountAndCountSettingDx, drawOtherSettingDx])
        
        if sp_state:
            self.aFrom = const.PHIGROS_SETTING_STATE.PLAY
            self.aTo = const.PHIGROS_SETTING_STATE.PLAY

    @property
    def atis_p(self): return self.aTo == const.PHIGROS_SETTING_STATE.PLAY
    @property
    def atis_a(self): return self.aTo == const.PHIGROS_SETTING_STATE.ACCOUNT_AND_COUNT
    @property
    def atis_o(self): return self.aTo == const.PHIGROS_SETTING_STATE.OTHER

class PhiWidgetEventZLyaer:
    NORMAL = 0
    COMBOBOX = 1

@dataclasses.dataclass
class PhiBaseWidget:
    tonext: float = 0.0
    break_event_chain: object = object()
    event_zlayer: int = PhiWidgetEventZLyaer.NORMAL
    
    def mouseDown(self, x: int, y: int): ...
    def mouseUp(self, x: int, y: int): ...
    def mouseMove(self, x: int, y: int): ...
    def inRect(self, x: int, y: int): return False
    
    @staticmethod
    def _new_atf(initvar: float = 1.0):
        atf = valueTransformer(animation_time=0.1)
        atf.target = initvar
        return atf
    
    @staticmethod
    def _new_ease_atf(initvar: float = 1.0):
        atf = PhiBaseWidget._new_atf(initvar)
        atf.ease = rpe_easing.ease_funcs[7]
        atf.animation_time = 0.3
        return atf
    
@dataclasses.dataclass
class PhiLabel(PhiBaseWidget):
    left_text: str = ""
    right_text: str = ""
    fontsize: float = 1.0
    color: str = "#FFFFFF"
    
@dataclasses.dataclass
class PhiSlider(PhiBaseWidget):
    value: float = 0.0
    number_points: tuple[tuple[float, float]] = ((0.0, 0.0), (1.0, 1.0))
    lr_button: bool = False
    sliderUnit: float = float("nan")
    conUnit: float = 0.0
    numberType: typing.Union[int, float] = float
    command: typing.Callable[[], typing.Any] = lambda *args, **kwargs: None
    
    def __post_init__(self):
        self.sliderRect = const.EMPTY_RECT
        self.lconButtonRect = const.EMPTY_RECT
        self.rconButtonRect = const.EMPTY_RECT
        self._mouseDown = False
        self._mouseDownInCon = False
        
        self.lcon_atf = self._new_atf()
        self.rcon_atf = self._new_atf()
        self.slider_atf = self._new_atf()
    
    def _fixValue(self):
        self.value = self.number_points[0][1] if self.value < self.number_points[0][1] else (
            self.number_points[-1][1] if self.value > self.number_points[-1][1] else self.value
        )
        self.value = self.numberType(self.value)
        
        self.command()
    
    def _SliderEvent(self, x: int, y: int):
        if not self._mouseDown or (
            utils.indrect(x, y, self.rconButtonRect)
            or utils.indrect(x, y, self.lconButtonRect)
        ) or self._mouseDownInCon:
            return
        
        p = (x - self.sliderRect[0]) / (self.sliderRect[2] - self.sliderRect[0])
        p = 0.0 if p < 0.02 else (1.0 if p > 0.97 else p)
        v = utils.sliderValueValue(p, self.number_points)
        if self.sliderUnit != self.sliderUnit: # nan
            self.value = v
        else:
            up = v / self.sliderUnit
            up = int(up) if abs(up) % 1.0 < 0.5 else int(up) + 1
            self.value = up * self.sliderUnit
        
        self._fixValue()
    
    def _ConButtonEvent(self, x: int, y: int):
        if utils.indrect(x, y, self.lconButtonRect):
            self.value -= self.conUnit
        elif utils.indrect(x, y, self.rconButtonRect):
            self.value += self.conUnit
        else:
            return False
        
        self._fixValue()
        return True
    
    def mouseDown(self, x: int, y: int):
        self._mouseDown = self.inRect(x, y)
        self._mouseDownInCon = self._ConButtonEvent(x, y)
        self._SliderEvent(x, y)
        
        self.lcon_atf.target = 0.7 if utils.indrect(x, y, self.lconButtonRect) else 1.0
        self.rcon_atf.target = 0.7 if utils.indrect(x, y, self.rconButtonRect) else 1.0
        self.slider_atf.target = 0.7 if utils.indrect(x, y, self.sliderRect) else 1.0
        
    def mouseUp(self, x: int, y: int):
        self._mouseDown = False
        
        self.lcon_atf.target = 1.0
        self.rcon_atf.target = 1.0
        self.slider_atf.target = 1.0
    
    def mouseMove(self, x: int, y: int):
        if self._mouseDown:
            self._SliderEvent(x, y)
    
    def inRect(self, x: int, y: int):
        return any([
            utils.indrect(x, y, self.sliderRect),
            utils.indrect(x, y, self.lconButtonRect),
            utils.indrect(x, y, self.rconButtonRect)
        ])
    
@dataclasses.dataclass
class PhiCheckbox(PhiBaseWidget):
    text: str = ""
    fontsize: float = 1.0
    checked: bool = False
    command: typing.Callable[[], typing.Any] = lambda *args, **kwargs: None
    
    def __post_init__(self):
        self.check_animation_st = float("-inf")
        self.checkboxRect = const.EMPTY_RECT
        self._mouseDown = False
        
        self.box_atf = self._new_atf()
    
    def mouseDown(self, x: int, y: int):
        self._mouseDown = self.inRect(x, y)
        self.box_atf.target = 0.7 if self.inRect(x, y) else 1.0
    
    def mouseUp(self, x: int, y: int):
        if self._mouseDown and self.inRect(x, y):
            self.checked = not self.checked
            self.check_animation_st = time.time()
            self.command()
            
        self._mouseDown = False
        self.box_atf.target = 1.0
    
    def inRect(self, x: int, y: int):
        return utils.inrect(x, y, self.checkboxRect)

@dataclasses.dataclass
class PhiButton(PhiBaseWidget):
    text: str = ""
    fontsize: float = 1.0
    width: float = 0.0
    command: typing.Callable[[], typing.Any] = lambda *args, **kwargs: None
    anchor: typing.Literal["left", "center", "right"] = "center"
    dx: float = 0.0

    def __post_init__(self):
        self.buttonRect = const.EMPTY_RECT
        self._mouseDown = False
        self.button_atf = self._new_atf()

    def mouseDown(self, x: int, y: int):
        self._mouseDown = self.inRect(x, y)
        self.button_atf.target = 0.7 if self.inRect(x, y) else 1.0

    def mouseUp(self, x: int, y: int):
        call_command = self._mouseDown and self.inRect(x, y)
        self._mouseDown = False
        self.button_atf.target = 1.0
        
        if call_command:
            self.command()

    def inRect(self, x: int, y: int):
        return utils.inrect(x, y, self.buttonRect)

@dataclasses.dataclass
class PhiCombobox(PhiBaseWidget):
    value: int = 2
    values: list[str] = dataclasses.field(default_factory=list)
    command: typing.Callable[[int], typing.Any] = lambda *args, **kwargs: None
    anchor: typing.Literal["left", "center", "right"] = "center"
    text_color: str = "black"
    fontsize: float = 1.0
    
    def __post_init__(self):
        self.event_zlayer = PhiWidgetEventZLyaer.COMBOBOX
        self.comboboxRect = const.EMPTY_RECT
        self.onRect = const.EMPTY_RECT
        self.itemHeight = 0.0
        self.itemStart = 0.0
        self.ison = False
        self.on_atf = self._new_ease_atf(0.0)
        self.md_bec = False
        self.value_atf = self._new_ease_atf(self.value)
        self._mouseDown = False
        self._mouseDownPos = const.EMPTY_RECT
    
    def mouseDown(self, x: int, y: int):
        self._mouseDownPos = (x, y)
        
        if self.ison and utils.indrect(x, y, self.onRect):
            self._mouseDown = True
            return PhiBaseWidget.break_event_chain
        elif utils.indrect(x, y, self.comboboxRect):
            self.ison = not self.ison
            self.on_atf.target = 1.0 if self.ison else 0.0
            self.md_bec = False
        
        self._mouseDown = False
    
    def mouseUp(self, x: int, y: int):
        if self._mouseDown:
            self._mouseDown = False
            x, y = self._mouseDownPos
            
            if utils.indrect(x, y, self.onRect):
                newi = int((y - self.itemStart) / self.itemHeight) if self.itemHeight else 0
                self.value = newi
                self.value = self.vaild_value
                self.value_atf.target = self.value
                self.ison = False
                self.on_atf.target = 0.0
                self.command(self.value)
                self.md_bec = True
                
            return PhiBaseWidget.break_event_chain
    
    @property
    def vaild_value(self):
        return min(len(self.values) - 1, max(0, self.value))
    
    @property
    def vaild_text(self):
        return self.values[self.vaild_value] if self.values else "NO-SELECTION"

class WidgetEventManager:
    def __init__(self, widgets: list[PhiBaseWidget], condition: typing.Callable[[int, int], bool]):
        self.widgets = widgets
        self.condition = condition
    
    def mouseDown(self, x: int, y: int):
        if not self.condition(x, y): return
        for widget in self.widgets_event_zlayer_sorted:
            ret = widget.mouseDown(x, y)
            if ret is PhiBaseWidget.break_event_chain:
                break

    def mouseUp(self, x: int, y: int):
        if not self.condition(x, y): return
        for widget in self.widgets_event_zlayer_sorted:
            ret = widget.mouseUp(x, y)
            if ret is PhiBaseWidget.break_event_chain:
                break

    def mouseMove(self, x: int, y: int):
        if not self.condition(x, y): return
        for widget in self.widgets_event_zlayer_sorted:
            ret = widget.mouseMove(x, y)
            if ret is PhiBaseWidget.break_event_chain:
                break
    
    def inRect(self, x: int, y: int):
        if not self.condition(x, y): return False
        for widget in self.widgets_event_zlayer_sorted:
            if widget.inRect(x, y):
                return True
        return False
    
    @property
    def widgets_event_zlayer_sorted(self):
        return sorted(self.widgets, key=lambda w: w.event_zlayer, reverse=True)

class SlideControler:
    def __init__(
        self,
        eventRect: (
            typing.Callable[[int, int], bool]
            | list[tuple[typing.Callable[[int, int], bool], float]]
        ),
        setFunc: typing.Callable[[float, float], typing.Any],
        minValueX: float, maxValueX: float,
        minValueY: float, maxValueY: float,
        w: int, h: int
    ):
        self.eventRect = eventRect if isinstance(eventRect, list) else [(eventRect, 1.0)]
        self.setFunc = setFunc
        self.minValueX, self.maxValueX = minValueX, maxValueX
        self.minValueY, self.maxValueY = minValueY, maxValueY
        self.w, self.h = w, h
        self._lastlastclickx, self._lastclicky = 0.0, 0.0
        self._lastclickx, self._lastclicky = 0.0, 0.0
        self._dx, self._dy = 0.0, 0.0
        self._mouseDown = False
        self._recti = -1
        
        self.startcallback = lambda: None
        self.endcallback = lambda: None
        self.easeEndXCallback = lambda: None
        self.easeEndYCallback = lambda: None
        self.easeScrollCallback = lambda: None
        
        self._easeBackXEvents: list[threading.Event] = []
        self._easeBackYEvents: list[threading.Event] = []
        self._easeScrollEvents: list[threading.Event] = []
        
        self.resistance = 0.93
        self._mouseDowned = False
    
    def _inrect(self, x: int, y: int):
        for i, (f, _) in enumerate(self.eventRect):
            if f(x, y): return True, i
        return False, -1
    
    def mouseDown(self, x: int, y: int):
        isinrect, i = self._inrect(x, y)
        if not isinrect: return
        
        self._recti = i
        self._lastclickx, self._lastclicky = x, y
        self._lastlastclickx, self._lastlastclicky = x, y
        self._mouseDown = True
        self.stopAllEase()
        self.startcallback()
    
    def mouseUp(self, x: int, y: int):
        if self._mouseDown:
            threading.Thread(target=self.easeSroll, daemon=True).start()
            
        self._mouseDown = False
        self.endcallback()
    
    def mouseMove(self, x: int, y: int):
        if not self._mouseDown: return
        self._mouseDowned = True
        
        self.mouseMoveBy(
            (x - self._lastclickx) * self.eventRect[self._recti][1],
            (y - self._lastclicky) * self.eventRect[self._recti][1]
        )
        self._lastlastclickx, self._lastlastclicky = self._lastclickx, self._lastclicky
        self._lastclickx, self._lastclicky = x, y
    
    def mouseMoveBy(self, x: int, y: int):
        self._dx += x
        self._dy += y
        self._set()
    
    def setDx(self, v: float): self._dx = v
    def setDy(self, v: float): self._dy = v
    def getDx(self): return self._dx
    def getDy(self): return self._dy
    
    def easeSroll(self):
        if not self._mouseDowned:
            return
        
        dx = self._lastclickx - self._lastlastclickx
        dy = self._lastclicky - self._lastlastclicky
        called_easeBackX, called_easeBackY = False, False
        dx *= 1.2; dy *= 1.2
        
        for e in self._easeScrollEvents.copy():
            e.clear()
            self._easeScrollEvents.remove(e)
        
        myevent = threading.Event()
        myevent.set()
        self._easeScrollEvents.append(myevent)
        
        while abs(dx) > self.w * 0.001 or abs(dy) > self.h * 0.001:
            if not myevent.is_set():
                return
            
            dx *= self.resistance; dy *= self.resistance
            self._dx += dx; self._dy += dy
            self._set()
            
            # 往右 = 负, 左 = 正, 反的, 所以`- self._d(x / y)`
            
            if - self._dx <= - self.minValueX or - self._dx >= self.maxValueX - self.minValueX:
                threading.Thread(target=self.easeBackX, daemon=True).start()
                called_easeBackX = True
                dx = 0.0
            
            if - self._dy <= - self.minValueY or - self._dy >= self.maxValueY - self.minValueY:
                threading.Thread(target=self.easeBackY, daemon=True).start()
                called_easeBackY = True
                dy = 0.0
            
            time.sleep(1 / 120)
        
        if not called_easeBackX:
            threading.Thread(target=self.easeBackX, daemon=True).start()
            
        if not called_easeBackY:
            threading.Thread(target=self.easeBackY, daemon=True).start()
        
        self.easeScrollCallback()
    
    def easeBackX(self, target: typing.Optional[float] = None, need_callback: bool = True):
        cdx = - self._dx
        if self.minValueX <= cdx <= self.maxValueX and target is None:
            return
        
        if target is None:
            if cdx < 0:
                dx = - cdx
            else:
                dx = self.maxValueX - cdx
            dx *= -1 # 前面cdx = 负的, 所以变回来
            if self._dx + dx > 0: # 超出左界
                dx = - self._dx
        else:
            dx = cdx - target
        
        for e in self._easeBackXEvents.copy():
            e.clear()
            self._easeBackXEvents.remove(e)
        
        myevent = threading.Event()
        myevent.set()
        self._easeBackXEvents.append(myevent)
        
        lastv, av, ast = 0.0, 0.0, time.time()
        while myevent.is_set():
            p = (time.time() - ast) / 0.75
            if p > 1.0:
                self._dx += dx - av
                self._set()
                break
            
            v = 1.0 - (1.0 - p) ** 4
            dxv = (v - lastv) * dx
            av += dxv
            self._dx += dxv
            self._set()
            lastv = v

            time.sleep(1 / 120)
        
        if need_callback:
            self.easeEndXCallback()
    
    def easeBackY(self, target: typing.Optional[float] = None, need_callback: bool = True):
        cdy = - self._dy
        if self.minValueY <= cdy <= self.maxValueY and target is None:
            return
        
        if target is None:
            if cdy < 0:
                dy = - cdy
            else:
                dy = self.maxValueY - cdy
            dy *= -1 # 前面cdy = 负的, 所以变回来
            if self._dy + dy > 0: # 超出左界
                dy = - self._dy
        else:
            dy = cdy - target
        
        for e in self._easeBackYEvents.copy():
            e.clear()
            self._easeBackYEvents.remove(e)
        
        myevent = threading.Event()
        myevent.set()
        self._easeBackYEvents.append(myevent)
        
        lastv, av, ast = 0.0, 0.0, time.time()
        while myevent.is_set():
            p = (time.time() - ast) / 0.75
            if p > 1.0:
                self._dy += dy - av
                self._set()
                break
            
            v = 1.0 - (1.0 - p) ** 4
            dyv = (v - lastv) * dy
            av += dyv
            self._dy += dyv
            self._set()
            lastv = v

            time.sleep(1 / 120)
        
        if need_callback:
            self.easeEndYCallback()

    def stopAllEase(self):
        for e in self._easeScrollEvents.copy():
            e.clear()
            self._easeScrollEvents.remove(e)
        
        for e in self._easeBackXEvents.copy():
            e.clear()
            self._easeBackXEvents.remove(e)

        for e in self._easeBackYEvents.copy():
            e.clear()
            self._easeBackYEvents.remove(e)
    
    def _set(self):
        self.setFunc(self._dx, self._dy)

    def check(self):
        threading.Thread(target=self.easeSroll, daemon=True).start()
    
class ChooseChartControler:
    def __init__(
        self, chapter: Chapter,
        w: int, h: int, # screen size
        changeUisound: dxsound.directSound,
        uistate: ChartChooseUI_State
    ):
        self.chapter = chapter
        self.uistate = uistate
        
        self._chartsShadowRect = (
            w * -0.009375, 0,
            w * 0.4921875, h
        )
        self._chartsShadowRectDPower = utils.getDPower(*utils.getSizeByRect(self._chartsShadowRect), 75)
        self._previewBgRect = (
            w * 0.4375, h * (219 / 1080),
            w * 0.9453125, h * (733 / 1080)
        )
        self._previewBgRectDPower = utils.getDPower(*utils.getSizeByRect(self._previewBgRect), 75)
        
        self.changeUisound = changeUisound
        self.itemHeight = h * (120 / 1080)
        self.itemNowDy = 0.0
        self._itemLastDy = 0.0
        
        self._slideControl = SlideControler(
            eventRect = [
                (
                    (lambda x, y: utils.indrect(x, y, self._chartsShadowRect, self._chartsShadowRectDPower) and y > h * (123 / 1080)),
                    1.0
                ),
                (
                    (lambda x, y: utils.indrect(x, y, self._previewBgRect, self._previewBgRectDPower)),
                    0.2
                )
            ],
            setFunc = self._slide_setfunc,
            minValueX = 0.0, maxValueX = 0.0,
            minValueY = 0.0, maxValueY = 0.0,
            w = h, h = h
        )
        
        self.scter_mousedown = self._slideControl.mouseDown
        self.scter_mouseup = self._slideControl.mouseUp
        self.scter_mousemove = self._slideControl.mouseMove
        self._slideControl.easeEndYCallback = self._scoll_end
        self._slideControl.easeScrollCallback = self._scoll_end
        self._slideControl.maxValueY = self.itemHeight * (len(self.chapter.songs) - 1)
        
        self._preview_events: list[threading.Event] = []
        self._preview_playing = None
        self._released = False
        self.mixer = unix_mixer
        
        self.challengeModeSelections: list[tuple[Song, SongDifficulty]] = []
        self.challengeModeSelectButtonAlpha = valueTransformer(rpe_easing.ease_funcs[0], 0.2)
        self.challengeModeSelectTextAlpha = valueTransformer(rpe_easing.ease_funcs[0], 0.2)
        self.challengeModeSelectButtonAlpha.target = 1.0
        self.challengeModeSelectTextAlpha.target = 1.0
        
        self.level_bar_rightx = valueTransformer(rpe_easing.ease_funcs[13])
        self.level_choose_x = valueTransformer(rpe_easing.ease_funcs[13])
        self.level_color = (
            valueTransformer(rpe_easing.ease_funcs[13]),
            valueTransformer(rpe_easing.ease_funcs[13]),
            valueTransformer(rpe_easing.ease_funcs[13])
        )
        self.level_diffnumber = valueTransformer(rpe_easing.ease_funcs[13])
        self.chooselevel_textsx = tuple(
            valueTransformer(rpe_easing.ease_funcs[13], 0.3)
            for _ in range(const.MAX_LEVEL_NUM)
        )
        self._set_level_bar_rightx()
        
        song = self.chapter.scsd_songs[self.vaildNowIndex]
        self.uistate.max_diffindex = len(song.difficulty) - 1
        self.set_level_callback = self._set_level_bar_rightx
        
        self._start_preview()
        self._preview_checker()
        
        self.challenge_mode_select_change_callback = self._challenge_mode_select_update
    
    def _set_level_bar_rightx(self):
        song = self.chapter.scsd_songs[self.vaildNowIndex]
        self.level_bar_rightx.target = song.level_bar_rightx_max
        
        for i in range(len(song.difficulty)):
            self.chooselevel_textsx[i].target = const.LEVEL_CHOOSE_XMAP[len(song.difficulty) - 1][i] + const.LEVEL_CHOOSE_BLOCK_WIDTH / 2
        
        self._set_level_choose_x()
    
    def _set_level_choose_x(self):
        song = self.chapter.scsd_songs[self.vaildNowIndex]
        xs = const.LEVEL_CHOOSE_XMAP[len(song.difficulty) - 1]
        self.level_choose_x.target = xs[min(self.uistate.diff_index, len(xs) - 1)]
        self._set_level_color()
        self._set_level_diffnumber()
    
    def _set_level_color(self):
        color = const.LEVEL_COLOR_MAP[min(self.uistate.diff_index, len(const.LEVEL_COLOR_MAP) - 1)]
        for i, v in enumerate(color):
            self.level_color[i].target = v
    
    def _set_level_diffnumber(self):
        song = self.chapter.scsd_songs[self.vaildNowIndex]
        self.level_diffnumber.target = song.difficulty[min(self.uistate.diff_index, len(song.difficulty) - 1)].level
        self._challenge_mode_select_update()
    
    def _challenge_mode_select_update(self):
        song = self.chapter.scsd_songs[self.vaildNowIndex]
        diff = song.difficulty[min(self.uistate.diff_index, len(song.difficulty) - 1)]
        if (song, diff) in self.challengeModeSelections:
            self.challengeModeSelectButtonAlpha.target = 0.75
            self.challengeModeSelectTextAlpha.target = 0.0
        else:
            self.challengeModeSelectButtonAlpha.target = 1.0
            self.challengeModeSelectTextAlpha.target = 1.0
    
    def get_level_color(self):
        return tuple(map(lambda x: x.value, self.level_color))
    
    def _vaild_index(self, i: int):
        return 0 <= i <= len(self.chapter.scsd_songs) - 1
    
    def _slide_setfunc(self, x: float, y: float, _fromsetto: bool = False):
        self.itemNowDy = y / self.itemHeight
        
        v1, v2 = round(-self.itemNowDy), round(-self._itemLastDy)
        
        v1_vaild = max(0, min(v1, len(self.chapter.scsd_songs) - 1))
        v2_vaild = max(0, min(v2, len(self.chapter.scsd_songs) - 1))
        
        if v1_vaild != v2_vaild:
            self.changeUisound.play()
            self._start_preview()
            self._set_level_bar_rightx()
            song = self.chapter.scsd_songs[self.vaildNowIndex]
            self.uistate.max_diffindex = len(song.difficulty) - 1
        
        self._itemLastDy = self.itemNowDy
    
    def _scoll_end(self):
        if -self.itemNowDy < 0: return
        if -self.itemNowDy >= len(self.chapter.scsd_songs) - 1: return
        
        targetDy = min(max(0, round(-self.itemNowDy)), len(self.chapter.scsd_songs) - 1) * self.itemHeight
        self._slideControl.easeBackY(targetDy, False)
    
    def _toae(self):
        for e in self._preview_events.copy():
            e.clear()
            self._preview_events.remove(e)
        
        myevent = threading.Event()
        myevent.set()
        self._preview_events.append(myevent)
        
        return myevent
    
    @utils.runByThread
    def _start_preview(self):
        myevent = self._toae()
        song = self.chapter.scsd_songs[self.vaildNowIndex]
        mixer = self.mixer
        self._preview_playing = song
        
        if mixer.music.get_busy():
            fadeout = 500
            mixer.music.fadeout(fadeout)
            
            st = time.time()
            while myevent.is_set() and not self._released:
                if time.time() - st > fadeout / 1000:
                    break
                
                time.sleep(1 / 20)
            
        if not myevent.is_set() or self._released:
            return
        
        mixer.music.load(utils.gtpresp(song.preview), needlength=False)
        if not myevent.is_set() or self._released: return
        mixer.music.play()
        mixer.music.set_volume(0.0)
        mixer.music.set_pos(song.preview_start)
        
        st = time.time()
        while myevent.is_set() and not self._released:
            if not mixer.music.get_busy():
                break
            
            p = (time.time() - st) / 0.5
            if p > 1.0: break
            
            mixer.music.set_volume(p)
        
        if not myevent.is_set() or self._released:
            return
        
        mixer.music.set_volume(1.0)
    
    @utils.runByThread
    def _preview_checker(self):
        while not self._released:
            time.sleep(1 / 10)
            
            if not self.mixer.music.get_busy() or self._preview_playing is None:
                continue
            
            nowpos = self.mixer.music.get_pos() + self._preview_playing.preview_start
            if nowpos > self._preview_playing.preview_end:
                if self._released: return
                myevent = self._toae()
                fadeout = 500
                self.mixer.music.fadeout(fadeout)
                
                st = time.time()
                while myevent.is_set() and not self._released:
                    if time.time() - st > fadeout / 1000:
                        break

                    time.sleep(1 / 20)
                
                if self._preview_playing is not None:
                    self._start_preview()
    
    def setto_index(self, index: int):
        if index == self.nowIndex: return
        targetDy = min(max(0, index), len(self.chapter.scsd_songs) - 1) * self.itemHeight
        self._slideControl.stopAllEase()
        self._slideControl.setDy(-targetDy)
        self._slide_setfunc(0, -targetDy, True)
    
    def setto_index_ease(self, index: int):
        targetDy = min(max(0, index), len(self.chapter.scsd_songs) - 1) * self.itemHeight
        self._slideControl.easeBackY(targetDy, False)
    
    @property
    def _valueters(self):
        return (
            self.level_bar_rightx,
            self.level_choose_x,
            *self.level_color,
            self.level_diffnumber,
            *self.chooselevel_textsx
        )
    
    def enable_valueter(self):
        for valueter in self._valueters:
            valueter.enable = True
    
    def disable_valueter(self):
        for valueter in self._valueters:
            valueter.enable = False
    
    def __del__(self):
        self._toae()
        self._released = True
        self._preview_playing = None
    
    @property
    def nowIndex(self):
        return int(round(-self.itemNowDy))
    
    @property
    def vaildNowCeil(self):
        return max(0, min(int(-self.itemNowDy), len(self.chapter.scsd_songs) - 1))
    
    @property
    def vaildNowNextCeil(self):
        return max(0, min(int(-self.itemNowDy) + 1, len(self.chapter.scsd_songs) - 1))
    
    @property
    def vaildNowIndex(self):
        return max(0, min(self.nowIndex, len(self.chapter.scsd_songs) - 1))
    
    @property
    def vaildNextIndex(self):
        return max(0, min(self.nowIndex + 1, len(self.chapter.scsd_songs) - 1))
    
    @property
    def vaildNowFloatIndex(self):
        return max(0, min(-self.itemNowDy, len(self.chapter.scsd_songs) - 1))
        
@dataclasses.dataclass
class ChartChooseUI_State:
    change_diff_sound: dxsound.directSound
    sort_reverse: bool = False
    sort_method: int = const.PHI_SORTMETHOD.DEFAULT
    is_mirror: bool = False
    is_autoplay: bool = False
    diff_index: int = 0
    
    change_diff_callback: typing.Callable[[], typing.Any] = lambda: None
    
    def __post_init__(self):
        self._max_diffindex = const.MAX_LEVEL_NUM - 1
            
    def next_sort_method(self):
        tempmethod = self.sort_method + 1
        
        if tempmethod > const.PHI_SORTMETHOD.SCORE:
            tempmethod = const.PHI_SORTMETHOD.DEFAULT
            
        self.sort_method = tempmethod
    
    def change_mirror(self):
        self.is_mirror = not self.is_mirror
    
    def change_autoplay(self):
        self.is_autoplay = not self.is_autoplay
    
    def change_diff(self, i: int):
        self.diff_index = min(i, self.max_diffindex)
        self.change_diff_callback()
    
    def change_diff_byuser(self, i: int):
        olddiff = self.diff_index
        self.change_diff(i)
        
        if olddiff != i:
            self.change_diff_sound.play()
    
    def dosort(self, chapter: Chapter, getScore: typing.Callable[[Song], float]):
        newsongs = chapter.songs.copy()
        
        match self.sort_method:
            case const.PHI_SORTMETHOD.DEFAULT:
                pass
            
            case const.PHI_SORTMETHOD.SONG_NAME:
                newsongs.sort(key=lambda x: ord(x.name[0]))
            
            case const.PHI_SORTMETHOD.DIFFICULTY:
                newsongs.sort(key=lambda x: x.difficulty[self.diff_index].level if self.diff_index <= len(x.difficulty) - 1 else -1.0)
            
            case const.PHI_SORTMETHOD.SCORE:
                newsongs.sort(key=getScore)
        
        if self.sort_reverse:
            newsongs.reverse()
        
        return newsongs
    
    @property
    def max_diffindex(self):
        return self._max_diffindex
    
    @max_diffindex.setter
    def max_diffindex(self, value: int):
        self._max_diffindex = value
        self.change_diff(self.diff_index)

@dataclasses.dataclass
class valueTransformer:
    ease: typing.Callable[[float], float] = lambda x: x
    animation_time: float = 0.5
    
    def __post_init__(self):
       self._last_change = float("-inf")
       self._last_value = float("-inf")
       self._target_value = float("-inf")
       self._inited = False
       self._enable = True
    
    def init(self, value: float):
        self._last_value = value
        self._last_change = time.time()
        self._target_value = value
    
    def updater(self):
        if self._last_change == float("-inf"):
            self._value = self._target_value
            return
        
        p = (time.time() - self._last_change) / self.animation_time
        
        if p > 1.0:
            self._value = self._target_value
        else:
            self._value = utils.easing_interpolation(
                p, 0.0, 1.0,
                self._last_value, self._target_value,
                self.ease
            )
    
    @property
    def target(self):
        return self._target_value
    
    @target.setter
    def target(self, value: float):
        if not self._inited:
            self._inited = True
            self.init(value)
            
        self._last_value = self.value
        self._last_change = time.time()
        self._target_value = value
    
    @property
    def value(self):
        self.updater()
        return self._value

    @property
    def enable(self):
        return self._inited

    @enable.setter
    def enable(self, value: bool):
        self._inited = value
