from __future__ import annotations

import time
import typing
import logging
import threading
import sys
from dataclasses import dataclass
from queue import Queue

from PIL import Image

import webcv
import const
import utils
import rpe_easing
import phi_tips
import dxsound
import phira_respack
import phichart
from dxsmixer import mixer
from graplib_webview import *

drawUIDefaultKwargs = {
    f"{k}_{k2}": v
    for k in ("combonumber", "combo", "score", "name", "level", "pause", "bar")
    for k2, v in (("dx", 0.0), ("dy", 0.0), ("scaleX", 1.0), ("scaleY", 1.0), ("color", "rgba(255, 255, 255, 1.0)"))
}
mainFramerateCalculator = utils.FramerateCalculator()

def initGlobalSettings():
    global enableMirror, enableWatermark
    global FCAPIndicator, noanimation
    
    enableMirror = False
    enableWatermark = True
    FCAPIndicator = True
    noanimation = "--noanimation" in sys.argv

initGlobalSettings()

# set in phigros.py
MirrorIconWidth: int
MirrorIconHeight: int

class settlementAnimationUserData:
    # every instance share those variables
    avatar: typing.Optional[Image.Image] = None
    userName: str = "GUEST"
    rankingScore: float = 16.0
    hasChallengeMode: bool = True
    challengeModeRank: int = 548
    
    def init(self):
        root.run_js_code(f"delete {root.get_img_jsvarname("user_avatar")};")
        respacker = webcv.PILResPacker(root)
        respacker.reg_img(self.avatar, "user_avatar")
        respacker.load(*respacker.pack())
        
        self.userNameConstFontSize = (w + h) / const.USERNAME_CONST_FONT
        self.userNamePadding = w * 0.01
        self.userNameWidth = root.run_js_code(f"ctx.getTextSize({repr(self.userName)}, '{self.userNameConstFontSize}px pgrFont')[0];") + self.userNamePadding * 2

@dataclass
class PhiCoreConfig:
    SETTER: typing.Callable[[str, typing.Any], typing.Any]
    
    root: webcv.WebCanvas
    w: int; h: int
    
    chart_information: dict
    chart_obj: phichart.CommonChart
    
    Resource: dict
    globalNoteWidth: float
    note_max_size_half: float
    raw_audio_length: float
    
    chart_res: dict[str, tuple[typing.Optional[Image.Image], tuple[int, int]]]
    cksmanager: ClickSoundManager
    clickeffect_randomblock_roundn: float = 0.0
    enable_clicksound: bool = True
    rtacc: bool = False
    noautoplay: bool = False
    showfps: bool = False
    speed: float = 1.0
    render_range_more: bool = False
    render_range_more_scale: float = 2.0
    debug: bool = False
    combotips: str = "AUTOPLAY"
    noplaychart: bool = False
    clicksound_volume: float = 1.0
    musicsound_volume: float = 1.0
    
def CoreConfigure(config: PhiCoreConfig):
    global SETTER
    global root, w, h, chart_information
    global chart_obj
    global Resource
    global globalNoteWidth
    global note_max_size_half
    global raw_audio_length
    global clickeffect_randomblock_roundn
    global chart_res, cksmanager
    global enable_clicksound, rtacc, noautoplay
    global showfps
    global speed, render_range_more
    global render_range_more_scale
    global debug, combotips, noplaychart
    
    SETTER = config.SETTER
    root = config.root
    w, h = config.w, config.h
    chart_information = config.chart_information
    chart_obj = config.chart_obj
    Resource = config.Resource
    globalNoteWidth = config.globalNoteWidth
    note_max_size_half = config.note_max_size_half
    raw_audio_length = config.raw_audio_length
    clickeffect_randomblock_roundn = config.clickeffect_randomblock_roundn
    chart_res = config.chart_res
    cksmanager = config.cksmanager
    enable_clicksound = config.enable_clicksound
    rtacc = config.rtacc
    noautoplay = config.noautoplay
    showfps = config.showfps
    speed = config.speed
    render_range_more = config.render_range_more
    render_range_more_scale = config.render_range_more_scale
    debug = config.debug
    combotips = config.combotips
    noplaychart = config.noplaychart
    
    if Resource["Note_Click_Audio"] is not None: # use in tools
        mixer.music.set_volume(config.musicsound_volume)
        for i in Resource["Note_Click_Audio"].values():
            i.set_volume(config.clicksound_volume)
    
    logging.info("CoreConfigure Done")

class ClickSoundManager:
    def __init__(self, res: dict[int, dxsound.directSound]):
        self.res = res
        self.queue: Queue[typing.Optional[int]] = Queue()
        
        for _ in range(const.CSOUND_MANAGER_THREADNUM):
            threading.Thread(target=self.runner, daemon=True).start()
    
    def play(self, nt: int):
        self.queue.put(nt)
    
    def stop(self):
        self.queue.put(None)
    
    def runner(self):
        while True:
            nt = self.queue.get()
            if nt is None:
                self.queue.put(None)
                break
            
            self.res[nt].play()

def processClickEffectBase(
    x: float, y: float, rotate: float,
    p: float, rblocks: typing.Optional[tuple[tuple[float, float]]],
    perfect: bool, noteWidth: float,
    root: webcv.WebCanvas,
    rblocks_roundn: float = 0.0
):
    if rblocks is None: rblocks = utils.newRandomBlocks()
    
    color = (
        (phira_respack.globalPack.perfectRGB if not phira_respack.globalPack.isdefault_perfect else (255, 236, 160))
        if perfect else
        phira_respack.globalPack.goodRGB
    )
    
    alpha = (
        phira_respack.globalPack.perfectAlpha
        if perfect else
        phira_respack.globalPack.goodAlpha
    ) / 255
    
    imn = f"Note_Click_Effect_{"Perfect" if perfect else "Good"}"
    effectSize = noteWidth * 1.375 * 1.12
    
    if not phira_respack.globalPack.hideParticles:
        real_sec = p * phira_respack.globalPack.effectDuration
        s = w * (noteWidth / (w * const.NOTE_DEFAULTSIZE)) / 4040 * 3
        nowBlockSize = s * 33 * utils.UnityCurve(const.PGR_PARTICLE_DATA["sizeCurves"], p)
        
        for i, (deg, randdr) in enumerate(rblocks):
            block_st = i * const.PGR_PARTICLE_DATA["spwanTime"]
            if real_sec < block_st: continue
            pointr = s * randdr * (9 * p / (8 * p + 1))
            
            if pointr < 0.0: continue
            
            point = utils.rotate_point(x, y, deg, pointr)
            addRoundRectData(
                point[0] - nowBlockSize / 2,
                point[1] - nowBlockSize / 2,
                nowBlockSize, nowBlockSize,
                nowBlockSize * rblocks_roundn,
                wait_execute = True
            )
        
        drawRoundDatas(f"rgba{color + (1.0 - p, )}", wait_execute = True)
    
    effectImageSize = effectSize * phira_respack.globalPack.effectScale
    (drawMirrorRotateImage if enableMirror else drawRotateImage)(
        f"{imn}_{int(p * (phira_respack.globalPack.effectFrameCount - 1)) + 1}",
        x, y,
        effectImageSize, effectImageSize,
        rotate if phira_respack.globalPack.effectRotate else 0.0, alpha,
        wait_execute = True
    )

def processClickEffect(
    x: float, y: float, rotate: float,
    p: float, rblocks: tuple[tuple[float, float]],
    perfect: bool
):
    return processClickEffectBase(
        x = x, y = y, rotate = rotate,
        p = p,
        rblocks = rblocks,
        perfect = perfect,
        noteWidth = globalNoteWidth,
        root = root,
        rblocks_roundn = clickeffect_randomblock_roundn
    )

def processBadEffect(
    x: float, y: float, rotate: float, st: float, now_t: float, bdfi_t: float,
    caller: typing.Callable[[typing.Callable, typing.Any], typing.Any] = lambda f, *args, **kwargs: f(*args, **kwargs)
):
    p = (now_t - st) / bdfi_t
    this_note_img = Resource["Notes"]["Bad"]
    caller(
        drawRotateImage,
        "Note_Bad",
        x * w, y * h,
        globalNoteWidth,
        globalNoteWidth / this_note_img.width * this_note_img.height,
        rotate,
        1 - p ** 3,
        wait_execute = True
    )

def getHoldDrawPosition(
    x: float, y: float,
    width: float,
    height_b: float,
    img_h: Image.Image,
    img_e: Image.Image,
    rotate: float,
    hadhead: bool
):
    height_h = width / img_h.width * img_h.height
    height_e = width / img_e.width * img_e.height
    height_b = max(0.0, height_b - height_e)
    
    headpos = (x, y)
    bodypos = utils.rotate_point(*headpos, rotate, height_h / 2) if hadhead and not phira_respack.globalPack.holdCompact else headpos
    endpos = utils.rotate_point(*bodypos, rotate, height_b + ((height_e / 2) if not phira_respack.globalPack.holdCompact else 0.0))
    
    _headheadpos = utils.rotate_point(*headpos, rotate, -height_h / 2)
    _endendpos = utils.rotate_point(*endpos, rotate, height_e / 2)
    
    holdrect = (
        utils.rotate_point(*_headheadpos, rotate - 90, width / 2),
        utils.rotate_point(*_headheadpos, rotate + 90, width / 2),
        utils.rotate_point(*_endendpos, rotate + 90, width / 2),
        utils.rotate_point(*_endendpos, rotate - 90, width / 2)
    )
    
    return (
        headpos,
        bodypos,
        endpos,
        holdrect,
        (height_b, )
    )

def stringifyScore(score: float) -> str:
    score_integer = int(score + 0.5)
    return f"{score_integer:>07}"

def drawDeepBgAndClipScreen():
    outOfTransformDrawCoverFullscreenChartBackgroundImage("background_blur", wait_execute=True)
    
    ctxSave(wait_execute=True)
    ctxBeginPath(wait_execute=True)
    ctxRect(0, 0, w, h, wait_execute=True)
    ctxClip(wait_execute=True)

def undoClipScreen():
    ctxRestore(wait_execute=True)

def drawBg():
    drawCoverFullScreenImage("background_blur", w, h, wait_execute=True)
    fillRectEx(0, 0, w, h, f"rgba(0, 0, 0, {chart_information["BackgroundDim"]})", wait_execute=True)

# color 一定要传 rgba 的
def draw_ui(
    process: float = 0.0,
    score: str = "0000000",
    combo_state: bool = False,
    combo: int = 0,
    acc: str = "100.00%",
    clear: bool = True,
    background: bool = True,
    animationing: bool = False,
    dy: float = 0.0,
    
    combonumberUI_dx: float = 0.0,
    combonumberUI_dy: float = 0.0,
    combonumberUI_scaleX: float = 1.0,
    combonumberUI_scaleY: float = 1.0,
    combonumberUI_color: str = "rgba(255, 255, 255, 1.0)",
    combonumberUI_rotate: float = 0.0,
    
    comboUI_dx: float = 0.0,
    comboUI_dy: float = 0.0,
    comboUI_scaleX: float = 1.0,
    comboUI_scaleY: float = 1.0,
    comboUI_color: str = "rgba(255, 255, 255, 1.0)",
    comboUI_rotate: float = 0.0,
    
    scoreUI_dx: float = 0.0,
    scoreUI_dy: float = 0.0,
    scoreUI_scaleX: float = 1.0,
    scoreUI_scaleY: float = 1.0,
    scoreUI_color: str = "rgba(255, 255, 255, 1.0)",
    scoreUI_rotate: float = 0.0,
    
    nameUI_dx: float = 0.0,
    nameUI_dy: float = 0.0,
    nameUI_scaleX: float = 1.0,
    nameUI_scaleY: float = 1.0,
    nameUI_color: str = "rgba(255, 255, 255, 1.0)",
    nameUI_rotate: float = 0.0,
    
    levelUI_dx: float = 0.0,
    levelUI_dy: float = 0.0,
    levelUI_scaleX: float = 1.0,
    levelUI_scaleY: float = 1.0,
    levelUI_color: str = "rgba(255, 255, 255, 1.0)",
    levelUI_rotate: float = 0.0,
    
    pauseUI_dx: float = 0.0, # in fact, timeUI...
    pauseUI_dy: float = 0.0,
    pauseUI_scaleX: float = 1.0,
    pauseUI_scaleY: float = 1.0,
    pauseUI_color: str = "rgba(255, 255, 255, 1.0)",
    pauseUI_rotate: float = 0.0,
    
    barUI_dx: float = 0.0,
    barUI_dy: float = 0.0,
    barUI_scaleX: float = 1.0,
    barUI_scaleY: float = 1.0,
    barUI_color: str = "rgba(255, 255, 255, 1.0)",
    barUI_rotate: float = 0.0
):
    if clear: clearCanvas(wait_execute = True)
    if background:
        drawBg()
    
    pauseImgWidth = w * (32 / 1920)
    pauseImgHeight = pauseImgWidth / 35 * 41
    
    pauseImgWidth *= pauseUI_scaleX
    pauseImgHeight *= pauseUI_scaleY
    
    pauseImgRGBA = list(map(float, pauseUI_color.replace(" ", "").replace("rgba", "").replace("(", "").replace(")", "").split(",")))
    fps = mainFramerateCalculator.framerate
    reqaf_fps = root.get_framerate()
    
    uidata = [
        {
            "type": "call",
            "name": "translate", "args": [0, - h / 7  + dy]
        } if animationing else None,
        {
            "type": "pbar",
            "w": w, "pw": h / 95,
            "process": process,
            "dx": barUI_dx, "dy": barUI_dy,
            "sx": barUI_scaleX, "sy": barUI_scaleY,
            "color": barUI_color, "rotate": barUI_rotate
        },
        {
            "type": "text",
            "text": f"{score}", "fontsize": (w + h) / 75 / 0.75,
            "textBaseline": "top", "textAlign": "right",
            "x": w * (1 - (40 / 1920)), "y": h * (31 / 1080),
            "dx": scoreUI_dx, "dy": scoreUI_dy,
            "sx": scoreUI_scaleX, "sy": scoreUI_scaleY,
            "color": scoreUI_color, "rotate": scoreUI_rotate
        },
        {
            "type": "text",
            "text": f"{acc}", "fontsize": (w + h) / 145 / 0.75,
            "textBaseline": "top", "textAlign": "right",
            "x": w * (1 - (40 / 1920)), "y": h * (85 / 1080),
            "dx": 0.0, "dy": 0.0,
            "sx": scoreUI_scaleX, "sy": scoreUI_scaleY,
            "color": scoreUI_color, "rotate": scoreUI_rotate
        } if rtacc else None,
        {
            "type": "text",
            "text": f"{combo}", "fontsize": (w + h) / 53 / 0.75,
            "textBaseline": "middle", "textAlign": "center",
            "x": w / 2, "y": h * (52 / 1080),
            "dx": combonumberUI_dx, "dy": combonumberUI_dy,
            "sx": combonumberUI_scaleX, "sy": combonumberUI_scaleY,
            "color": combonumberUI_color, "rotate": combonumberUI_rotate
        } if combo_state else None,
        {
            "type": "text",
            "text": f"{combotips}", "fontsize": (w + h) / 160 / 0.75,
            "textBaseline": "top", "textAlign": "center",
            "x": w / 2, "y": h * 0.085,
            "dx": comboUI_dx, "dy": comboUI_dy,
            "sx": comboUI_scaleX, "sy": comboUI_scaleY,
            "color": comboUI_color, "rotate": comboUI_rotate
        } if combo_state else None,
        {
            "type": "image",
            "image": root.get_img_jsvarname("PauseImg"),
            "x": w * (36 / 1920), "y": h * (41 / 1080),
            "dx": pauseUI_dx, "dy": pauseUI_dy,
            "width": pauseImgWidth, "height": pauseImgHeight,
            "rotate": pauseUI_rotate, "color": pauseImgRGBA
        },
        {
            "type": "call",
            "name": "translate", "args": [0, -2 * (- h / 7 + dy)]
        } if animationing else None,
        {
            "type": "text",
            "text": chart_information["Name"], "fontsize": (w + h) / 115 / 0.75,
            "textBaseline": "bottom", "textAlign": "left",
            "x": w * 0.0225, "y": h * 0.965,
            "dx": nameUI_dx, "dy": nameUI_dy,
            "sx": nameUI_scaleX, "sy": nameUI_scaleY,
            "color": nameUI_color, "rotate": nameUI_rotate
        },
        {
            "type": "text",
            "text": chart_information["Level"], "fontsize": (w + h) / 115 / 0.75,
            "textBaseline": "bottom", "textAlign": "right",
            "x": w * 0.9775, "y": h * 0.965,
            "dx": levelUI_dx, "dy": levelUI_dy,
            "sx": levelUI_scaleX, "sy": levelUI_scaleY,
            "color": levelUI_color, "rotate": levelUI_rotate
        },
        {
            "type": "text",
            "text": f"fps {fps:.0f} - reqaf fps {reqaf_fps:.0f}", "fontsize": (w + h) / 275 / 0.75,
            "textBaseline": "bottom", "textAlign": "center",
            "x": w * 0.5, "y": h * 0.975,
            "dx": 0.0, "dy": 0.0,
            "sx": 1.0, "sy": 1.0,
            "color": "rgba(255, 255, 255, 0.5)", "rotate": 0.0
        } if showfps else None,
        {
            "type": "text",
            "text": "phispler - by qaqFei - github.com/qaqFei/phispler - MIT License",
            "fontsize": (w + h) / 275 / 0.75,
            "textBaseline": "bottom", "textAlign": "center",
            "x": w * 0.5, "y": h * 0.99,
            "dx": 0.0, "dy": 0.0,
            "sx": 1.0, "sy": 1.0,
            "color": "rgba(255, 255, 255, 0.5)", "rotate": 0.0
        } if enableWatermark else None,
        {
            "type": "call",
            "name": "translate", "args": [0, - h / 7 + dy]
        } if animationing else None
    ]
    
    root.run_js_code(f"ctx.drawUIItems({uidata});", wait_execute = True)
    mainFramerateCalculator.frame()
             
def delDrawuiDefaultVals(kwargs: dict) -> dict:
    return {k: v for k, v in kwargs.items() if v != drawUIDefaultKwargs.get(k, None)}   

def drawDebugText(text: str, x: float, y: float, rotate: float, color: str):
    root.run_js_code(
        f"ctx.drawRotateText(\
            {repr(text)},\
            {",".join(map(str, utils.rotate_point(x, y, rotate, (w + h) / 75)))},\
            {90 + rotate}, {(w + h) / 85 / 0.75}, '{color}', 1.0, 1.0\
        );",
        wait_execute = True,
        order = const.CHART_RENDER_ORDERS.DEBUG
    )

def rrmStart():
    if not render_range_more: return
    lw, lh = w / render_range_more_scale, h / render_range_more_scale
    lr, lt = w / 2 - lw / 2, h / 2 - lh / 2
    rms = 1 / render_range_more_scale
    
    ctxSave(wait_execute=True)
    ctxTranslate(lr, lt, wait_execute=True)
    ctxScale(rms, rms, wait_execute=True)

def rrmEnd():
    if not render_range_more: return
    ctxRestore(wait_execute=True)
    
def processExTask(extasks: list[tuple[str, typing.Any]]):
    break_flag = False
    
    for ext in extasks:
        match ext[0]:
            case "break":
                break_flag = True
                
            case "psound":
                cksmanager.play(ext[1])
        
    return break_flag

def renderChart_Common(
    now_t: float, clear: bool = True, rjc: bool = True,
    pplm: typing.Optional[utils.PhigrosPlayLogicManager] = None,
    need_deepbg: bool = True, editing_line: typing.Optional[int] = None
):
    extasks = []
    
    if clear:
        clearCanvas(wait_execute=True)
    
    rrmStart()
    
    if need_deepbg:
        drawDeepBgAndClipScreen()
        
    drawBg()
    
    if noplaychart:
        extasks.append(("break", ))
    
    attachUIData = {}
    
    now_t *= speed
    now_t -= chart_obj.offset
    
    if chart_obj.extra is not None and chart_obj.extra.videos:
        for video, progress in chart_obj.extra.getVideoEffect(now_t):
            video_ratio = video.size[0] / video.size[1]
            user_ratio = w / h
            
            match video.scale:
                case "cropCenter":
                    if video_ratio > user_ratio:
                        video_size = (h * video_ratio, h)
                    else:
                        video_size = (w, w / video_ratio)
                
                case "inside":
                    if video_ratio > user_ratio:
                        video_size = (w, w / video_ratio)
                    else:
                        video_size = (h * video_ratio, h)
                
                case "fit":
                    video_size = (w, h)
                
                case _:
                    assert False, f"Unknown video scale: {video.scale}"
            
            video_pos = (
                (w - video_size[0]) / 2,
                (h - video_size[1]) / 2
            )
            root.wait_jspromise(f"setVideoTime({root.get_img_jsvarname(video.unqique_id)}, {progress});")
            drawImage(
                video.unqique_id,
                *video_pos,
                *video_size,
                wait_execute = True
            )
    
    noautoplay = pplm is not None
    
    if noautoplay:
        pplm.mob_update(now_t)
        pplm.pc_update(now_t)
    
    nowLineColor = (phira_respack.globalPack.perfectRGB if not noautoplay else pplm.ppps.getLineColor()) if FCAPIndicator else (255, 255, 255)
    nowLineWidth, nowLineHeight = (
        w * chart_obj.options.lineWidthUnit[0] + h * chart_obj.options.lineWidthUnit[1],
        w * chart_obj.options.lineHeightUnit[0] + h * chart_obj.options.lineHeightUnit[1]
    )
    
    rendered_hash_count = {}
    
    for line in chart_obj.sorted_lines:
        (
            linePos,
            lineAlpha,
            lineRotate,
            
            lineScaleX,
            lineScaleY,
            lineText,
            lineColor
        ) = line.getState(now_t, nowLineColor)
        
        if line.index == editing_line:
            lineColor = (147, 255, 145)
        
        linePos = (linePos[0] * w, linePos[1] * h)
        lineDrawPos = (
            *utils.rotate_point(*linePos, lineRotate, nowLineWidth / 2 * lineScaleX),
            *utils.rotate_point(*linePos, lineRotate, -nowLineWidth / 2 * lineScaleX)
        )
        lineWebColor = f"rgba{(*lineColor, max(0.0, lineAlpha))}"
        lineWidth = nowLineHeight * lineScaleY
        negAlpha = lineAlpha < 0.0
        
        if line.isAttachUI:
            if line.attachUI in ("combonumber", "combo", "score", "name", "level", "pause", "bar"): # cannot merge with above if statement
                attachUIData.update({
                    f"{line.attachUI}UI_dx": linePos[0] - w / 2,
                    f"{line.attachUI}UI_dy": linePos[1] - h / 2,
                    f"{line.attachUI}UI_scaleX": lineScaleX,
                    f"{line.attachUI}UI_scaleY": lineScaleY,
                    f"{line.attachUI}UI_color": lineWebColor,
                    f"{line.attachUI}UI_rotate": lineRotate
                })
        elif lineAlpha > 0.0:
            if line.isTextureLine:
                texture_width, texture_height = utils.conimgsize(*chart_res[line.texture][1], w, h)
                texture_width *= lineScaleX; texture_height *= lineScaleY
                if utils.TextureLine_CanRender(w, h, (texture_width ** 2 + texture_height ** 2) ** 0.5 / 2, *linePos):
                    texturename = f"lineTexture_{line.index}"
                    texturename_js = root.get_img_jsvarname(texturename)
                    if line.isGifLine:
                        root.run_js_code(
                            f"{texturename_js}.currentTime = {now_t} % {texturename_js}.duration;",
                            wait_execute = True
                        )
                    with ColorMultiplyFilter(lineColor, const.CHART_RENDER_ORDERS.LINE):
                        setOrder(const.CHART_RENDER_ORDERS.LINE)
                        drawRotateImage(
                            texturename,
                            *linePos,
                            texture_width,
                            texture_height,
                            lineRotate,
                            lineAlpha,
                            wait_execute = True
                        )
                        setOrder(None)
            elif lineText is not None:
                root.run_js_code(
                    f"ctx.drawRPEMultipleRotateText(\
                        {repr(lineText)},\
                        {linePos[0]},\
                        {linePos[1]},\
                        {lineRotate},\
                        {(w + h) / 75 * 1.35},\
                        '{lineWebColor}',\
                        {lineScaleX},\
                        {lineScaleY}\
                    );",
                    wait_execute = True,
                    order = const.CHART_RENDER_ORDERS.LINE
                )
            elif utils.lineInScreen(w, h, lineDrawPos):
                setOrder(const.CHART_RENDER_ORDERS.LINE)
                drawLine(*lineDrawPos, lineWidth, lineWebColor, wait_execute=True)
                setOrder(None)
        
        if debug:
            drawDebugText(f"{line.index}{"" if not line.index == editing_line else " (editing)"}", *linePos, lineRotate - 90, "rgba(255, 255, 170, 0.5)")
                            
            root.run_js_code(
                f"ctx.fillRectEx(\
                    {linePos[0] - (w + h) / 250},\
                    {linePos[1] - (w + h) / 250},\
                    {(w + h) / 250 * 2},\
                    {(w + h) / 250 * 2},\
                    'rgb(238, 130, 238)'\
                );",
                wait_execute = True,
                order = const.CHART_RENDER_ORDERS.DEBUG
            )
        
        line.playingFloorPosition = line.getFloorPosition(now_t)
        
        for notesChildren in line.renderNotes.copy():
            for note, remove_this in notesChildren:
                note_isontime = note.time < now_t
                
                if note_isontime and not note.isontime:
                    note.isontime = True
                    if enable_clicksound and not note.isFake and not noautoplay:
                        extasks.append(("psound", note.hitsound_reskey))
                
                if not note.ishold and note.isontime:
                    remove_this()
                    continue
                elif note.ishold and note.holdEndTime < now_t:
                    remove_this()
                    continue
                elif chart_obj.options.has_feature(phichart.CommonChartOptionFeatureFlags.ZERO_SPPED_HOLD_HIDDEN) and note.ishold and note.speed == 0.0:
                    continue
                elif noautoplay and note.state == const.NOTE_STATE.BAD:
                    remove_this()
                    continue
                elif noautoplay and not note.ishold and note.player_clicked:
                    remove_this()
                    continue
                
                noteFloorPosition = (
                    (note.floorPosition - (
                        line.playingFloorPosition
                        if not (chart_obj.options.holdIndependentSpeed and note.ishold and note.isontime) else
                        (note.floorPosition + utils.linear_interpolation(
                            now_t, note.time, note.holdEndTime, 0.0, note.holdLength
                        ))
                    ))
                    * h * (
                        note.speed 
                        if not (note.ishold and chart_obj.options.holdIndependentSpeed) else
                        1.0
                    )
                    + note.yOffset * h
                )
                
                if chart_obj.options.has_feature(phichart.CommonChartOptionFeatureFlags.HIGH_NOTE_FP_HIDDEN) and noteFloorPosition > h * 2:
                    continue
                
                if chart_obj.options.has_feature(phichart.CommonChartOptionFeatureFlags.NEG_LINE_ALPHA_HIDDEN) and negAlpha:
                    continue
                
                if line.enableCover and noteFloorPosition < const.FLOAT_LESSZERO_MAGIC and not note.isontime:
                    if not note.ishold or (note.ishold and chart_obj.options.holdCoverAtHead):
                        continue

                noteAtLinePos = utils.rotate_point(*linePos, lineRotate, note.positionX * w)
                lineToNoteRotate = lineRotate + (-90 if note.isAbove else 90)
                x, y = utils.rotate_point(*noteAtLinePos, lineToNoteRotate, noteFloorPosition)
                
                noteAlpha = note.alpha
                noteWidthX = note.width
                
                if chart_obj.options.enableOverlappedNoteOptimization:
                    note_render_hash = hash((x, y, note.type, lineToNoteRotate, noteAlpha, noteWidthX))
                    if note_render_hash not in rendered_hash_count:
                        rendered_hash_count[note_render_hash] = 0
                    
                    if rendered_hash_count[note_render_hash] > chart_obj.options.overlappedNoteOptimizationLimit:
                        continue
                
                    rendered_hash_count[note_render_hash] += 1
                
                note.nowpos = (x / w, y / h)
                note.nowrotate = lineToNoteRotate + 90
                
                noteImg = Resource["Notes"][note.img_keyname]
                noteWidth = globalNoteWidth * (phira_respack.globalPack.dub_fixscale[note.type] if note.morebets else 1.0)
                noteHadHead = not (note.ishold and note.isontime) or phira_respack.globalPack.holdKeepHead
                
                if note.alwaysHasHoldHead is not None:
                    noteHadHead = note.alwaysHasHoldHead
                
                if note.ishold:
                    noteEndImg = Resource["Notes"][note.img_end_keyname]
                    holdLength = note.holdLength * h * (note.speed if not chart_obj.options.holdIndependentSpeed else 1.0)
                    holdEndFloorPosition = noteFloorPosition + holdLength
                    bodyLength = holdEndFloorPosition if note.isontime else holdLength
                    
                    if not chart_obj.options.holdCoverAtHead and line.enableCover and holdEndFloorPosition < 0:
                        continue
                    
                    headpos, bodypos, endpos, holdrect, (bodyLength, ) = getHoldDrawPosition(
                        *(noteAtLinePos if note.isontime else (x, y)),
                        noteWidth, bodyLength,
                        noteImg, noteEndImg,
                        lineToNoteRotate,
                        noteHadHead
                    )
                
                if noteFloorPosition > note_max_size_half:
                    nlOutOfScreen_nohold = utils.noteLineOutOfScreen(
                        x, y, noteAtLinePos,
                        noteFloorPosition,
                        lineRotate, nowLineWidth,
                        lineToNoteRotate,
                        w, h, note_max_size_half
                    )
                    
                    nlOutOfScreen_hold = True if not note.ishold else utils.noteLineOutOfScreen(
                        x, y, noteAtLinePos,
                        holdEndFloorPosition, lineRotate, nowLineWidth,
                        lineToNoteRotate, w, h, note_max_size_half
                    )
                    
                    if nlOutOfScreen_nohold and nlOutOfScreen_hold:
                        break
                
                noteCanRender = (
                    utils.noteCanRender(w, h, note_max_size_half, x, y)
                    if not note.ishold
                    else utils.noteCanRender(w, h, -1, x, y, holdrect)
                ) and now_t >= 0.0 and (
                    note.visibleTime is None or
                    note.time - now_t <= note.visibleTime
                )
                
                if noteCanRender:
                    noteRotate = lineRotate + note.rotate_add
                    noteHeight = noteWidth / noteImg.width * noteImg.height
                    
                    if noteHadHead:
                        setOrder(note.draworder)
                        drawRotateImage(
                            note.imgname,
                            *(headpos if note.ishold else (x, y)),
                            noteWidth * noteWidthX,
                            noteHeight,
                            noteRotate,
                            noteAlpha,
                            wait_execute = True
                        )
                        setOrder(None)
                    
                    if note.ishold:
                        noteEndHeight = noteWidth / noteEndImg.width * noteEndImg.height
                        missAlpha = 0.5 if noautoplay and note.player_missed else 1.0
                        
                        setOrder(note.draworder)
                        drawRotateImage(
                            note.imgname_end,
                            *endpos,
                            noteWidth * noteWidthX,
                            noteEndHeight,
                            noteRotate,
                            noteAlpha * missAlpha,
                            wait_execute = True
                        )
                        setOrder(None)
                        
                        if bodyLength > 0.0:
                            root.run_js_code(
                                f"ctx.drawAnchorESRotateImage(\
                                    {root.get_img_jsvarname(note.imgname_body)},\
                                    {bodypos[0]}, {bodypos[1]},\
                                    {noteWidth * noteWidthX},\
                                    {bodyLength},\
                                    {noteRotate},\
                                    {noteAlpha * missAlpha}\
                                );",
                                wait_execute = True,
                                order = note.draworder
                            )
                    
                    if debug:
                        drawDebugText(f"{line.index}+{note.masterIndex}", x, y, lineToNoteRotate, "rgba(0, 255, 255, 0.5)")
                        
                        root.run_js_code(
                            f"ctx.fillRectEx(\
                                {x - (w + h) / 250},\
                                {y - (w + h) / 250},\
                                {(w + h) / 250 * 2},\
                                {(w + h) / 250 * 2},\
                                'rgb(0, 255, 0)'\
                            );",
                            wait_execute = True,
                            order = const.CHART_RENDER_ORDERS.DEBUG
                        )
        
            if not notesChildren:
                line.renderNotes.remove(notesChildren)

    root.run_jscode_orders()
    
    effect_time = phira_respack.globalPack.effectDuration
    miss_effect_time = 0.2
    bad_effect_time = 0.5
    
    effect_time *= speed
    miss_effect_time *= speed
    bad_effect_time *= speed
    
    if noautoplay:
        def process_miss(note: phichart.Note):
            p = (now_t - note.time) / miss_effect_time
            linePos = chart_obj.options.posConverter(note.master.getPos(now_t))
            lineRotate = sum(note.master.getEventsValue(el.rotateEvents, now_t) for el in note.master.eventLayers)
            
            pos = utils.rotate_point(
                linePos[0] * w, linePos[1] * h,
                lineRotate,
                note.positionX * w
            )
            
            x, y = utils.rotate_point(
                *pos,
                (-90 if note.isAbove else 90) + lineRotate,
                (note.floorPosition - note.master.playingFloorPosition) * note.speed * h
            )
            
            note.nowpos = (x / w, y / h)
            noteImg = Resource["Notes"][note.img_keyname]
            noteWidth = globalNoteWidth * phira_respack.globalPack.dub_fixscale[note.type] * note.width
            noteHeight = noteWidth / noteImg.width * noteImg.height
            
            drawRotateImage(
                note.imgname,
                x, y,
                noteWidth, noteHeight,
                lineRotate,
                1 - p ** 0.5,
                wait_execute = True
            )
    
    if noautoplay:
        for pplmckfi in pplm.clickeffects.copy():
            perfect, eft, erbs, (position, rotate) = pplmckfi
            if eft <= now_t <= eft + effect_time:
                processClickEffect(*position(w, h), rotate, (now_t - eft) / effect_time, erbs, perfect)
            
            if eft + effect_time < now_t:
                pplm.clickeffects.remove(pplmckfi)
        
        for pplmbdfi in pplm.badeffects.copy():
            st, rotate, pos = pplmbdfi
            if st <= now_t <= st + bad_effect_time:
                processBadEffect(*pos, rotate, st, now_t, bad_effect_time)
            
            if st + bad_effect_time < now_t:
                pplm.badeffects.remove(pplmbdfi)
    
    for line in chart_obj.lines:
        for note, remove_this in line.effectNotes:
            if not noautoplay and not note.isontime:
                break
            
            if not noautoplay:
                for eft, erbs, (position, rotate) in note.effect_times:
                    if eft <= now_t <= eft + effect_time:
                        processClickEffect(*position(w, h), rotate, (now_t - eft) / effect_time, erbs, True)
            else:
                if note.state == const.NOTE_STATE.MISS:
                    if 0.0 <= now_t - note.time <= miss_effect_time and note.type != const.NOTE_TYPE.HOLD:
                        process_miss(note)
            
            if note.effect_times[-1][0] + max(
                effect_time,
                miss_effect_time,
                bad_effect_time
            ) + 0.2 < now_t:
                remove_this()
    
    if chart_obj.extra is not None:
        extra_values = chart_obj.extra.getShaderEffect(now_t, False)
        for name, values in extra_values:
            root.do_shader(name, values)
            
    if enableMirror:
        root.run_js_code("ctx.mirror();", wait_execute=True)
        
    combo = chart_obj.getCombo(now_t) if not noautoplay else pplm.ppps.getCombo()
    draw_ui(
        process = now_t / ((raw_audio_length + chart_obj.offset) * speed),
        score = stringifyScore((combo * (1000000 / chart_obj.note_num)) if chart_obj.note_num != 0 else 1000000) if not noautoplay else stringifyScore(pplm.ppps.getScore()),
        combo_state = combo >= 3,
        combo = combo,
        acc = "100.00%" if not noautoplay else f"{(pplm.ppps.getAcc() * 100):>05.2f}%",
        clear = False,
        background = False,
        **delDrawuiDefaultVals(attachUIData)
    )
    
    if need_deepbg:
        undoClipScreen()
    
    if chart_obj.extra is not None:
        extra_values = chart_obj.extra.getShaderEffect(now_t, True)
        for name, values in extra_values:
            root.do_shader(name, values)
    
    now_t /= speed
    now_t += chart_obj.offset
    
    rrmEnd()
    
    if now_t >= raw_audio_length:
        extasks.append(("break", ))
        
    if rjc:
        root.run_js_wait_code()
    
    return extasks

def getLevelNumber() -> str:
    lv = chart_information["Level"].lower()
    if "lv." in lv:
        return lv.split("lv.")[1]
    elif "lv" in lv:
        return lv.split("lv")[1]
    elif "level" in lv:
        return lv.split("level")[1]
    else:
        return "?"
    
def getLevelText() -> str:
    return chart_information["Level"].split(" ")[0]

def getFontSize(text: str, maxwidth: float, maxsize: float, font: str = "pgrFont"):
    w1px = root.run_js_code(f"ctx.font='50px {font}'; ctx.measureText({repr(text)}).width;") / 50
    if w1px == 0: w1px = 1.0
    return min(maxsize, maxwidth / w1px)

def drawTipAndLoading(
    p: float, sec: float,
    tip: str, tip_font_size: float
):
    tipalpha = utils.begin_animation_eases.tip_alpha_ease(p)
    drawText(
        w * 0.053125,
        h * (1004 / 1080),
        text = f"Tip: {tip}",
        font = f"{tip_font_size}px pgrFont",
        textAlign = "left",
        textBaseline = "middle",
        fillStyle = f"rgba(255, 255, 255, {tipalpha})",
        wait_execute = True
    )
    
    loadingBlockX = w * 0.84375
    loadingBlockY = h * (971 / 1080)
    loadingBlockWidth = w * 0.1046875
    loadingBlockHeight = h * (50 / 1080)
    loadingBlockTime = 0.65
    loadingBlockState: typing.Literal[0, 1] = int(sec / loadingBlockTime) % 2
    loadingBlockP = (sec % loadingBlockTime) / loadingBlockTime
    loadingBlockP = min(loadingBlockP / 0.95, 1.0)
    loadingBlockEasingType = 10
    loadingBlockEasing = (
        rpe_easing.ease_funcs[loadingBlockEasingType - 1](loadingBlockP)
        if loadingBlockState == 0 else
        (1.0 - rpe_easing.ease_funcs[loadingBlockEasingType - 1](1.0 - loadingBlockP))
    )
    
    loadingBlockLeft = loadingBlockX if loadingBlockState == 0 else (loadingBlockX + loadingBlockEasing * loadingBlockWidth)
    loadingBlockRight = (loadingBlockX + loadingBlockWidth) if loadingBlockState == 1 else (loadingBlockX + loadingBlockEasing * loadingBlockWidth)
    root.run_js_code(
        f"ctx.fillRectEx(\
            {loadingBlockLeft}, {loadingBlockY}, {loadingBlockRight - loadingBlockLeft}, {loadingBlockHeight},\
            'rgba(255, 255, 255, {tipalpha})'\
        );",
        wait_execute = True
    )
    
    def drawLoadingItem(x0: float, x1: float, color: str):
        root.run_js_code(
            f"ctx.drawClipXText(\
                'Loading...',\
                {loadingBlockX + loadingBlockWidth / 2},\
                {loadingBlockY + loadingBlockHeight / 2},\
                'center', 'middle', '{color}',\
                '{(w + h) / 100}px pgrFont',\
                {x0}, {x1}\
            );",
            wait_execute = True
        )
    
    drawLoadingItem(loadingBlockX, loadingBlockX + loadingBlockWidth, f"rgba(255, 255, 255, {tipalpha})")
    drawLoadingItem(loadingBlockLeft, loadingBlockRight, f"rgba(0, 0, 0, {tipalpha})")

def loadingAnimationFrame(p: float, sec: float, clear: bool = True, fcb: typing.Callable[[], typing.Any] = lambda: None):
    if clear: clearCanvas(wait_execute=True)
    all_ease_value = utils.begin_animation_eases.im_ease(p)
    background_ease_value = utils.begin_animation_eases.background_ease(p) * 1.25
    info_data_ease_value = utils.begin_animation_eases.info_data_ease((p - 0.2) * 3.25)
    info_data_ease_value_2 = utils.begin_animation_eases.info_data_ease((p - 0.275) * 3.25)
    
    drawBg()
    
    blackShadowRect = (
        0, 0,
        background_ease_value * w, h
    )
    blackShadowDPower = utils.getDPower(*utils.getSizeByRect(blackShadowRect), 75)
    blackShadowPolygon = (
        (0, 0),
        (background_ease_value * w, 0),
        (background_ease_value * w * (1 - blackShadowDPower), h),
        (0, h),
        (0, 0)
    )
    
    ctxSave(wait_execute=True)
    ctxBeginPath(wait_execute=True)
    ctxRect(0, 0, w, h, wait_execute=True)
    doPolygon(blackShadowPolygon, wait_execute = True)
    ctxClip("evenodd", wait_execute=True)
    fcb()
    ctxRestore(wait_execute=True)
    
    drawPolygon(
        blackShadowPolygon,
        fillStyle = f"rgba(0, 0, 0, {0.75 * (1 - p)})",
        wait_execute = True
    )
    
    root.run_js_code(
        f"ctx.translate({all_ease_value * w}, 0.0);",
        wait_execute = True
    )
    
    songShadowRect = (
        w * 0.0640625, h * (361 / 1080),
        w * 0.45, h * (505 / 1080)
    )
    root.run_js_code(
        f"ctx.drawDiagonalRectangle(\
            {",".join(map(str, songShadowRect))},\
            {utils.getDPower(*utils.getSizeByRect(songShadowRect), 75)},\
            'rgba(0, 0, 0, 0.6)'\
        );",
        wait_execute = True
    )
    
    difRect = (
        w * 0.340625, h * (355 / 1080),
        w * 0.440625, h * (513 / 1080)
    )
    root.run_js_code(
        f"ctx.drawDiagonalRectangle(\
            {",".join(map(str, difRect))},\
            {utils.getDPower(*utils.getSizeByRect(difRect), 75)},\
            'rgb(255, 255, 255)'\
        );",
        wait_execute = True
    )
    
    drawText(
        w * 0.1,
        h * (416 / 1080),
        text = chart_name_text,
        font = f"{(chart_name_font_text_size)}px pgrFont",
        textAlign = "left",
        textBaseline = "middle",
        fillStyle = "white",
        wait_execute = True
    )
    
    drawText(
        w * 0.0984375,
        h * (467 / 1080),
        text = chart_artist_text,
        font = f"{(chart_artist_text_font_size)}px pgrFont",
        textAlign = "left",
        textBaseline = "middle",
        fillStyle = "white",
        wait_execute = True
    )
    
    drawText(
        w * 0.390625,
        h * (424 / 1080),
        text = chart_level_number,
        font = f"{(chart_level_number_font_size)}px pgrFont",
        textAlign = "center",
        textBaseline = "middle",
        fillStyle = "#2F2F2F",
        wait_execute = True
    )
    
    drawText(
        w * 0.390625,
        h * (467 / 1080),
        text = chart_level_text,
        font = f"{(chart_level_text_font_size)}px pgrFont",
        textAlign = "center",
        textBaseline = "middle",
        fillStyle = "#2F2F2F",
        wait_execute = True
    )
    
    drawTipAndLoading(p, sec, tip, tip_font_size)
    
    info_charter_dx = (1 - info_data_ease_value) * -1 * w * 0.075
    info_ill_dx = (1 - info_data_ease_value_2) * -1 * w * 0.075
    
    drawText(
        w * 0.1265625 + info_charter_dx,
        h * (561 / 1080),
        text = "Chart",
        font = f"{w / 98}px pgrFont",
        textAlign = "left",
        textBaseline = "middle",
        fillStyle = f"rgba(255, 255, 255, {info_data_ease_value})",
        wait_execute = True
    )
    
    drawText(
        w * 0.1265625 + info_charter_dx,
        h * (590 / 1080),
        text = chart_charter_text,
        font = f"{chart_charter_text_font_size}px pgrFont",
        textAlign = "left",
        textBaseline = "middle",
        fillStyle = f"rgba(255, 255, 255, {info_data_ease_value})",
        wait_execute = True
    )
    
    drawText(
        w * 0.1125 + info_ill_dx,
        h * (645 / 1080),
        text = "Illustration",
        font = f"{w / 98}px pgrFont",
        textAlign = "left",
        textBaseline = "middle",
        fillStyle = f"rgba(255, 255, 255, {info_data_ease_value_2})",
        wait_execute = True
    )
    
    drawText(
        w * 0.1109375 + info_ill_dx,
        h * (677 / 1080),
        text = chart_illustrator_text,
        font = f"{chart_illustrator_text_font_size}px pgrFont",
        textAlign = "left",
        textBaseline = "middle",
        fillStyle = f"rgba(255, 255, 255, {info_data_ease_value_2})",
        wait_execute = True
    )
    
    baimg_x0 = w * 0.4375
    baimg_x1 = w * 0.9453125
    baimg_y1 = h * (733 / 1080)
    baimg_y0 = h * (219 / 1080)
    baimg_dpower = utils.getDPower(baimg_x1 - baimg_x0, baimg_y1 - baimg_y0, 75)
    root.run_js_code(
        f"ctx.drawDiagonalRectangleClipImageOnlyHeight(\
            {baimg_x0}, {baimg_y0},\
            {baimg_x1}, {baimg_y1},\
            {root.get_img_jsvarname("chart_image")},\
            {baimg_y1 - baimg_y0}, {baimg_dpower}, 1.0\
        );",
        wait_execute = True
    )
    
    if enableMirror:
        mirrorIconLeft = (
            baimg_x0 + (baimg_x1 - baimg_x0) * baimg_dpower
        ) - const.MIRROR_ICON_LEFT * MirrorIconWidth
        
        drawImage(
            "mirror",
            mirrorIconLeft, baimg_y0,
            MirrorIconWidth, MirrorIconHeight,
            wait_execute = True
        )
    
    root.run_js_code(
        f"ctx.translate(-{all_ease_value * w},0.0);",
        wait_execute = True
    )

def prepareLoadingAnimation(font_options: typing.Optional[dict] = None):
    global chart_name_text, chart_name_font_text_size
    global chart_artist_text, chart_artist_text_font_size
    global chart_level_number, chart_level_number_font_size
    global chart_level_text, chart_level_text_font_size
    global tip, tip_font_size
    global chart_charter_text
    global chart_illustrator_text
    global chart_charter_text_font_size
    global chart_illustrator_text_font_size
    
    if font_options is None:
        font_options = {}
    
    chart_name_text = chart_information["Name"]
    chart_level_number = getLevelNumber()
    chart_level_text = getLevelText()
    chart_artist_text = chart_information["Artist"]
    chart_charter_text = chart_information["Charter"]
    chart_illustrator_text = chart_information["Illustrator"]
    tip = phi_tips.get_tip()
    
    infoframe_width = w * 0.321875
    
    tip_font_size = getFontSize(tip, w * 0.84375 * 0.9, w * 0.020833 / 1.25)
    chart_name_font_text_size = getFontSize(chart_name_text, infoframe_width * 0.6, w * 0.025)
    chart_level_number_font_size = getFontSize(chart_level_number, infoframe_width * 0.125, h * (66 / 1080))
    chart_level_text_font_size = getFontSize(chart_level_text, infoframe_width * 0.075, h * (24 / 1080))
    chart_artist_text_font_size = getFontSize(chart_artist_text, infoframe_width * 0.65, w * 0.0161875)
    chart_charter_text_font_size = getFontSize(chart_charter_text, infoframe_width * 0.85, (w + h) * 0.011)
    chart_illustrator_text_font_size = getFontSize(chart_illustrator_text, infoframe_width * 0.85, (w + h) * 0.011)
    
    chart_name_font_text_size = font_options.get("songNameFontSize", chart_name_font_text_size)
    chart_artist_text_font_size = font_options.get("songComposerFontSize", chart_artist_text_font_size)
    chart_level_number_font_size = font_options.get("levelNumberFontSize", chart_level_number_font_size)
    chart_level_text_font_size = font_options.get("levelNameFontSize", chart_level_text_font_size)
    
    if len(chart_level_number) == 1:
        chart_level_text_font_size *= 1.35

def loadingAnimation(
    clear: bool = True,
    fcb: typing.Callable[[], typing.Any] = lambda: None,
    font_options: typing.Optional[dict] = None,
    start_p: float = 0.0,
    blackIn: bool = False
):
    if noanimation:
        return
    
    prepareLoadingAnimation(font_options)
    
    animation_time = 4.5
    animation_st = time.time() - start_p * animation_time
    while True:
        sec = time.time() - animation_st
        real_sec = sec - start_p * animation_time
        p = sec / animation_time
        
        if p > 1.0:
            break
        
        loadingAnimationFrame(p, sec, clear, fcb)
        
        if blackIn and real_sec <= 0.75:
            fillRectEx(
                0, 0, w, h, f"rgba(0, 0, 0, {1.0 - real_sec / 0.75})",
                wait_execute = True
            )
    
        root.run_js_wait_code()
        
def lineOpenAnimation(fcb: typing.Callable[[], typing.Any] = lambda: None):
    if noanimation:
        return
    
    csat = 1.25
    st = time.time()
        
    showLine = False
    
    lineHeight = w * chart_obj.options.lineHeightUnit[0] + h * chart_obj.options.lineHeightUnit[1]

    if not chart_obj.options.alwaysLineOpenAnimation:
        for line in chart_obj.lines:
            (
                linePos,
                lineAlpha,
                lineRotate
            ) = line.getState(0.0, (0, 0, 0))[:3]
            
            if (
                abs(linePos[1] - 0.5) <= 0.001 * h
                and abs(lineRotate) <= 0.001
                and abs(lineAlpha) >= 0.999
            ):
                showLine = True
                break
    else:
        showLine = True
    
    while True:
        p = (time.time() - st) / csat
        if p > 1.0:
            break
        
        fcb()
        val = rpe_easing.ease_funcs[12](p)
        
        clearCanvas(wait_execute=True)
        drawBg()
        if enableMirror:
            root.run_js_code("ctx.mirror();", wait_execute=True)
            
        draw_ui(
            clear = False,
            background = False,
            animationing = True,
            dy = h / 7 * val
        )
        
        if showLine:
            drawLine(
                w / 2 - (val * w / 2), h / 2,
                w / 2 + (val * w / 2), h / 2,
                strokeStyle = const.JUDGELINE_PERFECT_COLOR if FCAPIndicator else "rgb(255, 255, 255)",
                lineWidth = lineHeight / render_range_more_scale if render_range_more else lineHeight,
                wait_execute = True
            )
        
        root.run_js_wait_code()
    
    time.sleep(0.15)

def initSettlementAnimation(
    pplm: typing.Optional[utils.PhigrosPlayLogicManager] = None,
    avatar: str = "./resources/default_avatar.png"
):
    global im_size
    global ChartNameString, ChartNameStringFontSize
    global ChartLevelString, ChartLevelStringFontSize
    global ScoreString, LevelName, MaxCombo, AccString
    global PerfectCount, GoodCount, BadCount, MissCount
    global EarlyCount, LateCount
    global saUserData
    
    im_size = 0.475
    LevelName = "AP" if not noautoplay else pplm.ppps.getLevelString()
    EarlyCount = 0 if not noautoplay else pplm.ppps.getEarlyCount()
    LateCount = 0 if not noautoplay else pplm.ppps.getLateCount()
    PerfectCount = chart_obj.note_num if not noautoplay else pplm.ppps.getPerfectCount()
    GoodCount = 0 if not noautoplay else pplm.ppps.getGoodCount()
    BadCount = 0 if not noautoplay else pplm.ppps.getBadCount()
    MissCount = 0 if not noautoplay else pplm.ppps.getMissCount()
    Acc = 1.0 if not noautoplay else pplm.ppps.getAccOfAll()
    ScoreString = "1000000" if not noautoplay else stringifyScore(pplm.ppps.getScore())
    MaxCombo = chart_obj.note_num if not noautoplay else pplm.ppps.getMaxCombo()
    AccString = f"{(Acc * 100):.2f}%"
    ChartNameString = chart_information["Name"]
    ChartNameStringFontSize = w * im_size * 0.65 / (root.run_js_code(f"ctx.font='50px pgrFont'; ctx.measureText({repr(ChartNameString)}).width;") / 50)
    ChartLevelString = chart_information["Level"]
    ChartLevelStringFontSize = w * im_size * 0.275 / (root.run_js_code(f"ctx.font='50px pgrFont'; ctx.measureText({repr(ChartLevelString)}).width;") / 50)
    if ChartNameStringFontSize > w * 0.0275:
        ChartNameStringFontSize = w * 0.0275
    if ChartLevelStringFontSize > w * 0.0275 * 0.55:
        ChartLevelStringFontSize = w * 0.0275 * 0.55
    
    saUserData = settlementAnimationUserData()
    saUserData.avatar = Image.open(avatar)
    saUserData.init()

def settlementAnimationFrame(
    p: float, rjc: bool = True,
    ud_isPopup: bool = True,
    ud_popupP: float = 1.0
):
    clearCanvas(wait_execute = True)
    im_ease_value = utils.finish_animation_eases.all_ease(p)
    im_ease_pos = w * 1.25 * (1 - im_ease_value)
    data_block_1_ease_value = utils.finish_animation_eases.all_ease(p - 0.015)
    data_block_1_ease_pos = w * 1.25 * (1 - data_block_1_ease_value)
    data_block_2_ease_value = utils.finish_animation_eases.all_ease(p - 0.035)
    data_block_2_ease_pos = w * 1.25 * (1 - data_block_2_ease_value)
    data_block_3_ease_value = utils.finish_animation_eases.all_ease(p - 0.055)
    data_block_3_ease_pos = w * 1.25 * (1 - data_block_3_ease_value)
    button_ease_value = utils.finish_animation_eases.button_ease(p * 4.5 - 0.95)
    level_size = 0.1125
    level_size *= utils.finish_animation_eases.level_size_ease(p)
    button_ease_pos = - w * const.FINISH_UI_BUTTON_SIZE * (1 - button_ease_value)
    
    drawBg()
    
    baimg_w = w * 0.5203125
    baimg_h = h * (624 / 1080)
    dpower = utils.getDPower(baimg_w, baimg_h, 75)
    
    root.run_js_code(
        f"ctx.drawDiagonalRectangleCoverClipImage(\
            {w * 0.315625 - baimg_w / 2 + im_ease_pos}, {h * (539 / 1080) - baimg_h / 2},\
            {w * 0.315625 + baimg_w / 2 + im_ease_pos}, {h * (539 / 1080) + baimg_h / 2},\
            {root.get_img_jsvarname("chart_image")},\
            {dpower}, 1.0\
        );",
        wait_execute = True
    )
    
    root.run_js_code(
        f"ctx.drawDiagonalGrd(\
            {w * 0.315625 - baimg_w / 2 + im_ease_pos}, {h * (539 / 1080) - baimg_h / 2},\
            {w * 0.315625 + baimg_w / 2 + im_ease_pos}, {h * (539 / 1080) + baimg_h / 2},\
            {dpower}, {[
                [0.0, "rgba(0, 0, 0, 0.0)"],
                [0.25, "rgba(0, 0, 0, 0.0)"],
                [0.5, "rgba(0, 0, 0, 0.25)"],
                [0.75, "rgba(0, 0, 0, 0.5)"],
                [1.0, "rgba(0, 0, 0, 0.796875)"]
            ]},\
            {[
                0.0, h * (539 / 1080) - baimg_h / 2,
                0.0, h * (539 / 1080) + baimg_h / 2
            ]}\
        );",
        wait_execute = True
    )
    
    drawText(
        w * 0.0828125 + im_ease_pos,
        h * (815 / 1080),
        text = ChartNameString,
        font = f"{ChartNameStringFontSize}px pgrFont",
        textAlign = "left",
        textBaseline = "bottom",
        fillStyle = "#FFFFFF", 
        wait_execute = True
    )
    
    drawText(
        w * 0.48125 + im_ease_pos,
        h * (822 / 1080),
        text = ChartLevelString,
        font = f"{ChartLevelStringFontSize}px pgrFont",
        textAlign = "right",
        textBaseline = "bottom",
        fillStyle = "#FFFFFF", 
        wait_execute = True
    )
    
    def drawDiagonalDataBlock(sy: float, ey: float, ease_pos: float):
        sy *= h
        ey *= h
        db_x = w * 0.5046875
        db_y = h * (227 / 1080)
        db_width = w * 0.4484375
        db_height = h * (624 / 1080)
        db_dpower = utils.getDPower(db_width, db_height, 75)
        db_dw = db_dpower * db_width
        sy += db_y
        ey += db_y
        
        db_itemrect = (
            db_x + db_dw * (1.0 - (ey - db_y) / db_height) + ease_pos, sy,
            db_x + db_width - db_dw * ((sy - db_y) / db_height) + ease_pos, ey
        )
        
        drawPolygon(
            utils.rect2drect(db_itemrect, 75),
            fillStyle = "rgba(0, 0, 0, 0.5)",
            wait_execute = True
        )
    
    drawDiagonalDataBlock(0.0, 312 / 1080, data_block_1_ease_pos)
    drawDiagonalDataBlock(357 / 1080, 467 / 1080, data_block_2_ease_pos)
    drawDiagonalDataBlock(512 / 1080, 622 / 1080, data_block_3_ease_pos)
    
    drawText(
        w * 0.584375 + data_block_1_ease_pos,
        h * (467 / 1080),
        text = ScoreString,
        font = f"{(w + h) / 38}px pgrFont",
        textAlign = "left",
        textBaseline = "bottom",
        fillStyle = f"rgba(255, 255, 255, {utils.finish_animation_eases.score_alpha_ease(p)})",
        wait_execute = True
    )
    
    root.run_js_code(
        f"ctx.drawAlphaCenterImage(\
            {root.get_img_jsvarname(f"Level_{LevelName}")},\
            {w * 0.8578125 + data_block_1_ease_pos}, {h * (380 / 1080)},\
            {w * level_size}, {w * level_size},\
            {utils.finish_animation_eases.level_alpha_ease(p)}\
        );",
        wait_execute = True
    )
    
    root.run_js_code(
        f"ctx.save(); ctx.globalAlpha = {utils.finish_animation_eases.playdata_alpha_ease(p - 0.02)}",
        wait_execute = True
    )
    
    drawText( # Max Combo
        w * 0.55625 + data_block_2_ease_pos,
        h * (650 / 1080),
        text = f"{MaxCombo}",
        textAlign = "left",
        textBaseline = "bottom",
        fillStyle = "#FFFFFF",
        font = f"{(w + h) / 65}px pgrFont",
        wait_execute = True
    )
    
    drawText(
        w * 0.55625 + data_block_2_ease_pos,
        h * (674 / 1080),
        text = "Max Combo",
        textAlign = "left",
        textBaseline = "bottom",
        fillStyle = "#FFFFFF",
        font = f"{(w + h) / 125}px pgrFont",
        wait_execute = True
    )
    
    drawText( # Accuracy
        w * 0.878125 + data_block_2_ease_pos,
        h * (650 / 1080),
        text = AccString,
        textAlign = "right",
        textBaseline = "bottom",
        fillStyle = "#FFFFFF",
        font = f"{(w + h) / 65}px pgrFont",
        wait_execute = True
    )
    
    drawText(
        w * 0.878125 + data_block_2_ease_pos,
        h * (674 / 1080),
        text = "Accuracy",
        textAlign = "right",
        textBaseline = "bottom",
        fillStyle = "#FFFFFF",
        font = f"{(w + h) / 125}px pgrFont",
        wait_execute = True
    )
    
    root.run_js_code(
        f"ctx.globalAlpha = {utils.finish_animation_eases.playdata_alpha_ease(p - 0.04)}",
        wait_execute = True
    )
    
    def drawDataCount(x: float, text: str, count: int):
        drawText( # Perfect Count
            x + data_block_3_ease_pos,
            h * (826 / 1080),
            text = text,
            textAlign = "center",
            textBaseline = "bottom",
            fillStyle = "white",
            font = f"{(w + h) / 185}px pgrFont",
            wait_execute = True
        )
        
        drawText(
            x + data_block_3_ease_pos,
            h * (806 / 1080),
            text = f"{count}",
            textAlign = "center",
            textBaseline = "bottom",
            fillStyle = "white",
            font = f"{(w + h) / 75}px pgrFont",
            wait_execute = True
        )
    
    def drawELCount(y: float, text: float, count: int):
        drawText(
            w * 0.7764375 + data_block_3_ease_pos,
            y,
            text = text,
            textAlign = "left",
            textBaseline = "bottom",
            fillStyle = "white",
            font = f"{(w + h) / 146}px pgrFont",
            wait_execute = True
        )
        
        drawText(
            w * 0.8548125 + data_block_3_ease_pos,
            y,
            text = f"{count}",
            textAlign = "right",
            textBaseline = "bottom",
            fillStyle = "white",
            font = f"{(w + h) / 146}px pgrFont",
            wait_execute = True
        )
        
    drawDataCount(w * 0.5515625, "Perfect", PerfectCount)
    drawDataCount(w * 0.6234375, "Good", GoodCount)
    drawDataCount(w * 0.6765625, "Bad", BadCount)
    drawDataCount(w * 0.7296875, "Miss", MissCount)
    drawELCount(h * (794 / 1080), "Early", EarlyCount)
    drawELCount(h * (823 / 1080), "Late", LateCount)
    
    root.run_js_code("ctx.restore();", wait_execute = True)
    
    Retry_Button_Width = w * const.FINISH_UI_BUTTON_SIZE
    Retry_Button_Height = w * const.FINISH_UI_BUTTON_SIZE / 190 * 145
    Retry_imsize = Retry_Button_Height * 0.3
    
    Continue_Button_Width, Continue_Button_Height = Retry_Button_Width, Retry_Button_Height
    Continue_imsize = Retry_imsize
    
    drawImage( # Retry Button
        "ButtonLeftBlack",
        button_ease_pos, 0,
        width = Retry_Button_Width,
        height = Retry_Button_Height,
        wait_execute = True
    )
    
    drawImage(
        "Retry",
        button_ease_pos + w * const.FINISH_UI_BUTTON_SIZE * 0.3 - Retry_imsize / 2,
        Retry_Button_Height / 2 - (Retry_Button_Height * (8 / 145)) - Retry_imsize / 2,
        width = Retry_imsize,
        height = Retry_imsize,
        wait_execute = True
    )
    
    drawImage( # Continue Button
        "ButtonRightBlack",
        w - button_ease_pos - Continue_Button_Width, h - Continue_Button_Height,
        width = Continue_Button_Width,
        height = Continue_Button_Height,
        wait_execute = True
    )
    
    drawImage(
        "Arrow_Right",
        w - (button_ease_pos + w * const.FINISH_UI_BUTTON_SIZE * 0.35 + Continue_imsize / 2),
        h - (Continue_Button_Height / 2 - (Continue_Button_Height * (8 / 145)) * 1.15 + Continue_imsize / 2),
        width = Continue_imsize,
        height = Continue_imsize,
        wait_execute = True
    )
    
    root.run_js_code(
        f"ctx.save(); ctx.globalAlpha = {utils.finish_animation_eases.userinfo_alpha_ease(p - 0.03)}",
        wait_execute = True
    )
    
    avatar_rect = drawUserData(
        root, ud_popupP,
        w, h,
        Resource,
        
        saUserData.avatar,
        saUserData.userNameWidth,
        saUserData.userNamePadding,
        ud_isPopup,
        
        saUserData.userName,
        saUserData.rankingScore,
        saUserData.hasChallengeMode,
        saUserData.challengeModeRank
    )
    
    root.run_js_code("ctx.restore();", wait_execute = True)
    if rjc: root.run_js_wait_code()
    
    return avatar_rect

def lineCloseAimationFrame(p: float, a1_combo: typing.Optional[int], rjc: bool = True):
    v = p ** 2
    if not noautoplay:
        draw_ui(
            process = 1.0,
            score = ScoreString,
            combo_state = chart_obj.note_num >= 3,
            combo = chart_obj.note_num,
            acc = AccString,
            animationing = True,
            dy = h / 7 * (1 - v)
        )
    else:
        draw_ui(
            process = 1.0,
            score = ScoreString,
            combo_state = a1_combo >= 3,
            combo = a1_combo,
            acc = AccString,
            animationing = True,
            dy = h / 7 * (1 - v)
        )
        
    if rjc: root.run_js_wait_code()

def drawUserData(
    root: webcv.WebCanvas,
    p: float,
    w: int, h: int,
    Resource: dict,
    
    avatar_img: Image.Image,
    userNameWidth: float,
    userNamePadding: float,
    userDataIsPopup: bool,
    
    userName: str = "GUEST",
    rankingScore: float = 0,
    hasChallengeMode: bool = False,
    challengeModeRank: int = 000,
    
    alpha: float = 1.0
):
    utils.shadowDrawer.root = root
    
    ctxSave(wait_execute=True)
    ctxMutGlobalAlpha(alpha, wait_execute=True)
    
    userDataRect = (
        w * 0.83025, h * (28 / 1080),
        w * 2.0, h * (135 / 1080)
    )
    userDataRectSize = utils.getSizeByRect(userDataRect)
    userDataDPower = utils.getDPower(*userDataRectSize, 75)
    
    root.run_js_code(
        f"ctx.drawDiagonalRectangle(\
            {",".join(map(str, userDataRect))},\
            {userDataDPower},\
            'rgb(0, 0, 0)'\
        );",
        wait_execute = True
    )
    
    avatar_rect = (
        w * 0.840625, h * (21 / 1080),
        w * 0.95, h * (142 / 1080)
    )
    avatar_rectsize = utils.getSizeByRect(avatar_rect)
    avatar_w, avatar_h = utils.getCoverSize(*avatar_img.size, *avatar_rectsize)
    avatar_x, avatar_y = utils.getPosFromCoverSize(avatar_w, avatar_h, *avatar_rectsize)
    avatar_dpower = utils.getDPower(*avatar_rectsize, 75)
    rks_y = h * (126 / 1080)
    rks_x = (
        avatar_rect[2]
        - avatar_rectsize[0] * avatar_dpower * (
            (rks_y - avatar_rect[1]) / avatar_rectsize[1]
        )
    )
    rks_rect = (
        rks_x, h * (93 / 1080),
        w * 0.997125, rks_y
    )
    root.run_js_code(
        f"ctx.drawDiagonalRectangle(\
            {",".join(map(str, rks_rect))},\
            {utils.getDPower(*utils.getSizeByRect(rks_rect), 75)},\
            'rgb(255, 255, 255)'\
        );",
        wait_execute = True
    )
    
    rks_rect_center = utils.getCenterPointByRect(rks_rect)
    drawText(
        rks_rect_center[0], rks_rect_center[1] - h * (2 / 1080),
        f"{rankingScore:.2f}",
        font = f"{(w + h) / 100}px pgrFont",
        textAlign = "center",
        textBaseline = "middle",
        fillStyle = "black",
        wait_execute = True
    )
    
    popupUserDataLeftX = (userDataRect[0] - userNameWidth * p) if userDataIsPopup else (userDataRect[0] - userNameWidth * (1.0 - p))
    popupUserDataRect = (
        popupUserDataLeftX, userDataRect[1],
        max(userDataRect[0] + userDataRectSize[0] * userDataDPower, popupUserDataLeftX) + 1, userDataRect[3]
    )
    popupUserDataRectSize = utils.getSizeByRect(popupUserDataRect)
    popupUserDataDPower = utils.getDPower(*popupUserDataRectSize, 75)
    root.run_js_code(
        f"ctx.drawDiagonalRectangle(\
            {",".join(map(str, popupUserDataRect))},\
            {popupUserDataDPower},\
            'rgb(0, 0, 0)'\
        );",
        wait_execute = True
    )
    
    root.run_js_code(
        f"ctx.drawDiagonalRectangleClipImage(\
            {",".join(map(str, avatar_rect))},\
            {root.get_img_jsvarname("user_avatar")},\
            {avatar_x}, {avatar_y},\
            {avatar_w}, {avatar_h},\
            {avatar_dpower}, 1.0\
        );",
        wait_execute = True
    )
    
    ctxSave(wait_execute=True)
    ctxBeginPath(wait_execute=True)
    ctxRect(*utils.xxyy_rect2_xywh(popupUserDataRect), wait_execute=True)
    ctxClip(wait_execute=True)
    drawText(
        popupUserDataRect[0] + popupUserDataRectSize[0] * popupUserDataDPower + userNamePadding,
        utils.getCenterPointByRect(popupUserDataRect)[1],
        userName,
        font = f"{(w + h) / const.USERNAME_CONST_FONT}px pgrFont",
        textAlign = "left",
        textBaseline = "middle",
        fillStyle = "white",
        wait_execute = True
    )
    ctxRestore(wait_execute=True)
    
    if hasChallengeMode:
        cmLevel = min(challengeModeRank // 100, len(Resource["challenge_mode_levels"]) - 1)
        cmImage = Resource["challenge_mode_levels"][cmLevel]
        cmCenter = (w * 0.969875, h * (67 / 1080))
        cmImageWidth = w * 0.043
        cmImageHeight = cmImageWidth * cmImage.height / cmImage.width
        drawImage(
            f"cmlevel_{cmLevel}",
            cmCenter[0] - cmImageWidth / 2,
            cmCenter[1] - cmImageHeight / 2,
            cmImageWidth,
            cmImageHeight,
            wait_execute = True
        )
        
        with utils.shadowDrawer("rgba(255, 255, 255, 0.5)", (w + h) / 125):
            drawText(
                cmCenter[0],
                cmCenter[1] - h * (10 / 1080),
                f"{challengeModeRank % 100}",
                font = f"{(w + h) / 85}px pgrFont",
                textAlign = "center",
                textBaseline = "middle",
                fillStyle = "rgba(255, 255, 255, 0.8)",
                wait_execute = True
            )
    
    ctxRestore(wait_execute=True)
    
    return avatar_rect
