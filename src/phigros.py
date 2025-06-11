import err_processer as _
import init_logging as _
import load_extended as _
import fix_workpath as _
import import_argvs as _
import check_edgechromium as _
import check_bin as _

import webbrowser
import typing
import random
import json
import sys
import time
import math
import logging
import platform
import ctypes
import functools
from io import BytesIO
from threading import Thread, Event as ThreadEvent
from os import system
from os.path import exists

from PIL import Image, ImageFilter

import webcv
import const
import utils
import phigame_obj
import rpe_easing
import phicore
import dxsound
import phira_respack
import tempdir
import socket_webviewbridge
import phi_tips
import phichart
from dxsmixer import mixer
from exitfunc import exitfunc
from graplib_webview import *

if not exists("./phigros_assets") or not all([
    exists(utils.gtpresp(i)) for i in [
        "config.json",
        "chapters.json"
    ]
]):
    logging.error("phigros_assets not found or corrupted, you can create it by tool-make-pgrassets-byunpack")
    system("pause")
    raise SystemExit

tempdir.clearTempDir()
temp_dir = tempdir.createTempDir()

assetConfig = json.loads(open(utils.gtpresp("config.json"), "r", encoding="utf-8").read())
userData_default = {
    "userdata-userName": "GUEST",
    "userdata-userAvatar": assetConfig["default-avatar"],
    "userdata-userBackground": assetConfig["default-background"],
    "userdata-rankingScore": 0.0,
    "userdata-selfIntroduction": "There is a self-introduction, write something just like:\nTwitter: @Phigros_PGS\nYouTube: Pigeon Games\n\nHope you have fun in Phigros.\nBest regards,\nPigeon Games",
    "setting-chartOffset": 0,
    "setting-noteScale": 1.0,
    "setting-backgroundDim": 0.4,
    "setting-enableClickSound": True,
    "setting-musicVolume": 1.0,
    "setting-uiVolume": 1.0,
    "setting-clickSoundVolume": 1.0,
    "setting-enableMorebetsAuxiliary": True,
    "setting-enableFCAPIndicator": True,
    "setting-enableLowQuality": False,
    "setting-enableSceneTransitionAnimation": True,
    "setting-enableTrigrid": True,
    "internal-lowQualityScale": 1.0,
    "internal-dspBufferExponential": 8,
    "internal-lowQualityScale-JSLayer": 2.5,
    "internal-lastDiffIndex": 0
}

playData_default = {
    "datas": [],
    "hasChallengeMode": False,
    "challengeModeRank": 100,
    "isFirstStart": True
}

def saveUserData(data: dict):
    try:
        with open("./phigros_userdata.json", "w", encoding="utf-8") as f:
            f.write(json.dumps(data, indent=4, ensure_ascii=False))
    except Exception as e:
        logging.error(f"phigros_userdata.json save failed: {e}")

def loadUserData():
    global userData
    userData = userData_default.copy()
    try:
        userData.update(json.loads(open("./phigros_userdata.json", "r", encoding="utf-8").read()))
    except Exception as e:
        logging.error(f"phigros_userdata.json load failed, using default data, {e}")

def getUserData(key: str):
    return userData.get(key, userData_default[key])

def setUserData(key: str, value: typing.Any):
    userData[key] = value

def savePlayData(data: dict):
    try:
        with open("./phigros_playdata.json", "w", encoding="utf-8") as f:
            f.write(json.dumps(data, indent=4, ensure_ascii=False))
    except Exception as e:
        logging.error(f"phigros_playdata.json save failed: {e}")

def loadPlayData():
    global playData
    playData = playData_default.copy()
    try:
        playData.update(json.loads(open("./phigros_playdata.json", "r", encoding="utf-8").read()))
    except Exception as e:
        logging.error(f"phigros_playdata.json load failed, using default data, {e}")

def findPlayData(finder: typing.Callable[[dict], bool]):
    for i in playData["datas"]:
        if finder(i):
            return i
    return None

findPlayDataBySid = lambda sid: findPlayData(lambda x: x["sid"] == sid)

def initPlayDataItem(sid: str):
    if findPlayDataBySid(sid) is None:
        playData["datas"].append({
            "sid": sid,
            "score": 0.0,
            "acc": 0.0,
            "level": "never_play"
        })

def setPlayData(sid: str, score: float, acc: float, level: typing.Literal["AP", "FC", "V", "S", "A", "B", "C", "F"], save: bool = True):
    initPlayDataItem(sid)
    old_data = findPlayData(lambda x: x["sid"] == sid)
    old_data["score"] = max(score, old_data["score"])
    old_data["acc"] = max(acc, old_data["acc"])
    old_data["level"] = max((old_data["level"], level), key=lambda x: const.PGR_LEVEL_INTMAP[x])
    if save: savePlayData(playData)

def getPlayDataItem(key: str):
    return playData.get(key, playData_default[key])

def setPlayDataItem(key: str, value: typing.Any):
    playData[key] = value

@functools.cache
def countPlayData(chapter: phigame_obj.Chapter, key: str):
    diffindex = getUserData("internal-lastDiffIndex")
    count = 0
    for song in chapter.songs:
        diff = song.difficulty[min(diffindex, len(song.difficulty) - 1)]
        if const.PGR_LEVEL_INTMAP[findPlayDataBySid(diff.unqique_id())["level"]] >= const.PGR_LEVEL_INTMAP[key]:
            count += 1
    return count

class UserDataPopuper:
    def __init__(self):
        self.isPopup = True
        self.animatTime = 0.4
        self.animatEase = rpe_easing.ease_funcs[13]
        self.lastClickTime = time.time() - self.animatTime
    
    def change(self):
        self.isPopup = not self.isPopup
        self.lastClickTime = time.time()
    
    @property
    def p(self):
        p = (time.time() - self.lastClickTime) / self.animatTime
        return self.animatEase(utils.fixorp(p))

if not exists("./phigros_userdata.json"):
    saveUserData(userData_default)
    loadUserData()

loadUserData()
saveUserData(userData)
loadPlayData()
savePlayData(playData)

mixer.init(buffer = 2 ** getUserData("internal-dspBufferExponential"))
chaptersDx = 0.0
inMainUI = False
inSettingUI = False
settingState = None
lastMainUI_ChaptersClickX = 0.0
lastLastMainUI_ChaptersClickX = 0.0
settingPlayWidgetsDy = 0.0
mainUI_ChaptersMouseDown = False
changeChapterMouseDownX = float("nan")
lastChangeChapterTime = float("-inf")
setting = phigame_obj.Setting()
PlaySettingWidgets: dict[str, phigame_obj.PhiBaseWidget] = {}
dspSettingWidgets: dict[str, phigame_obj.PhiBaseWidget] = {}

def loadChapters():
    global Chapters, ChaptersMaxDx
    
    jsonData: dict = json.loads(open(utils.gtpresp("chapters.json"), "r", encoding="utf-8").read())
    jsonData["chapters"].insert(0, {
        "name": "Phigros",
        "cn-name": "",
        "o-name": "",
        "image": "/../resources/AllSong.png",
        "songs": [
            j
            for i in jsonData["chapters"]
            for j in i["songs"]
        ]
    })
    
    Chapters = phigame_obj.Chapters(
        [
            phigame_obj.Chapter(
                name = chapter["name"],
                cn_name = chapter["cn-name"],
                o_name = chapter["o-name"],
                image = chapter["image"],
                songs = [
                    phigame_obj.Song(
                        name = song["name"],
                        composer = song["composer"],
                        iller = song["iller"],
                        image = song["image"],
                        image_lowres = song["image_lowres"],
                        preview = song["preview"],
                        preview_start = song["preview_start"],
                        preview_end = song["preview_end"],
                        import_archive_alias = song.get("import_archive_alias", None),
                        difficulty = [
                            phigame_obj.SongDifficulty(
                                name = diff["name"],
                                level = diff["level"],
                                chart_audio = diff["chart_audio"],
                                chart_image = diff["chart_image"],
                                chart_file = diff["chart_file"],
                                charter = diff["charter"]
                            )
                            for diff in song["difficlty"]
                        ]
                    )
                    for song in chapter["songs"]
                ],
                all_songs_flag = chapter is jsonData["chapters"][0]
            )
            for chapter in jsonData["chapters"]
        ]
    )
    
    for chapter in Chapters.items:
        for song in chapter.songs:
            for diff in song.difficulty:
                initPlayDataItem(diff.unqique_id())
    
    savePlayData(playData)
    
    ChaptersMaxDx = w * (len(Chapters.items) - 1) * (295 / 1920) + w * 0.5 - w * 0.875

def putColor(color: tuple|str, im: Image.Image):
    return Image.merge("RGBA", (
        *Image.new("RGB", im.size, color).split(),
        im.split()[-1]
    ))

def updateUserAvatar():
    udAvatar = getUserData("userdata-userAvatar")
    if udAvatar not in assetConfig["avatars"]:
        setUserData("userdata-userAvatar", userData_default["userdata-userAvatar"])
        if udAvatar not in assetConfig["avatars"]:
            udAvatar = assetConfig["avatars"][0]
        saveUserData(userData)
        logging.warning("User avatar not found, reset to default")
    root.run_js_code(f"{root.get_img_jsvarname("userAvatar")} = {root.get_img_jsvarname(f"avatar_{assetConfig["avatars"].index(getUserData("userdata-userAvatar"))}")};")

def loadResource():
    global note_max_width, note_max_height
    global note_max_size_half
    global ButtonWidth, ButtonHeight
    global MainUIIconWidth, MainUIIconHeight
    global SettingUIOtherIconWidth, SettingUIOtherIconHeight
    global MessageButtonSize
    global JoinQQGuildBannerWidth, JoinQQGuildBannerHeight
    global JoinQQGuildPromoWidth, JoinQQGuildPromoHeight
    global SettingUIOtherDownIconWidth
    global SettingUIOtherDownIconHeight_Twitter, SettingUIOtherDownIconHeight_QQ
    global SettingUIOtherDownIconHeight_Bilibili, SettingUIOtherDownIconHeight_Github
    global TapTapIconWidth, TapTapIconHeight
    global CheckedIconWidth, CheckedIconHeight
    global SortIconWidth, SortIconHeight
    global RandomIconWidth, RandomIconHeight
    global ChartChooseSettingIconWidth, ChartChooseSettingIconHeight
    global MirrorIconWidth, MirrorIconHeight
    global challengeModeCheckedWidth, challengeModeCheckedHeight
    global UndoIconWidth, UndoIconHeight
    global ComboboxArrowWidth, ComboboxArrowHeight
    global LoadSuccess
    
    logging.info("Loading Resource...")
    LoadSuccess = mixer.Sound(("./resources/LoadSuccess.wav"))
    
    phi_rpack = phira_respack.PhiraResourcePack("./resources/resource_packs/default")
    phi_rpack.setToGlobal()
    
    Resource = {
        "levels": {
            "AP": Image.open("./resources/levels/AP.png"),
            "FC": Image.open("./resources/levels/FC.png"),
            "V": Image.open("./resources/levels/V.png"),
            "S": Image.open("./resources/levels/S.png"),
            "A": Image.open("./resources/levels/A.png"),
            "B": Image.open("./resources/levels/B.png"),
            "C": Image.open("./resources/levels/C.png"),
            "F": Image.open("./resources/levels/F.png"),
            "NEW": Image.open("./resources/levels/NEW.png")
        },
        "challenge_mode_levels": [
            Image.open(f"./resources/challenge_mode_levels/{i}.png")
            for i in range(6)
        ],
        "logoipt": Image.open("./resources/logoipt.png"),
        "warning": Image.open("./resources/le_warn.png"),
        "phigros": Image.open("./resources/phigros.png"),
        "AllSongBlur": Image.open("./resources/AllSongBlur.png"),
        "facula": Image.open("./resources/facula.png"),
        "collectibles": Image.open("./resources/collectibles.png"),
        "setting": Image.open("./resources/setting.png"),
        "ButtonLeftBlack": Image.open("./resources/Button_Left_Black.png"),
        "ButtonRightBlack": None,
        "message": Image.open("./resources/message.png"),
        "JoinQQGuildBanner": Image.open("./resources/JoinQQGuildBanner.png"),
        "UISound_1": mixer.Sound("./resources/UISound_1.wav"),
        "UISound_2": mixer.Sound("./resources/UISound_2.wav"),
        "UISound_3": mixer.Sound("./resources/UISound_3.wav"),
        "UISound_4": mixer.Sound("./resources/UISound_4.wav"),
        "UISound_5": mixer.Sound("./resources/UISound_5.wav"),
        "JoinQQGuildPromo": Image.open("./resources/JoinQQGuildPromo.png"),
        "Arrow_Left": Image.open("./resources/Arrow_Left.png"),
        "Arrow_Right": Image.open("./resources/Arrow_Right.png"),
        "Arrow_Right_Black": Image.open("./resources/Arrow_Right_Black.png"),
        "twitter": Image.open("./resources/twitter.png"),
        "qq": Image.open("./resources/qq.png"),
        "bilibili": Image.open("./resources/bilibili.png"),
        "taptap": Image.open("./resources/taptap.png"),
        "checked": Image.open("./resources/checked.png"),
        "CalibrationHit": dxsound.directSound("./resources/CalibrationHit.wav"),
        "Retry": Image.open("./resources/Retry.png"),
        "Pause": mixer.Sound("./resources/Pause.wav"),
        "PauseImg": Image.open("./resources/Pause.png"),
        "PUIBack": Image.open("./resources/PUIBack.png"),
        "PUIRetry": Image.open("./resources/PUIRetry.png"),
        "PUIResume": Image.open("./resources/PUIResume.png"),
        "edit": Image.open("./resources/edit.png"),
        "close": Image.open("./resources/close.png"),
        "sort": Image.open("./resources/sort.png"),
        "Random": Image.open("./resources/Random.png"),
        "mirror": Image.open("./resources/mirror.png"),
        "blackPixel": Image.new("RGBA", (1, 1), (0, 0, 0, 255)),
        "challengeModeChecked": Image.open("./resources/challengeModeChecked.png"),
        "Undo": Image.open("./resources/Undo.png"),
        "cross": Image.open("./resources/cross.png"),
        "github": Image.open("./resources/github.png"),
        "trigridBase": Image.open("./resources/TriGridBase.png"),
        "combobox_arrow": Image.open("./resources/bytedance_icons/combobox_arrow.png"),
    }
    
    Resource.update(phi_rpack.createResourceDict())
    
    Resource["ButtonRightBlack"] = Resource["ButtonLeftBlack"].transpose(Image.FLIP_LEFT_RIGHT).transpose(Image.FLIP_TOP_BOTTOM)
    Resource["Notes"]["Bad"] = putColor((90, 60, 70), Resource["Notes"]["Tap"])
    
    imageBlackMaskHeight = 12
    imageBlackMask = Image.new("RGBA", (1, imageBlackMaskHeight), (0, 0, 0, 0))
    imageBlackMask.putpixel((0, 0), (0, 0, 0, 64))
    imageBlackMask.putpixel((0, 1), (0, 0, 0, 32))
    imageBlackMask.putpixel((0, 2), (0, 0, 0, 16))
    imageBlackMask.putpixel((0, imageBlackMaskHeight - 3), (0, 0, 0, 16))
    imageBlackMask.putpixel((0, imageBlackMaskHeight - 2), (0, 0, 0, 32))
    imageBlackMask.putpixel((0, imageBlackMaskHeight - 1), (0, 0, 0, 64))
    
    respacker = webcv.PILResPacker(root)
    respacker.reg_img(imageBlackMask.resize((1, 500)), "imageBlackMask")
    respacker.reg_img(Resource["Retry"], "Retry")
    respacker.reg_img(Resource["PauseImg"], "PauseImg")
    respacker.reg_img(Resource["logoipt"], "logoipt")
    respacker.reg_img(Resource["warning"], "warning")
    respacker.reg_img(Resource["phigros"], "phigros")
    respacker.reg_img(Resource["AllSongBlur"], "AllSongBlur")
    respacker.reg_img(Resource["facula"], "facula")
    respacker.reg_img(Resource["collectibles"], "collectibles")
    respacker.reg_img(Resource["setting"], "setting")
    respacker.reg_img(Resource["ButtonLeftBlack"], "ButtonLeftBlack")
    respacker.reg_img(Resource["ButtonRightBlack"], "ButtonRightBlack")
    respacker.reg_img(Resource["message"], "message")
    respacker.reg_img(Resource["JoinQQGuildBanner"], "JoinQQGuildBanner")
    respacker.reg_img(Resource["JoinQQGuildPromo"], "JoinQQGuildPromo")
    respacker.reg_img(Resource["Arrow_Left"], "Arrow_Left")
    respacker.reg_img(Resource["Arrow_Right"], "Arrow_Right")
    respacker.reg_img(Resource["Arrow_Right_Black"], "Arrow_Right_Black")
    respacker.reg_img(Resource["twitter"], "twitter")
    respacker.reg_img(Resource["qq"], "qq")
    respacker.reg_img(Resource["bilibili"], "bilibili")
    respacker.reg_img(Resource["taptap"], "taptap")
    respacker.reg_img(Resource["checked"], "checked")
    respacker.reg_img(Resource["PUIBack"], "PUIBack")
    respacker.reg_img(Resource["PUIRetry"], "PUIRetry")
    respacker.reg_img(Resource["PUIResume"], "PUIResume")
    respacker.reg_img(Resource["edit"], "edit")
    respacker.reg_img(Resource["close"], "close")
    respacker.reg_img(Resource["sort"], "sort")
    respacker.reg_img(Resource["Random"], "Random")
    respacker.reg_img(Resource["mirror"], "mirror")
    respacker.reg_img(Resource["blackPixel"], "blackPixel")
    respacker.reg_img(Resource["challengeModeChecked"], "challengeModeChecked")
    respacker.reg_img(Resource["Undo"], "Undo")
    respacker.reg_img(Resource["cross"], "cross")
    respacker.reg_img(Resource["github"], "github")
    respacker.reg_img(Resource["trigridBase"], "trigridBase")
    respacker.reg_img(Resource["combobox_arrow"], "combobox_arrow")

    ButtonWidth = w * 0.10875
    ButtonHeight = ButtonWidth / Resource["ButtonLeftBlack"].width * Resource["ButtonLeftBlack"].height # bleft and bright size is the same.
    MainUIIconWidth = w * 0.0265
    MainUIIconHeight = MainUIIconWidth / Resource["collectibles"].width * Resource["collectibles"].height # or arr or oth w/h same ratio
    SettingUIOtherIconWidth = w * 0.01325
    SettingUIOtherIconHeight = SettingUIOtherIconWidth / Resource["Arrow_Right_Black"].width * Resource["Arrow_Right_Black"].height
    MessageButtonSize = w * 0.025
    JoinQQGuildBannerWidth = w * 0.2
    JoinQQGuildBannerHeight = JoinQQGuildBannerWidth / Resource["JoinQQGuildBanner"].width * Resource["JoinQQGuildBanner"].height
    JoinQQGuildPromoWidth = w * 0.721875
    JoinQQGuildPromoHeight = JoinQQGuildPromoWidth / Resource["JoinQQGuildPromo"].width * Resource["JoinQQGuildPromo"].height
    SettingUIOtherDownIconWidth = w * 0.01725
    SettingUIOtherDownIconHeight_Twitter = SettingUIOtherDownIconWidth / Resource["twitter"].width * Resource["twitter"].height
    SettingUIOtherDownIconHeight_QQ = SettingUIOtherDownIconWidth / Resource["qq"].width * Resource["qq"].height
    SettingUIOtherDownIconHeight_Bilibili = SettingUIOtherDownIconWidth / Resource["bilibili"].width * Resource["bilibili"].height
    SettingUIOtherDownIconHeight_Github = SettingUIOtherDownIconWidth / Resource["github"].width * Resource["github"].height
    TapTapIconWidth = w * 0.05
    TapTapIconHeight = TapTapIconWidth / Resource["taptap"].width * Resource["taptap"].height
    CheckedIconWidth = w * 0.0140625
    CheckedIconHeight = CheckedIconWidth / Resource["checked"].width * Resource["checked"].height
    SortIconWidth = w * 0.0171875
    SortIconHeight = SortIconWidth / Resource["sort"].width * Resource["sort"].height
    RandomIconWidth = w * 0.0244375
    RandomIconHeight = RandomIconWidth / Resource["Random"].width * Resource["Random"].height
    ChartChooseSettingIconWidth = w * 0.018
    ChartChooseSettingIconHeight = ChartChooseSettingIconWidth / Resource["setting"].width * Resource["setting"].height
    MirrorIconWidth = w * 0.108925
    MirrorIconHeight = MirrorIconWidth / Resource["mirror"].width * Resource["mirror"].height
    challengeModeCheckedWidth = w * 0.026
    challengeModeCheckedHeight = challengeModeCheckedWidth / Resource["challengeModeChecked"].width * Resource["challengeModeChecked"].height
    UndoIconWidth = w * 0.02
    UndoIconHeight = UndoIconWidth / Resource["Undo"].width * Resource["Undo"].height
    ComboboxArrowWidth = w * 0.03
    ComboboxArrowHeight = ComboboxArrowWidth / Resource["combobox_arrow"].width * Resource["combobox_arrow"].height
    
    phicore.MirrorIconWidth = MirrorIconWidth
    phicore.MirrorIconHeight = MirrorIconHeight
    
    for k, v in Resource["levels"].items():
        respacker.reg_img(v, f"Level_{k}")
    
    for i, v in enumerate(Resource["challenge_mode_levels"]):
        respacker.reg_img(v, f"cmlevel_{i}")
        
    for k, v in Resource["Notes"].items():
        respacker.reg_img(Resource["Notes"][k], f"Note_{k}")
    
    for i in range(phira_respack.globalPack.effectFrameCount):
        respacker.reg_img(Resource["Note_Click_Effect"]["Perfect"][i], f"Note_Click_Effect_Perfect_{i + 1}")
        respacker.reg_img(Resource["Note_Click_Effect"]["Good"][i], f"Note_Click_Effect_Good_{i + 1}")

    for chapter in Chapters.items:
        chapterimbytes = open(utils.gtpresp(chapter.image), "rb").read()
        im = Image.open(BytesIO(chapterimbytes))
        chapter.im = im
        respacker.reg_img(chapterimbytes, f"chapter_{chapter.chapterId}_raw")
        respacker.reg_img(im.filter(ImageFilter.GaussianBlur(radius = (im.width + im.height) / 45)), f"chapter_{chapter.chapterId}_blur")
    
    for index, avatar in enumerate(assetConfig["avatars"]):
        respacker.reg_img(open(utils.gtpresp(avatar), "rb").read(), f"avatar_{index}")
    
    root.reg_res(open("./resources/font.ttf", "rb").read(), "pgrFont.ttf")
    root.reg_res(open("./resources/font-thin.ttf", "rb").read(), "pgrFontThin.ttf")
    respacker.load(*respacker.pack())
    
    root.wait_jspromise(f"loadFont('pgrFont', \"{root.get_resource_path("pgrFont.ttf")}\");")
    root.wait_jspromise(f"loadFont('pgrFontThin', \"{root.get_resource_path("pgrFontThin.ttf")}\");")
    root.unreg_res("pgrFont.ttf")
    root.unreg_res("pgrFontThin.ttf")
    
    updateUserAvatar()
    root._regims.clear()
    
    shaders = {
        "trigrid": open("./shaders/trigrid.glsl", "r", encoding="utf-8").read(),
    }
    
    for name, glsl in shaders.items():
        root.load_glsl(name, glsl)
    
    logging.info("Load Resource Successfully")
    return Resource

def bindEvents():
    global mainUISlideControler, settingUIPlaySlideControler
    global settingUIOpenSourceLicenseSlideControler
    global SettingPlayWidgetEventManager, dspSettingWidgetEventManager
    global settingUIChooseAvatarAndBackgroundSlideControler
    
    root.jsapi.set_attr("click", eventManager.click)
    root.run_js_code("_click = (e) => pywebview.api.call_attr('click', e.x, e.y);")
    root.run_js_code("window.addEventListener('mousedown-np', _click);")
    
    root.jsapi.set_attr("mousemove", eventManager.move)
    root.run_js_code("_mousemove = (e) => pywebview.api.call_attr('mousemove', e.x, e.y);")
    root.run_js_code("window.addEventListener('mousemove-np', _mousemove);")
    
    root.jsapi.set_attr("mouseup", eventManager.release)
    root.run_js_code("_mouseup = (e) => pywebview.api.call_attr('mouseup', e.x, e.y);")
    root.run_js_code("window.addEventListener('mouseup-np', _mouseup);")
    
    mainUISlideControler = phigame_obj.SlideControler(
        mainUI_slideControlerMouseDown_valid,
        mainUI_slideControler_setValue,
        0.0, ChaptersMaxDx,
        0.0, 0.0, w, h
    )
    eventManager.regClickEventFs(mainUISlideControler.mouseDown, False)
    eventManager.regReleaseEvent(phigame_obj.ReleaseEvent(mainUISlideControler.mouseUp))
    eventManager.regMoveEvent(phigame_obj.MoveEvent(mainUISlideControler.mouseMove))
    
    settingUIPlaySlideControler = phigame_obj.SlideControler(
        settingUI_slideControlerMouseDown_valid,
        settingUI_slideControler_setValue,
        0.0, 0.0,
        0.0, 0.0, w, h
    )
    eventManager.regClickEventFs(settingUIPlaySlideControler.mouseDown, False)
    eventManager.regReleaseEvent(phigame_obj.ReleaseEvent(settingUIPlaySlideControler.mouseUp))
    eventManager.regMoveEvent(phigame_obj.MoveEvent(settingUIPlaySlideControler.mouseMove))
    
    settingUIOpenSourceLicenseSlideControler = phigame_obj.SlideControler(
        lambda x, y: w * 0.2 <= x <= w * 0.8,
        lambda x, y: None,
        0.0, 0.0,
        0.0, 0.0, w, h
    )
    eventManager.regClickEventFs(settingUIOpenSourceLicenseSlideControler.mouseDown, False)
    eventManager.regReleaseEvent(phigame_obj.ReleaseEvent(settingUIOpenSourceLicenseSlideControler.mouseUp))
    eventManager.regMoveEvent(phigame_obj.MoveEvent(settingUIOpenSourceLicenseSlideControler.mouseMove))
    
    settingUIChooseAvatarAndBackgroundSlideControler = phigame_obj.SlideControler(
        lambda x, y: True,
        lambda x, y: None,
        0.0, 0.0,
        0.0, 0.0, w, h
    )
    eventManager.regClickEventFs(settingUIChooseAvatarAndBackgroundSlideControler.mouseDown, False)
    eventManager.regReleaseEvent(phigame_obj.ReleaseEvent(settingUIChooseAvatarAndBackgroundSlideControler.mouseUp))
    eventManager.regMoveEvent(phigame_obj.MoveEvent(settingUIChooseAvatarAndBackgroundSlideControler.mouseMove))
    
    SettingPlayWidgetEventManager = phigame_obj.WidgetEventManager([], settingPlayWidgetEvent_valid)
    eventManager.regClickEventFs(SettingPlayWidgetEventManager.mouseDown, False)
    eventManager.regReleaseEvent(phigame_obj.ReleaseEvent(SettingPlayWidgetEventManager.mouseUp))
    eventManager.regMoveEvent(phigame_obj.MoveEvent(SettingPlayWidgetEventManager.mouseMove))
    
    dspSettingWidgetEventManager = phigame_obj.WidgetEventManager([], lambda x, y: True)
    eventManager.regClickEventFs(dspSettingWidgetEventManager.mouseDown, False)
    eventManager.regReleaseEvent(phigame_obj.ReleaseEvent(dspSettingWidgetEventManager.mouseUp))
    eventManager.regMoveEvent(phigame_obj.MoveEvent(dspSettingWidgetEventManager.mouseMove))

    eventManager.regClickEventFs(changeChapterMouseDown, False)
    eventManager.regReleaseEvent(phigame_obj.ReleaseEvent(changeChapterMouseUp))

def drawBackground():
    f, t = Chapters.aFrom, Chapters.aTo
    if f == -1: f = t # 最开始的, 没有之前的选择
    imfc, imtc = Chapters.items[f], Chapters.items[t]
    p = getChapterP(imtc)
    
    drawAlphaImage(f"chapter_{imfc.chapterId}_blur", 0, 0, w, h, 1.0 - p, wait_execute=True)
    drawAlphaImage(f"chapter_{imtc.chapterId}_blur", 0, 0, w, h, p, wait_execute=True)

def drawFsBgdeCoration(trigrid_cfg: typing.Optional[dict] = None):
    if not getUserData("setting-enableTrigrid"):
        for facula in faManager.faculas:
            if facula["startTime"] <= time.time() <= facula["endTime"]:
                state = faManager.getFaculaState(facula)
                sizePx = facula["size"] * (w + h) / 40
                drawAlphaImage(
                    "facula",
                    facula["x"] * w - sizePx / 2, state["y"] * h - sizePx / 2,
                    sizePx, sizePx,
                    state["alpha"] * 0.4,
                    wait_execute = True
                )
                
    else:
        setCtx("trigrid_ctx")
        drawImage("trigridBase", 0, 0, w, h, wait_execute=True)
        setCtx("ctx")
        
        trigrid_shader_datas = {
            "tex_size": [0.2, 0.25],
            "base_color": [0.057, 0.057, 0.057, 0.4],
            
            "face_color": [0.702, 0.9449554, 1, 1],
            "face_brightness": 0.1,
            
            "grid_color": [1, 1, 1, 1],
            "grid_brightness": 0.35,
            
            "glow_color": [0.383, 0.8843222, 1, 1],
            "glow_brightness": 1.3,
            
            "t": time.perf_counter()
        }
        
        if trigrid_cfg is not None:
            trigrid_shader_datas.update(trigrid_cfg)
            
        root.do_shader("trigrid", trigrid_shader_datas, "trigrid_ctx")
        root.run_js_code(f"ctx.drawImage(trigrid_cv, 0, 0, {w}, {h});", wait_execute=True)

def getChapterP(chapter: phigame_obj.Chapter):
    chapterIndex = Chapters.items.index(chapter)
    ef = rpe_easing.ease_funcs[0]
    atime = 1.0
    
    if chapterIndex == Chapters.aFrom:
        p = 1.0 - (time.time() - Chapters.aSTime) / atime
        ef = rpe_easing.ease_funcs[16]
    elif chapterIndex == Chapters.aTo:
        p = (time.time() - Chapters.aSTime) / atime
        ef = rpe_easing.ease_funcs[15]
    else:
        p = 0.0
    
    return ef(utils.fixorp(p))

def getChapterWidth(p: float):
    return w * (0.221875 + (0.5640625 - 0.221875) * p)

def getChapterToNextWidth(p: float):
    return w * (295 / 1920) + (w * 0.5 - w * (295 / 1920)) * p

def getChapterRect(dx: float, chapterWidth: float):
    pady = 140 / 1920 * w
    return (
        dx, pady,
        dx + chapterWidth, h - pady
    )

intoChallengeModeButtonRect = const.EMPTY_RECT
def drawChapterItem(item: phigame_obj.Chapter, dx: float, rectmap: dict):
    global intoChallengeModeButtonRect
    
    p = getChapterP(item)
    if dx > w: return getChapterToNextWidth(p)
    chapterWidth = getChapterWidth(p)
    if dx + chapterWidth < 0: return getChapterToNextWidth(p)
    chapterImWidth = h * (1.0 - 140 / 1080 * 2) / item.im.height * item.im.width
    chapterDPower = utils.getDPower(chapterWidth, h * (1.0 - 140 / 1080 * 2), 75)
    
    chapterRect = getChapterRect(dx, chapterWidth)
    
    root.run_js_code(
        f"ctx.drawDiagonalRectangleShadow(\
            {",".join(map(str, chapterRect))},\
            {chapterDPower}, 'rgb(16, 16, 16)', 'rgba(16, 16, 16, 0.7)', {(w + h) / 125}\
        );",
        wait_execute = True
    )
    
    if p != 1.0:
        root.run_js_code(
            f"ctx.drawDiagonalRectangleClipImage(\
                {",".join(map(str, chapterRect))},\
                {root.get_img_jsvarname(f"chapter_{item.chapterId}_blur")},\
                {- (chapterImWidth - chapterWidth) / 2}, 0, {chapterImWidth}, {h * (1.0 - 140 / 1080 * 2)},\
                {chapterDPower}, 1.0\
            );",
            wait_execute = True
        )
        
        root.run_js_code(
            f"ctx.drawDiagonalRectangle(\
                {",".join(map(str, chapterRect))},\
                {chapterDPower}, 'rgba(0, 0, 0, 0.5)'\
            );",
            wait_execute = True
        )
    
    root.run_js_code(
        f"ctx.drawDiagonalRectangleClipImage(\
            {",".join(map(str, chapterRect))},\
            {root.get_img_jsvarname(f"chapter_{item.chapterId}_raw")},\
            {- (chapterImWidth - chapterWidth) / 2}, 0, {chapterImWidth}, {h * (1.0 - 140 / 1080 * 2)},\
            {chapterDPower}, {p}\
        );",
        wait_execute = True
    )
    
    root.run_js_code(
        f"ctx.drawDiagonalRectangleClipImage(\
            {",".join(map(str, chapterRect))},\
            {root.get_img_jsvarname("imageBlackMask")},\
            {- (chapterImWidth - chapterWidth) / 2}, 0, {chapterImWidth}, {h * (1.0 - 140 / 1080 * 2)},\
            {chapterDPower}, 1.0\
        );",
        wait_execute = True
    )
    
    root.run_js_code(
        f"ctx.drawRotateText2(\
            '{processStringToLiteral(item.name)}',\
            {chapterRect[2] - chapterDPower * chapterWidth - (w + h) / 150}, {chapterRect[3] - (w + h) / 150},\
            -75, 'rgba(255, 255, 255, {0.82 * (1.0 - (1.0 if p >= 0.4 else p / 0.4))})', '{(w + h) / 50}px pgrFont',\
            'left', 'bottom'\
        );",
        wait_execute = True
    )
    
    if p != 0.0:
        drawText(
            chapterRect[2] - (w + h) / 50,
            chapterRect[1] + (w + h) / 90,
            item.cn_name,
            font = f"{(w + h) / 75}px pgrFont",
            textAlign = "right",
            textBaseline = "top",
            fillStyle = f"rgba(255, 255, 255, {p ** 2})", # ease again
            wait_execute = True
        )
        
        drawText(
            chapterRect[0] + chapterDPower * chapterWidth + (w + h) / 125,
            chapterRect[1] + (w + h) / 90,
            item.o_name,
            font = f"{(w + h) / 115}px pgrFont",
            textAlign = "left",
            textBaseline = "top",
            fillStyle = f"rgba(255, 255, 255, {p ** 2})", # ease again
            wait_execute = True
        )
    
    PlayButtonWidth = w * 0.1453125
    PlayButtonHeight = h * (5 / 54)
    PlayButtonDPower = utils.getDPower(PlayButtonWidth, PlayButtonHeight, 75)

    playButtonRect = (
        chapterRect[2] - chapterDPower * chapterWidth + PlayButtonDPower * PlayButtonWidth - PlayButtonWidth, chapterRect[3] - PlayButtonHeight,
        chapterRect[2] - chapterDPower * chapterWidth + PlayButtonDPower * PlayButtonWidth, chapterRect[3]
    )
    
    playButtonTriangle = (
        playButtonRect[0] + (playButtonRect[2] - playButtonRect[0]) * 0.17, playButtonRect[1] + (playButtonRect[3] - playButtonRect[1]) * (4 / 11),
        playButtonRect[0] + (playButtonRect[2] - playButtonRect[0]) * 0.17, playButtonRect[3] - (playButtonRect[3] - playButtonRect[1]) * (4 / 11),
        playButtonRect[0] + (playButtonRect[2] - playButtonRect[0]) * 0.25, playButtonRect[1] + (playButtonRect[3] - playButtonRect[1]) * 0.5
    )
    
    playButtonAlpha = 0.0 if p <= 0.6 else (p - 0.6) / 0.4
    
    if not item.all_songs_flag:
        rectmap[item.chapterId] = playButtonRect
    
    if playButtonAlpha != 0.0 and not item.all_songs_flag:
        root.run_js_code(
            f"ctx.drawDiagonalRectangle(\
                {",".join(map(str, playButtonRect))},\
                {PlayButtonDPower}, 'rgba(255, 255, 255, {playButtonAlpha})'\
            );",
            wait_execute = True
        )
        
        root.run_js_code(
            f"ctx.drawTriangleFrame(\
                {",".join(map(str, playButtonTriangle))},\
                'rgba(0, 0, 0, {playButtonAlpha})',\
                {(w + h) / 800}\
            );",
            wait_execute = True
        )
        
        drawText(
            playButtonRect[0] + (playButtonRect[2] - playButtonRect[0]) * 0.35,
            playButtonRect[1] + (playButtonRect[3] - playButtonRect[1]) * 0.5,
            "P L A Y",
            font = f"{(w + h) / 65}px pgrFont",
            textAlign = "left",
            textBaseline = "middle",
            fillStyle = f"rgba(49, 49, 49, {playButtonAlpha})",
            wait_execute = True
        )
    
    if item.all_songs_flag:
        allsongs_bar_y0 = chapterRect[1] + (chapterRect[3] - chapterRect[1]) * 0.73625
        allsongs_bar_height = h * (179 / 1080)
        allsongs_bar_y1 = allsongs_bar_y0 + allsongs_bar_height
        
        getx_fromy = lambda y: chapterRect[0] + (1.0 - (y - chapterRect[1]) / (chapterRect[3] - chapterRect[1])) * chapterWidth * chapterDPower
        
        allsongs_bar_x0 = getx_fromy(allsongs_bar_y1)
        allsongs_bar_x1 = getx_fromy(allsongs_bar_y0) + chapterWidth * (1.0 - chapterDPower)
        allsongs_bar_rect = (
            allsongs_bar_x0, allsongs_bar_y0,
            allsongs_bar_x1, allsongs_bar_y1
        )
        
        allsongs_bar_alpha = 0.0 if p <= 0.6 else (p - 0.6) / 0.4
        
        allsongs_show_level_dpower = utils.getDPower(*allsongs_show_level_size, 75)
        root.run_js_code(
            f"ctx.drawLeftBottomSkewText(\
                {repr(allsongs_show_level)},\
                {chapterRect[0] + w * 0.03125}, {chapterRect[1] + h * (745 / 1080)},\
                '{allsongs_show_level_font}px pgrFont', 'rgba{(255, 255, 255, allsongs_bar_alpha * 0.5)}', {allsongs_show_level_dpower}\
            );",
            wait_execute = True
        )
        
        with utils.shadowDrawer("rgba(0, 0, 0, 0.8)", (w + h) / 85):
            root.run_js_code(
                f"ctx.drawDiagonalRectangle(\
                    {",".join(map(str, allsongs_bar_rect))},\
                    {utils.getDPower(*utils.getSizeByRect(allsongs_bar_rect), 75)}, 'rgba(0, 0, 0, {allsongs_bar_alpha * 0.45})'\
                );",
                wait_execute = True
            )
        
        def _drawButton(bottom_y: float, text: str):
            dx = chapterWidth * (493 / 1083) - chapterWidth / 3 * (1.0 - p)
            x0 = getx_fromy(bottom_y) + dx
            top_y = bottom_y - h * (99 / 1080)
            x1 = getx_fromy(top_y) + w * 0.18125 + dx
            
            button_rect = (
                x0, top_y,
                x1, bottom_y
            )
            
            root.run_js_code(
                f"ctx.drawDiagonalRectangle(\
                    {",".join(map(str, button_rect))},\
                    {utils.getDPower(*utils.getSizeByRect(button_rect), 75)}, 'rgba(255, 255, 255, {allsongs_bar_alpha * 0.9})'\
                );",
                wait_execute = True
            )
            
            drawText(
                *utils.getCenterPointByRect(button_rect),
                text,
                font = f"{(w + h) / 85}px pgrFont",
                textAlign = "center",
                textBaseline = "middle",
                fillStyle = f"rgba(0, 0, 0, {allsongs_bar_alpha * 0.8})",
                wait_execute = True
            )
            
            return button_rect
        
        rectmap[item.chapterId] = _drawButton(chapterRect[3] - h * (24 / 1080), "全部歌曲")
        intoChallengeModeButtonRect = _drawButton(chapterRect[3] - h * (126 / 1080), "课题模式")
    
    dataAlpha = 0.0 if p <= 0.6 else (p - 0.6) / 0.4
    
    if dataAlpha != 0.0:
        def _drawScoreTexts(name: str, num: int, i: int):
            dx = 0.095 * (i - 1)
            dy = 0.0 if not item.all_songs_flag else -h * (15 / 1080)
            x = chapterRect[0] + chapterWidth * (0.075 + dx)
            
            if item.all_songs_flag:
                x += w * 0.0109375
            
            drawText(
                x,
                chapterRect[3] - h * (1.0 - 140 / 1080 * 2) * 0.04375 + dy,
                name,
                font = f"{(w + h) / 175 * 0.9}px pgrFont",
                textAlign = "center",
                textBaseline = "bottom",
                fillStyle = f"rgba(255, 255, 255, {0.95 * dataAlpha})",
                wait_execute = True
            )
            
            drawText(
                x,
                chapterRect[3] - h * (1.0 - 140 / 1080 * 2) * (0.04375 + 0.0275) + dy,
                f"{num}",
                font = f"{(w + h) / 95 * 0.9}px pgrFont",
                textAlign = "center",
                textBaseline = "bottom",
                fillStyle = f"rgba(255, 255, 255, {0.95 * dataAlpha})",
                wait_execute = True
            )
        
        _drawScoreTexts("All", len(item.songs), 1)
        _drawScoreTexts("Clear", countPlayData(item, "C"), 2)
        _drawScoreTexts("Full Combo", countPlayData(item, "FC"), 3)
        _drawScoreTexts("Phi", countPlayData(item, "AP"), 4)
    
    return getChapterToNextWidth(p)

def drawChapters(rectmap: dict):
    chapterX = w * 0.034375 + chaptersDx
    for chapter in Chapters.items:
        chapterX += drawChapterItem(chapter, chapterX, rectmap)

def drawButton(
    buttonName: str,
    iconName: str,
    buttonPos: tuple[float, float],
    iconSize: typing.Optional[tuple[float, float]] = None
):
    if iconSize is None:
        iconSize = (MainUIIconWidth, MainUIIconHeight)
        
    drawImage(buttonName, *buttonPos, ButtonWidth, ButtonHeight, wait_execute=True)
    
    centerPoint = (0.35, 0.395) if buttonName == "ButtonLeftBlack" else (0.65, 0.605)
    
    drawImage(
        iconName,
        buttonPos[0] + ButtonWidth * centerPoint[0] - iconSize[0] / 2,
        buttonPos[1] + ButtonHeight * centerPoint[1] - iconSize[1] / 2,
        *iconSize,
        wait_execute = True
    )

def drawDialog(
    p: float,
    dialogImageName: str, diagonalPower: float,
    dialogImageSize: tuple[float, float],
    noText: str, yesText: str
):
    setCtx("dialog_canvas_ctx")
    clearCanvas(wait_execute=True)
    setCtx("ctx")
            
    p = 1.0 - (1.0 - p) ** 3
    tempWidth = dialogImageSize[0] * (0.65 + p * 0.35)
    tempHeight = dialogImageSize[1] * (0.65 + p * 0.35)
    diagonalRectanglePowerPx = diagonalPower * tempWidth
    dialogCenterY = h * 0.5 - tempHeight * 0.2 / 2
    
    dialogRect = (
        w / 2 - tempWidth / 2,
        dialogCenterY - tempHeight / 2,
        w / 2 + tempWidth / 2,
        dialogCenterY + tempHeight / 2 + tempHeight * 0.2
    )
    dialogDPower = utils.getDPower(*utils.getSizeByRect(dialogRect), 75)
    
    root.run_js_code(
        f"dialog_canvas_ctx.save();\
        dialog_canvas_ctx.clipDiagonalRectangle(\
            {",".join(map(str, dialogRect))},\
            {utils.getDPower(*utils.getSizeByRect(dialogRect), 75)}\
        );",
        wait_execute = True
    )
    
    
    setCtx("dialog_canvas_ctx")
    drawAlphaImage(
        dialogImageName,
        w / 2 - tempWidth / 2 + tempWidth * dialogDPower * (0.2 / 1.2),
        dialogCenterY - tempHeight / 2,
        tempWidth, tempHeight,
        p,
        wait_execute = True
    )
    setCtx("ctx")
    
    diagonalRectangle = (
        w / 2 - tempWidth / 2 - diagonalRectanglePowerPx * 0.2,
        dialogCenterY + tempHeight / 2,
        w / 2 + tempWidth / 2 - diagonalRectanglePowerPx,
        dialogCenterY + tempHeight / 2 + tempHeight * 0.2
    )
    
    root.run_js_code(
        f"dialog_canvas_ctx.fillRectExByRect(\
            {",".join(map(str, diagonalRectangle))},\
            'rgba(0, 0, 0, {0.85 * p})'\
        );",
        wait_execute = True
    )
    
    root.run_js_code(
        f"dialog_canvas_ctx.drawDiagonalDialogRectangleText(\
            {",".join(map(str, diagonalRectangle))},\
            {diagonalPower * 0.2},\
            '{processStringToLiteral(noText)}',\
            '{processStringToLiteral(yesText)}',\
            'rgba(255, 255, 255, {p})',\
            '{(w + h) / 95 * (0.65 + p * 0.35)}px pgrFont'\
        );",
        wait_execute = True
    )
    
    root.run_js_code(f"dialog_canvas_ctx.restore();", wait_execute=True)
    
    return (
        diagonalRectangle[0] + diagonalRectanglePowerPx * 0.2, diagonalRectangle[1],
        diagonalRectangle[0] + (diagonalRectangle[2] - diagonalRectangle[0]) / 2, diagonalRectangle[3]
    ), (
        diagonalRectangle[0] + (diagonalRectangle[2] - diagonalRectangle[0]) / 2, diagonalRectangle[1],
        diagonalRectangle[2] - diagonalRectanglePowerPx * 0.2, diagonalRectangle[3]
    )

def showStartAnimation():
    global faManager
    
    start_animation_clicked = False
    def start_animation_click_cb(*args): nonlocal start_animation_clicked; start_animation_clicked = True
    
    a1_t = 5.0
    a1_st = time.time()
    mixer.music.load("./resources/NewSplashSceneBGM.mp3")
    played_NewSplashSceneBGM = False
    while True:
        p = (time.time() - a1_st) / a1_t
        if p > 1.0: break
                
        if p > 0.4 and not played_NewSplashSceneBGM:
            played_NewSplashSceneBGM = True
            mixer.music.play(-1)
            Thread(target=soundEffect_From0To1, daemon=True).start()
        
        if p > 0.4:
            eventManager.regClickEventFs(start_animation_click_cb, True)
            if start_animation_clicked:
                break
            
        clearCanvas(wait_execute = True)
        
        alpha = utils.easeAlpha(p)
        drawAlphaImage(
            "logoipt",
            0, 0, w, h,
            alpha,
            wait_execute = True
        )
        
        ep = 1.0 - (1.0 - utils.fixorp(p * 4)) ** 4
        
        drawText(
            w * 0.5,
            h * 1.2 - h * 0.55 * ep,
            "声明",
            f"{(w + h) / 85}px pgrFont",
            textAlign = "center",
            textBaseline = "top",
            fillStyle = f"rgba(255, 255, 255, {alpha})",
            wait_execute = True
        )
        
        drawText(
            w * 0.5,
            h * 1.2 - h * 0.5 * ep,
            "(1) 本项目是一款仿制作品，原作为Pigeon Games 鸽游创作的《Phigros》。",
            f"{(w + h) / 100}px pgrFont",
            textAlign = "center",
            textBaseline = "top",
            fillStyle = f"rgba(255, 255, 255, {alpha})",
            wait_execute = True
        )
        
        drawText(
            w * 0.5,
            h * 1.2 - h * 0.45 * ep,
            "(2) 本项目仅为研究学习目的，不可商业使用、违法使用。",
            f"{(w + h) / 100}px pgrFont",
            textAlign = "center",
            textBaseline = "top",
            fillStyle = f"rgba(255, 255, 255, {alpha})",
            wait_execute = True
        )
        
        root.run_js_wait_code()
    
    a2_t = 5.0
    a2_st = time.time()
    while True:
        p = (time.time() - a2_st) / a2_t
        if p > 1.0: break
        if start_animation_clicked: break
        
        clearCanvas(wait_execute = True)
        
        drawAlphaImage(
            "warning",
            0, 0, w, h,
            utils.easeAlpha(p),
            wait_execute = True
        )
        
        root.run_js_wait_code()
    
    for e in eventManager.clickEvents:
        if e.callback is start_animation_click_cb:
            eventManager.clickEvents.remove(e)
            break
    
    faManager = phigame_obj.FaculaAnimationManager()
    Thread(target=faManager.main, daemon=True).start()
    a3_st = time.time()
    a3_clicked = False
    a3_clicked_time = float("nan")
    a3_sound_fadeout = False
    def a3_click_cb(*args):
        nonlocal a3_clicked_time, a3_clicked
        a3_clicked_time = time.time()
        a3_clicked = True
    eventManager.regClickEventFs(a3_click_cb, True)
    phigros_logo_width = 0.25
    phigros_logo_rect = (
        w / 2 - w * phigros_logo_width / 2,
        h * (100 / 230) - h * phigros_logo_width / Resource["phigros"].width * Resource["phigros"].height / 2,
        w * phigros_logo_width, w * phigros_logo_width / Resource["phigros"].width * Resource["phigros"].height
    )
    
    if not abs(mixer.music.get_pos() - 8.0) <= 0.05:
        mixer.music.set_pos(8.0)
        
    while True:
        atime = time.time() - a3_st
        
        if a3_clicked and time.time() - a3_clicked_time > 1.0:
            clearCanvas() # no wait
            break
        
        clearCanvas(wait_execute = True)
        
        drawBackground()
        
        root.run_js_code(
            f"ctx.fillRectEx(\
                0, 0, {w}, {h},\
                'rgba(0, 0, 0, {(math.sin(atime / 1.5) + 1.0) / 5 + 0.15})'\
            );",
            wait_execute = True
        )
        
        lines_n = 0
        for i in range(lines_n):
            drawLine(
                0, h * (i / lines_n), w, h * (i / lines_n),
                strokeStyle = "rgba(162, 206, 223, 0.3)",
                lineWidth = 0.25, wait_execute = True
            )
    
        drawFsBgdeCoration({
            "base_color": [0.018, 0.018, 0.018, 0.0901],
            "grid_brightness": 0.4,
            "glow_brightness": 0.71
        })
        
        drawImage("phigros", *phigros_logo_rect, wait_execute = True)
        
        textBlurTime = atime % 5.5
        if textBlurTime > 3.0:
            textBlur = math.sin(math.pi * (textBlurTime - 3.0) / 2.5) * 10
        else:
            textBlur = 0.0
        
        root.run_js_code(
            f"ctx.shadowColor = '#FFFFFF'; ctx.shadowBlur = {textBlur};",
            wait_execute = True
        )
        
        drawText(
            w / 2,
            h * (155 / 230),
            text = "点  击  屏  幕  开  始",
            font = f"{(w + h) / 125}px pgrFont",
            textAlign = "center",
            textBaseline = "middle",
            fillStyle = "#FFFFFF",
            wait_execute = True
        )
        
        root.run_js_code(
            "ctx.shaderColor = 'rgba(0, 0, 0, 0)'; ctx.shadowBlur = 0;",
            wait_execute = True
        )
        
        drawText(
            w / 2,
            h * 0.98,
            text = f"Version: {const.PHIGROS_VERSION}",
            font = f"{(w + h) / 250}px pgrFont",
            textAlign = "center",
            textBaseline = "bottom",
            fillStyle = "#888888",
            wait_execute = True
        )
        
        if atime <= 2.0:
            blurP = 1.0 - (1.0 - atime / 2.0) ** 3
            root.run_js_code(f"mask.style.backdropFilter = 'blur({(w + h) / 60 * (1 - blurP)}px)';", wait_execute = True)
        else:
            root.run_js_code(f"mask.style.backdropFilter = '';", wait_execute = True)
        
        if a3_clicked and time.time() - a3_clicked_time <= 1.0:
            if not a3_sound_fadeout:
                a3_sound_fadeout = True
                mixer.music.fadeout(500)
            
            root.run_js_code(
                f"ctx.fillRectEx(\
                    0, 0, {w}, {h},\
                    'rgba(0, 0, 0, {1.0 - (1.0 - (time.time() - a3_clicked_time)) ** 2})'\
                );",
                wait_execute = True
            )
        
        root.run_js_wait_code()
    
    root.run_js_code(f"mask.style.backdropFilter = '';", wait_execute = True)
    
    if getPlayDataItem("isFirstStart"):
        setPlayDataItem("isFirstStart", False)
        savePlayData(playData)
        settingRender()
    else:
        mainRender()

def soundEffect_From0To1():
    v = 0.0
    for _ in range(100):
        v += 0.01
        if mixer.music.get_pos() <= 3.0:
            mixer.music.set_volume(v)
            time.sleep(0.02)
        else:
            mixer.music.set_volume(1.0)
            return

def processStringToLiteral(string: str):
    return string.replace("\\","\\\\").replace("'","\\'").replace("\"","\\\"").replace("`","\\`").replace("\n", "\\n")

def mainUI_slideControlerMouseDown_valid(x, y):
    if not inMainUI:
        return False
    
    for e in eventManager.clickEvents:
        if e.tag == "mainUI" and utils.inrect(x, y, e.rect):
            return False
    
    return True

def mainUI_slideControler_setValue(x, y):
    global chaptersDx
    chaptersDx = x

def settingUI_slideControlerMouseDown_valid(x, y):
    if not inSettingUI or settingState is None or SettingPlayWidgetEventManager.inRect(x, y):
        return False
    
    return (
        settingState.aTo == const.PHIGROS_SETTING_STATE.PLAY and
        w * 0.0921875 <= x <= w * 0.534375 and
        h * (180 / 1080) <= y <= h * (1015 / 1080)
    )

def settingUI_slideControler_setValue(x, y):
    global settingPlayWidgetsDy
    settingPlayWidgetsDy = y

def settingPlayWidgetEvent_valid(x, y):
    if settingState is None:
        return False
    
    return settingState.aTo == const.PHIGROS_SETTING_STATE.PLAY and inSettingUI
    
def changeChapterMouseDown(x, y):
    global changeChapterMouseDownX
    
    if y < h * (140 / 1080) or y > h * (1.0 - 140 / 1080):
        return
    elif not inMainUI:
        return
    
    changeChapterMouseDownX = x

def changeChapterMouseUp(x, y):
    global lastChangeChapterTime
    
    if y < h * (140 / 1080) or y > h * (1.0 - 140 / 1080):
        return
    elif abs(x - changeChapterMouseDownX) > w * 0.005:
        return
    elif not inMainUI:
        return
    elif time.time() - lastChangeChapterTime < 0.85: # 1.0s 动画时间, 由于是ease out, 所以可以提前一点
        return
    
    chapterX = w * 0.034375 + chaptersDx
    for index, i in enumerate(Chapters.items):
        p = getChapterP(i)
        width = getChapterWidth(p)
        if utils.indrect(x, y, getChapterRect(chapterX, width)):
            if Chapters.aTo != index:
                Chapters.aFrom, Chapters.aTo, Chapters.aSTime = Chapters.aTo, index, time.time()
                lastChangeChapterTime = time.time()
                Resource["UISound_3"].play()
            break
        chapterX += getChapterToNextWidth(p)
        
def checkOffset(now_t: float):
    global show_start_time
    
    dt = utils.checkOffset(now_t, raw_audio_length, mixer)
    if dt != 0.0:
        show_start_time += dt
        coreConfig.show_start_time = show_start_time
        phicore.CoreConfigure(coreConfig)
        
def mainRender():
    global inMainUI
    global allsongs_show_level, allsongs_show_level_font
    global allsongs_show_level_size
    
    inMainUI = True
    allsongs_show_level = const.DIFF_STRING_MAP[getUserData("internal-lastDiffIndex")]
    allsongs_show_level_font = (w + h) / 23
    allsongs_show_level_size = root.run_js_code(f"ctx.getTextSize({repr(allsongs_show_level)}, '{allsongs_show_level_font}px pgrFont')")
    
    countPlayData.cache_clear()
    faManager.faculas.clear()
    mainRenderSt = time.time()
    mixer.music.load("./resources/ChapterSelect.mp3")
    mixer.music.play(-1)
    
    messageRect = (w * 0.015, h * 0.985 - MessageButtonSize, MessageButtonSize, MessageButtonSize)
    JoinQQGuildBannerRect = (0.0, h - JoinQQGuildBannerHeight, JoinQQGuildBannerWidth, JoinQQGuildBannerHeight)
    events = []
    
    clickedMessage = False
    clickMessageTime = float("nan")
    canClickMessage = True
    messageBackTime = 7.0
    messageBacking = False
    messageBackSt = float("nan")
    def clickMessage(*args):
        nonlocal clickedMessage, clickMessageTime, canClickJoinQQGuildBanner
        if canClickMessage:
            clickMessageTime = time.time()
            clickedMessage = True
            canClickJoinQQGuildBanner = True
            Resource["UISound_1"].play()
    events.append(phigame_obj.ClickEvent(
        rect = (messageRect[0], messageRect[1], messageRect[0] + messageRect[2], messageRect[1] + messageRect[3]),
        callback = clickMessage,
        once = False,
        tag = "mainUI"
    ))
    eventManager.regClickEvent(events[-1])
    
    clickedJoinQQGuildBanner = False
    clickedJoinQQGuildBannerTime = float("nan")
    canClickJoinQQGuildBanner = False
    def clickJoinQQGuildBanner(*args):
        global inMainUI
        nonlocal clickedJoinQQGuildBanner, clickedJoinQQGuildBannerTime, messageBackTime
        
        if canClickJoinQQGuildBanner and (time.time() - clickMessageTime) > 0.1:
            clickedJoinQQGuildBannerTime = time.time()
            clickedJoinQQGuildBanner = True
            messageBackTime = float("inf")
            inMainUI = False
            Resource["UISound_2"].play()
    events.append(phigame_obj.ClickEvent(
        rect = (JoinQQGuildBannerRect[0], JoinQQGuildBannerRect[1], JoinQQGuildBannerRect[0] + JoinQQGuildBannerRect[2], JoinQQGuildBannerRect[1] + JoinQQGuildBannerRect[3]),
        callback = clickJoinQQGuildBanner,
        once = False
    ))
    eventManager.regClickEvent(events[-1])
    
    JoinQQGuildPromoNoEvent = None
    JoinQQGuildPromoYesEvent = None
    JoinQQGuildBacking = False
    JoinQQGuildBackingSt = float("nan")
    
    chapterPlayButtonRectMap = {}
    
    def JoinQQGuildPromoNoCallback(*args):
        global inMainUI
        nonlocal JoinQQGuildBacking, JoinQQGuildBackingSt, clickedJoinQQGuildBanner
        nonlocal JoinQQGuildPromoNoEvent, JoinQQGuildPromoYesEvent
        
        JoinQQGuildBacking = True
        JoinQQGuildBackingSt = time.time()
        clickedJoinQQGuildBanner = False
        
        eventManager.unregEvent(JoinQQGuildPromoNoEvent)
        eventManager.unregEvent(JoinQQGuildPromoYesEvent)
        events.remove(JoinQQGuildPromoNoEvent)
        events.remove(JoinQQGuildPromoYesEvent)
        
        JoinQQGuildPromoNoEvent = None
        JoinQQGuildPromoYesEvent = None
        inMainUI = True
    
    def JoinQQGuildPromoYesCallback(*args):
        webbrowser.open_new("https://qun.qq.com/qqweb/qunpro/share?inviteCode=21JzOLUd6J0")
        JoinQQGuildPromoNoCallback(*args)
    
    nextUI, tonextUI, tonextUISt = None, False, float("nan")
    
    def unregEvents():
        for e in events:
            eventManager.unregEvent(e)
    
    def SettingCallback(*args):
        nonlocal nextUI, tonextUI, tonextUISt
        
        if not tonextUI:
            unregEvents()
            nextUI, tonextUI, tonextUISt = settingRender, True, time.time()
            mixer.music.fadeout(500)
            Resource["UISound_2"].play()
    
    events.append(phigame_obj.ClickEvent(
        rect = (w - ButtonWidth, h - ButtonHeight, w, h),
        callback = SettingCallback,
        once = False,
        tag = "mainUI"
    ))
    eventManager.regClickEvent(events[-1])
    
    def chaptertChooseCallback(x, y):
        nonlocal nextUI, tonextUI, tonextUISt
        
        if clickedMessage: return
        
        # why need to copy: RuntimeError: dictionary changed size during iteration
        for cid, rect in chapterPlayButtonRectMap.copy().items():
            if utils.inrect(x, y, rect) and Chapters.items[Chapters.aTo].chapterId == cid:
                if not tonextUI:
                    unregEvents()

                nextUI, tonextUI, tonextUISt = lambda: loadingTransitionRender(lambda: chooseChartRender(Chapters.items[Chapters.aTo])), True, time.time()
                mixer.music.fadeout(500)
                Resource["UISound_2"].play()
                return
        
        if utils.inrect(x, y, intoChallengeModeButtonRect) and Chapters.aTo == 0:
            if not tonextUI:
                unregEvents()
                
            nextUI, tonextUI, tonextUISt = lambda: loadingTransitionRender(lambda: chooseChartRender(Chapters.items[0], True)), True, time.time()
            mixer.music.fadeout(500)
            Resource["UISound_2"].play()
    
    events.append(phigame_obj.ClickEvent(
        rect = (0, 0, w, h),
        callback = chaptertChooseCallback,
        once = False
    ))
    eventManager.regClickEvent(events[-1])
    
    while True:
        clearCanvas(wait_execute = True)
        
        drawBackground()
        
        root.run_js_code(
            f"ctx.fillRectEx(\
                0, 0, {w}, {h},\
                'rgba(0, 0, 0, 0.7)'\
            );",
            wait_execute = True
        )
        
        drawFsBgdeCoration({
            "face_brightness": 0.03,
            "grid_brightness": 0.56,
            "glow_brightness": 0.46,
            "glow_ooroff": True
        })
        
        drawButton("ButtonLeftBlack", "collectibles", (0, 0))
        drawButton("ButtonRightBlack", "setting", (w - ButtonWidth, h - ButtonHeight))
        drawChapters(chapterPlayButtonRectMap)
        
        drawAlphaImage(
            "message",
            *messageRect, 0.7,
            wait_execute = True
        )
        
        if clickedMessage and time.time() - clickMessageTime >= messageBackTime:
            clickedMessage = False
            messageBacking = True
            messageBackSt = time.time()
            canClickJoinQQGuildBanner = False
            
            if messageBackTime == 0.0:
                messageBackTime = 2.0 # back JoinQQGuild
            elif messageBackTime == 2.0:
                messageBackTime = 7.0
        
        if clickedMessage and time.time() - clickMessageTime <= 1.5:
            drawImage(
                "JoinQQGuildBanner",
                JoinQQGuildBannerRect[0] - JoinQQGuildBannerWidth + (1.0 - (1.0 - ((time.time() - clickMessageTime) / 1.5)) ** 6) * JoinQQGuildBannerWidth,
                *JoinQQGuildBannerRect[1:],
                wait_execute = True
            )
        elif not clickedMessage and messageBacking:
            if time.time() - messageBackSt > 1.5:
                messageBacking = False
                messageBackSt = time.time() - 1.5 # 防止回弹
                canClickMessage = True
            drawImage(
                "JoinQQGuildBanner",
                JoinQQGuildBannerRect[0] - (1.0 - (1.0 - ((time.time() - messageBackSt) / 1.5)) ** 6) * JoinQQGuildBannerWidth,
                *JoinQQGuildBannerRect[1:],
                wait_execute = True
            )
        elif clickedMessage:
            drawImage(
                "JoinQQGuildBanner",
                *JoinQQGuildBannerRect,
                wait_execute = True
            )
        
        if clickedMessage and canClickMessage:
            canClickMessage = False
        
        if clickedJoinQQGuildBanner:
            canClickJoinQQGuildBanner = False
            p = (time.time() - clickedJoinQQGuildBannerTime) / 0.35
            p = p if p <= 1.0 else 1.0
            ep = 1.0 - (1.0 - p) ** 2
            
            root.run_js_code(
                f"ctx.fillRectEx(\
                    0, 0, {w}, {h},\
                    'rgba(0, 0, 0, {ep * 0.5})'\
                );",
                wait_execute = True
            )
            
            root.run_js_code(
                f"mask.style.backdropFilter = 'blur({(w + h) / 120 * ep}px)';",
                wait_execute = True
            )
            
            noRect, yesRect = drawDialog(
                p, "JoinQQGuildPromo",
                const.JOINQQGUILDPROMO_DIAGONALRECTANGLEPOWER,
                (JoinQQGuildPromoWidth, JoinQQGuildPromoHeight),
                "关闭", "跳转到外部应用"
            )
            
            if JoinQQGuildPromoNoEvent is None and JoinQQGuildPromoYesEvent is None:
                JoinQQGuildPromoNoEvent = phigame_obj.ClickEvent( # once is false, remove event in callback
                    noRect, JoinQQGuildPromoNoCallback, False
                )
                JoinQQGuildPromoYesEvent = phigame_obj.ClickEvent(
                    yesRect, JoinQQGuildPromoYesCallback, False
                )
                events.append(JoinQQGuildPromoNoEvent)
                events.append(JoinQQGuildPromoYesEvent)
                eventManager.regClickEvent(JoinQQGuildPromoNoEvent)
                eventManager.regClickEvent(JoinQQGuildPromoYesEvent)
            else:
                JoinQQGuildPromoNoEvent.rect = noRect
                JoinQQGuildPromoYesEvent.rect = yesRect
        elif JoinQQGuildBacking and time.time() - JoinQQGuildBackingSt < 0.35:
            p = 1.0 - (time.time() - JoinQQGuildBackingSt) / 0.35
            ep = 1.0 - (1.0 - p) ** 2
            
            root.run_js_code(
                f"ctx.fillRectEx(\
                    0, 0, {w}, {h},\
                    'rgba(0, 0, 0, {ep * 0.5})'\
                );",
                wait_execute = True
            )
            
            root.run_js_code(
                f"mask.style.backdropFilter = 'blur({(w + h) / 120 * ep}px)';",
                wait_execute = True
            )
            
            drawDialog(
                p, "JoinQQGuildPromo",
                const.JOINQQGUILDPROMO_DIAGONALRECTANGLEPOWER,
                (JoinQQGuildPromoWidth, JoinQQGuildPromoHeight),
                "关闭", "跳转到外部应用"
            )
        elif JoinQQGuildBacking:
            root.run_js_code(
                "mask.style.backdropFilter = 'blur(0px)';",
                wait_execute = True
            )
            
            root.run_js_code(
                "dialog_canvas_ctx.clear();",
                wait_execute = True
            )
            
            JoinQQGuildBacking = False
            JoinQQGuildBackingSt = float("nan")
            messageBackTime = 0.0
        
        if time.time() - mainRenderSt < 2.0:
            p = (time.time() - mainRenderSt) / 2.0
            root.run_js_code(
                f"ctx.fillRectEx(\
                    0, 0, {w}, {h},\
                    'rgba(0, 0, 0, {(1.0 - p) ** 2})'\
                );",
                wait_execute = True
            )
        
        if tonextUI and time.time() - tonextUISt < 0.75:
            p = (time.time() - tonextUISt) / 0.75
            root.run_js_code(
                f"ctx.fillRectEx(\
                    0, 0, {w}, {h},\
                    'rgba(0, 0, 0, {1.0 - (1.0 - p) ** 2})'\
                );",
                wait_execute = True
            )
        elif tonextUI:
            inMainUI = False
            clearCanvas(wait_execute = True)
            root.run_js_wait_code()
            Thread(target=nextUI, daemon=True).start()
            break
        
        root.run_js_wait_code()

def renderPhigrosWidgets(
    widgets,
    sx: float,
    sy: float,
    dy: float,
    dx_f: typing.Callable[[float], float],
    max_width: float,
    minY: float, maxY: float
):
    root.run_js_code(
        f"ctx.save(); ctx.clipRect(0.0, {minY}, {w}, {maxY});",
        wait_execute = True
    )
    widgets_height = 0.0
    getdrect = lambda y0, y1, lfix = 0.0: (
        sx - dx_f(y1) + lfix, y0,
        sx - dx_f(y0) + max_width, y1
    )
    
    for widget in widgets:
        x, y = sx - dx_f(sy + (dy + widgets_height)), sy + (dy + widgets_height)
        
        if isinstance(widget, phigame_obj.PhiLabel):
            _temp = lambda text, align: drawText(
                x + (max_width if align == "right" else 0.0), y, text, 
                font = f"{widget.fontsize}px pgrFont",
                textAlign = align,
                textBaseline = "top",
                fillStyle = widget.color,
                wait_execute = True
            ) if text else None
            _temp(widget.left_text, "left")
            _temp(widget.right_text, "right")
            
            widgets_height += widget.fontsize
            widgets_height += widget.tonext
            widgets_height += h * (27 / 1080)
            
        elif isinstance(widget, phigame_obj.PhiSlider):
            sliderShadowRect = (
                x, y + h * (6 / 1080),
                x + max_width, y + h * ((41 + 6) / 1080)
            )
            root.run_js_code(
                f"ctx.drawDiagonalRectangle(\
                    {",".join(map(str, sliderShadowRect))},\
                    {utils.getDPower(*utils.getSizeByRect(sliderShadowRect), 75)},\
                    'rgba(0, 0, 0, 0.25)'\
                );",
                wait_execute = True
            )
            
            conButtonHeight = h * (52 / 1080)
            conWidth = w * 0.0359375 if widget.lr_button else w * 0.0046875
            lConRect = (
                x, y,
                x + conWidth, y + conButtonHeight
            )
            rConRect = (
                lConRect[0] + max_width - conWidth, lConRect[1],
                lConRect[2] + max_width - conWidth, lConRect[3]
            )
            
            root.run_js_code(
                f"ctx.drawDiagonalRectangle(\
                    {",".join(map(str, lConRect))},\
                    {utils.getDPower(*utils.getSizeByRect(lConRect), 75)},\
                    'rgba(255, 255, 255, {widget.lcon_atf.value})'\
                );",
                wait_execute = True
            )
            
            root.run_js_code(
                f"ctx.drawDiagonalRectangle(\
                    {",".join(map(str, rConRect))},\
                    {utils.getDPower(*utils.getSizeByRect(rConRect), 75)},\
                    'rgba(255, 255, 255, {widget.rcon_atf.value})'\
                );",
                wait_execute = True
            )
            
            if widget.lr_button:
                ctp_l, ctp_r = utils.getCenterPointByRect(lConRect), utils.getCenterPointByRect(rConRect)
                coniw_l, coniw_r = (w + h) * 0.003, (w + h) * 0.005 # 控制按钮图标线长度
                root.run_js_code(
                    f"ctx.drawLineEx(\
                        {ctp_l[0] - coniw_l / 2}, {ctp_l[1]},\
                        {ctp_l[0] + coniw_l / 2}, {ctp_l[1]},\
                        {(w + h) * (1 / 1500)}, 'rgb(63, 63, 63)'\
                    );",
                    wait_execute = True
                )
                root.run_js_code(
                    f"ctx.drawLineEx(\
                        {ctp_r[0] - coniw_r / 2}, {ctp_r[1]},\
                        {ctp_r[0] + coniw_r / 2}, {ctp_r[1]},\
                        {(w + h) * (1 / 1500)}, 'rgb(63, 63, 63)'\
                    );",
                    wait_execute = True
                )
                root.run_js_code(
                    f"ctx.drawLineEx(\
                        {ctp_r[0]}, {ctp_r[1] - coniw_r / 2},\
                        {ctp_r[0]}, {ctp_r[1] + coniw_r / 2},\
                        {(w + h) * (1 / 1500)}, 'rgb(63, 63, 63)'\
                    );",
                    wait_execute = True
                )
            
            slider_p = utils.sliderValueP(widget.value, widget.number_points)
            sliderBlockWidth = w * 0.0359375
            sliderFrameWidth = conWidth - conWidth * utils.getDPower(*utils.getSizeByRect(lConRect), 75) + sliderBlockWidth / 2 + w * 0.0046875
            sliderBlockHeight = conButtonHeight
            sliderBlock_x = x + sliderFrameWidth - sliderBlockWidth / 2 + slider_p * (max_width - sliderFrameWidth * 2)
            sliderBlockRect = (
                sliderBlock_x, y,
                sliderBlock_x + sliderBlockWidth, y + sliderBlockHeight
            )
            
            root.run_js_code(
                f"ctx.drawDiagonalRectangle(\
                    {",".join(map(str, sliderBlockRect))},\
                    {utils.getDPower(*utils.getSizeByRect(sliderBlockRect), 75)},\
                    'rgba(255, 255, 255, {widget.slider_atf.value})'\
                );",
                wait_execute = True
            )
            
            widget.sliderRect = (
                x + sliderFrameWidth, y,
                x + max_width - sliderFrameWidth, y + sliderBlockHeight
            )
            
            widget.lconButtonRect, widget.rconButtonRect = lConRect, rConRect
            
            widgets_height += widget.tonext
            
        elif isinstance(widget, phigame_obj.PhiCheckbox):
            drawText(
                x, y, widget.text,
                font = f"{widget.fontsize}px pgrFont",
                textAlign = "left",
                textBaseline = "top",
                fillStyle = "rgb(255, 255, 255)",
                wait_execute = True
            )
            
            checkboxShadowRect = (
                x + w * 0.321875, y + h * (6 / 1080),
                x + w * 0.321875 + w * 0.06875, y + h * ((41 + 6) / 1080)
            )
            root.run_js_code(
                f"ctx.drawDiagonalRectangle(\
                    {",".join(map(str, checkboxShadowRect))},\
                    {utils.getDPower(*utils.getSizeByRect(checkboxShadowRect), 75)},\
                    'rgba(0, 0, 0, 0.25)'\
                );",
                wait_execute = True
            )
            
            checkAnimationP = (time.time() - widget.check_animation_st) / 0.2
            checkAnimationP = utils.fixorp(checkAnimationP)
            if not widget.checked:
                checkAnimationP = 1.0 - checkAnimationP
            checkAnimationP = 1.0 - (1.0 - checkAnimationP) ** 2
            
            checkButtonDx = (w * 0.06875 - w * 0.0375) * checkAnimationP
            checkButtonRect = (
                x + w * 0.321875 + checkButtonDx, y,
                x + w * 0.321875 + w * 0.0375 + checkButtonDx, y + h * (52 / 1080)
            )
            
            drawAlphaImage(
                "checked",
                x + w * 0.340625 - CheckedIconWidth / 2,
                y + utils.getSizeByRect(checkButtonRect)[1] / 2 - CheckedIconHeight / 2,
                CheckedIconWidth, CheckedIconHeight,
                checkAnimationP ** 0.5,
                wait_execute = True
            )
            
            root.run_js_code(
                f"ctx.drawDiagonalRectangle(\
                    {",".join(map(str, checkButtonRect))},\
                    {utils.getDPower(*utils.getSizeByRect(checkButtonRect), 75)},\
                    'rgba(255, 255, 255, {widget.box_atf.value})'\
                );",
                wait_execute = True
            )
            
            widget.checkboxRect = checkboxShadowRect
            
            widgets_height += widget.tonext
            
        elif isinstance(widget, phigame_obj.PhiButton):
            buttonDx = (
                (max_width / 2)
                if widget.anchor == "center"
                else ((widget.width / 2) if widget.anchor == "left" else (max_width - widget.width / 2))
            ) 
            
            buttonRect = (
                x + buttonDx - widget.width / 2, y,
                x + buttonDx + widget.width / 2, y + h * (80 / 1080)
            )
            
            root.run_js_code(
                f"ctx.drawDiagonalRectangle(\
                    {",".join(map(str, buttonRect))},\
                    {utils.getDPower(*utils.getSizeByRect(buttonRect), 75)},\
                    'rgba(255, 255, 255, {widget.button_atf.value})'\
                );",
                wait_execute = True
            )
            
            drawText(
                buttonRect[0] + (buttonRect[2] - buttonRect[0]) / 2, buttonRect[1] + (buttonRect[3] - buttonRect[1]) / 2,
                widget.text,
                font = f"{widget.fontsize}px pgrFont",
                textAlign = "center",
                textBaseline = "middle",
                fillStyle = "rgb(0, 0, 0)",
                wait_execute = True
            )
            
            widget.buttonRect = buttonRect
        
        elif isinstance(widget, phigame_obj.PhiCombobox):
            cbbHeight = h * (80 / 1080)
            
            cbbShadowRect = (
                x, y + h * (6 / 1080),
                x + max_width, y + cbbHeight + h * (6 / 1080)
            )
            rawCbbShadowRect = cbbShadowRect
            cbbShadowRectDPower = utils.getDPower(*utils.getSizeByRect(cbbShadowRect), 75)
            cbbColor = (*((255, ) * 3), 1.0)
            
            totop_itemnum = (len(widget.values) - 1) // 2
            tobottom_itemnum = len(widget.values) - 1 - totop_itemnum
            totop_height = totop_itemnum * cbbHeight
            tobottom_height = tobottom_itemnum * cbbHeight
            items_starty = cbbShadowRect[1] - totop_height
            
            onRect = getdrect(
                items_starty,
                cbbShadowRect[3] + tobottom_height,
                (cbbShadowRect[2] - cbbShadowRect[0]) * cbbShadowRectDPower
            )
            
            cbbShadowRect = tuple(utils.nums_interp(cbbShadowRect, onRect, widget.on_atf.value))
            cbbShadowRectDPower = utils.getDPower(*utils.getSizeByRect(cbbShadowRect), 75)
            
            utils.shadowDrawer.root = root
            with utils.shadowDrawer(f"rgba(0, 0, 0, {widget.on_atf.value})", (w + h) / 55):
                root.run_js_code(
                    f"ctx.drawDiagonalRectangle(\
                        {",".join(map(str, cbbShadowRect))},\
                        {cbbShadowRectDPower},\
                        'rgba{cbbColor}'\
                    );",
                    wait_execute = True
                )
            
            ctxSave(wait_execute=True)
            ctxBeginPath(wait_execute=True)
            root.run_js_code(
                f"ctx.diagonalRectangle(\
                    {",".join(map(str, cbbShadowRect))},\
                    {cbbShadowRectDPower}\
                );",
                wait_execute = True
            )
            ctxClip(wait_execute=True)
            ctxMutGlobalAlpha(widget.on_atf.value, wait_execute=True)
            
            _gettextx = lambda basex: (
                basex + ((max_width - cbbLRPadding) if widget.anchor == "right" else (
                    (max_width / 2) if widget.anchor == "center" else 0.0
                ))
            )
            
            drawing_itemy = items_starty
            getitemx_fromcbbi = lambda i, ymore = 0.0: cbbShadowRect[0] + (
                    cbbShadowRect[2] - cbbShadowRect[0]
                ) * cbbShadowRectDPower * (
                    1.0 - (
                        (cbbHeight * i + cbbHeight / 2 + ymore)
                        / (cbbShadowRect[3] - cbbShadowRect[1])
                    )
                )
            
            cbbLRPadding = max_width * 0.07
            arrow_pos = (
                x + max_width - cbbLRPadding,
                y + h * (6 / 1080) + cbbHeight / 2
            )
            
            onarrow_pos = arrow_pos
            for i, v in enumerate(widget.values):
                itemx = getitemx_fromcbbi(i)
                
                drawText(
                    _gettextx(itemx), drawing_itemy + cbbHeight / 2,
                    f"{v}",
                    font = f"{widget.fontsize}px pgrFont",
                    textAlign = widget.anchor,
                    textBaseline = "middle",
                    fillStyle = widget.text_color,
                    wait_execute = True
                )
                
                if i == widget.value:
                    onarrow_pos = (
                        getitemx_fromcbbi(widget.value_atf.value, cbbHeight / 2) + max_width - cbbLRPadding,
                        items_starty + cbbHeight * widget.value_atf.value + cbbHeight / 2
                    )
                
                if i != len(widget.values) - 1:
                    sepliney = drawing_itemy + cbbHeight
                    width = (cbbShadowRect[2] - cbbShadowRect[0]) * (1.0 - cbbShadowRectDPower)
                    
                    ctxSave(wait_execute=True)
                    ctxMutGlobalAlpha(0.8, wait_execute=True)
                    drawLine(
                        getitemx_fromcbbi(i + 1 / 2) + cbbLRPadding * 1.5, sepliney,
                        getitemx_fromcbbi(i + 1 / 2) + width - cbbLRPadding * 1.5, sepliney,
                        strokeStyle = widget.text_color,
                        lineWidth = 1,
                        wait_execute = True
                    )
                    ctxRestore(wait_execute=True)
                
                drawing_itemy += cbbHeight
            
            ctxRestore(wait_execute=True)
            
            arrow_pos = tuple(utils.nums_interp(arrow_pos, onarrow_pos, widget.on_atf.value))
            
            with ColorMultiplyFilter(color=tuple(map(lambda x: 255 - x, cbbColor))):
                drawAlphaImage(
                    "combobox_arrow",
                    arrow_pos[0] - ComboboxArrowWidth / 2,
                    arrow_pos[1] - ComboboxArrowHeight / 2,
                    ComboboxArrowWidth, ComboboxArrowHeight,
                    cbbColor[-1],
                    wait_execute = True
                )
            
            _temp = lambda text, dy = 0.0: drawText(
                _gettextx(x), y + dy,
                text, 
                font = f"{widget.fontsize}px pgrFont",
                textAlign = widget.anchor,
                textBaseline = "middle",
                fillStyle = widget.text_color,
                wait_execute = True
            ) if text else None
            
            ctxSave(wait_execute=True)
            ctxMutGlobalAlpha(1.0 - widget.on_atf.value, wait_execute=True)
            _temp(widget.vaild_text, cbbHeight / 2)
            ctxRestore(wait_execute=True)
            
            widget.comboboxRect = rawCbbShadowRect
            widget.onRect = cbbShadowRect
            widget.itemStart = items_starty
            widget.itemHeight = cbbHeight
            
            widgets_height += cbbShadowRect[3] - rawCbbShadowRect[1] - h * (95 / 1080)
        
        if not isinstance(widget, phigame_obj.PhiLabel):
            widgets_height += h * (150 / 1080)
            
    root.run_js_code(
        "ctx.restore();",
        wait_execute = True
    )
    
    return widgets_height
        
def settingRender(backUI: typing.Callable[[], typing.Any] = mainRender):
    global inSettingUI, settingState
    global settingPlayWidgetsDy
    global PlaySettingWidgets
    
    inSettingUI = True
    
    bgrespacker = webcv.LazyPILResPacker(root)
    for i, bg in enumerate(assetConfig["backgrounds"]):
        bgrespacker.reg_img(utils.gtpresp(bg), f"background_{i}")
    bgrespacker.load(*bgrespacker.pack())
    
    settingState = phigame_obj.SettingState()
    clickedBackButton = False
    settingPlayWidgetsDy = 0.0
    CalibrationClickSoundPlayed = False
    editingUserData = False
    CalibrationClickEffects = []
    CalibrationClickEffectLines = []
    editUserNameRect, editIntroductionRect = const.EMPTY_RECT, const.EMPTY_RECT
    editAvatarRect, editBackgroundRect = const.EMPTY_RECT, const.EMPTY_RECT
    loginButtonRect = const.EMPTY_RECT
    nextUI, tonextUI, tonextUISt = None, False, float("nan")
    ShowOpenSource, ShowOpenSourceSt = False, float("nan")
    CloseOpenSource, CloseOpenSourceSt = False, float("nan")
    showAvatars, showAvatarsSt = False, float("nan")
    showBackgrounds, showBackgroundsSt = False, float("nan")
    chooseRects = {"avatars": {}, "backgrounds": {}}
    lastClickChooseAvatarOrBackgroundPos = (0.0, 0.0)
    settingUIOpenSourceLicenseSlideControler.maxValueY = root.run_js_code(
        f"ctx.drawRectMultilineText(\
            -{w}, -{h}, 0, 0,\
            {repr(const.PHI_OPENSOURCELICENSE)},\
            'rgb(255, 255, 255)', '{(w + h) / 145}px pgrFont', {(w + h) / 145}, 1.25\
        );"
    ) + h * (143 / 1080) * 2 - h
    
    mixer.music.load("./resources/Calibration.wav")
    mixer.music.play(-1)
    
    def updatebg():
        ubgjsname = root.get_img_jsvarname("userBackground")
        
        try:
            bgimname = f"background_{assetConfig["backgrounds"].index(getUserData("userdata-userBackground"))}"
        except ValueError:
            setUserData("userdata-userBackground", assetConfig["backgrounds"][0])
            saveUserData(userData)
            return updatebg()
        
        root.run_js_code(f"{ubgjsname} = blurImg({root.get_img_jsvarname(bgimname)}, {(w + h) / 125});")
    
    def unregEvents():
        eventManager.unregEvent(clickBackButtonEvent)
        eventManager.unregEvent(settingMainClickEvent)
        eventManager.unregEvent(settingMainReleaseEvent)
    
    def clickBackButtonCallback(*args):
        nonlocal clickedBackButton
        nonlocal nextUI, tonextUI, tonextUISt
        
        if not clickedBackButton and inSettingUI:
            unregEvents()
            nextUI, tonextUI, tonextUISt = backUI, True, time.time()
            Resource["UISound_4"].play()
            mixer.music.fadeout(500)
    
    clickBackButtonEvent = phigame_obj.ClickEvent(
        rect = (0, 0, ButtonWidth, ButtonHeight),
        callback = clickBackButtonCallback,
        once = False
    )
    eventManager.regClickEvent(clickBackButtonEvent)
    
    lastChangeSettingStateTime = float("-inf")
    
    def _setSettingState(t: int):
        nonlocal lastChangeSettingStateTime
        
        if time.time() - lastChangeSettingStateTime < 0.6:
            return
        elif t == settingState.aTo:
            return
        lastChangeSettingStateTime = time.time()
        settingState.changeState(t)
    
    def settingMainClickCallback(x, y):
        global inSettingUI
        nonlocal nextUI, tonextUI, tonextUISt
        nonlocal ShowOpenSource, ShowOpenSourceSt
        nonlocal CloseOpenSource, CloseOpenSourceSt
        nonlocal editingUserData
        nonlocal showAvatars, showAvatarsSt
        nonlocal showBackgrounds, showBackgroundsSt
        nonlocal lastClickChooseAvatarOrBackgroundPos
        
        # 游玩
        if utils.inrect(x, y, (
            w * 346 / 1920, h * 35 / 1080,
            w * 458 / 1920, h * 97 / 1080
        )) and inSettingUI and not editingUserData:
            if settingState.aTo == const.PHIGROS_SETTING_STATE.PLAY:
                return
            
            Thread(target=lambda: (time.sleep(settingState.atime / 2), mixer.music.stop(), mixer.music.play(-1)), daemon=True).start()
            _setSettingState(const.PHIGROS_SETTING_STATE.PLAY)
        
        # 账号与统计
        if utils.inrect(x, y, (
            w * 540 / 1920, h * 35 / 1080,
            w * 723 / 1920, h * 97 / 1080
        )) and inSettingUI and not editingUserData:
            if settingState.aTo == const.PHIGROS_SETTING_STATE.ACCOUNT_AND_COUNT:
                return
            
            mixer.music.fadeout(500)
            _setSettingState(const.PHIGROS_SETTING_STATE.ACCOUNT_AND_COUNT)
        
        # 其他
        if utils.inrect(x, y, (
            w * 807 / 1920, h * 35 / 1080,
            w * 915 / 1920, h * 97 / 1080
        )) and inSettingUI and not editingUserData:
            if settingState.aTo == const.PHIGROS_SETTING_STATE.OTHER:
                return
            
            mixer.music.fadeout(500)
            _setSettingState(const.PHIGROS_SETTING_STATE.OTHER)
        
        # 校准延迟点击扩散的线条
        if settingState.atis_p and utils.inrect(x, y, (
            w * 0.6015625, 0.0,
            w, h
        )) and inSettingUI:
            if mixer.music.get_busy():
                mixer_pos = mixer.music.get_pos()
                CalibrationClickEffectLines.append((time.time(), mixer_pos))
        
        # 账号与统计 - 编辑
        if settingState.atis_a and utils.inrect(x, y, (
            w * 0.85625, h * (181 / 1080),
            w * 0.921875, h * (220 / 1080)
        )) and not (showAvatars or showBackgrounds):
            editingUserData = not editingUserData
        
        # 编辑用户名字
        if settingState.atis_a and utils.inrect(x, y, editUserNameRect) and editingUserData and not (showAvatars or showBackgrounds):
            newName = root.run_js_code(f"prompt('请输入新名字', {repr(getUserData("userdata-userName"))});")
            if newName is not None:
                setUserData("userdata-userName", newName)
                updateFontSizes()
                saveUserData(userData)
        
        # 编辑用户介绍
        if settingState.atis_a and utils.inrect(x, y, editIntroductionRect) and editingUserData and not (showAvatars or showBackgrounds):
            newName = root.run_js_code(f"prompt('请输入新介绍 (输入\"\\\\n\"可换行)', {repr(getUserData("userdata-selfIntroduction").replace("\n", "\\n"))});")
            if newName is not None:
                setUserData("userdata-selfIntroduction", newName.replace("\\n", "\n"))
                updateFontSizes()
                saveUserData(userData)
        
        # 编辑用户头像
        if settingState.atis_a and utils.inrect(x, y, editAvatarRect) and editingUserData and not (showAvatars or showBackgrounds):
            showAvatars, showAvatarsSt = True, time.time()
            settingUIChooseAvatarAndBackgroundSlideControler.setDy(0.0)
        
        # 编辑用户背景
        if settingState.atis_a and utils.inrect(x, y, editBackgroundRect) and editingUserData and not (showAvatars or showBackgrounds):
            showBackgrounds, showBackgroundsSt = True, time.time()
            settingUIChooseAvatarAndBackgroundSlideControler.setDy(0.0)

        # 编辑用户头像/背景 - 关闭
        if settingState.atis_a and utils.inrect(x, y, (
            w * 0.9078125 - (w + h) * 0.014 / 2, h * (225 / 1080) - (w + h) * 0.014 / 2,
            w * 0.9078125 + (w + h) * 0.014 / 2, h * (225 / 1080) + (w + h) * 0.014 / 2
        )) and (showAvatars or showBackgrounds):
            if showAvatars: showAvatars, showAvatarsSt = False, time.time()
            if showBackgrounds: showBackgrounds, showBackgroundsSt = False, time.time()
            chooseRects["avatars"].clear()
            chooseRects["backgrounds"].clear()
        
        # 编辑用户头像 - 选择
        if settingState.atis_a and showAvatars and (time.time() - showAvatarsSt) > 0.15:
            lastClickChooseAvatarOrBackgroundPos = (x, y)
        
        # 编辑用户背景 - 选择
        if settingState.atis_a and showBackgrounds and (time.time() - showBackgroundsSt) > 0.15:
            lastClickChooseAvatarOrBackgroundPos = (x, y)
        
        # 登录
        if settingState.atis_a and utils.inrect(x, y, loginButtonRect) and not (showAvatars or showBackgrounds):
            root.run_js_code(f"alert({repr("你在想 peach")});")
        
        # 音频问题疑难解答
        if settingState.atis_o and utils.inrect(x, y, otherSettingButtonRects[0]) and inSettingUI:
            Resource["UISound_4"].play()
            unregEvents()
            nextUI, tonextUI, tonextUISt = audioQARender, True, time.time()
        
        # 观看教学
        if settingState.atis_o and utils.inrect(x, y, otherSettingButtonRects[1]) and inSettingUI:
            unregEvents()
            nextUI, tonextUI, tonextUISt = lambda: chartPlayerRender(
                chartAudio = "./resources/introduction_chart/audio.mp3",
                chartImage = "./resources/introduction_chart/image.png",
                chartFile = "./resources/introduction_chart/chart.json",
                startAnimation = False,
                chart_information = {
                    "Name": "Introduction",
                    "Artist": "姜米條",
                    "Level": "IN Lv.13",
                    "Illustrator": "L-sp4",
                    "Charter": "星空孤雁",
                    "BackgroundDim": None
                },
                blackIn = True,
                nextUI = mainRender
            ), True, time.time()
        
        # 关于我们
        if settingState.atis_o and utils.inrect(x, y, otherSettingButtonRects[2]) and inSettingUI:
            unregEvents()
            nextUI, tonextUI, tonextUISt = aboutUsRender, True, time.time()
        
        # 开源许可证
        if settingState.atis_o and utils.inrect(x, y, otherSettingButtonRects[3]) and inSettingUI:
            inSettingUI = False
            ShowOpenSource, ShowOpenSourceSt = True, time.time()
            settingUIOpenSourceLicenseSlideControler.setDy(settingUIOpenSourceLicenseSlideControler.minValueY)
        
        # 隐私政策
        if settingState.atis_o and utils.inrect(x, y, otherSettingButtonRects[4]) and inSettingUI:
            webbrowser.open(const.PHIGROS_LINKS.PRIVACYPOLIC)
        
        # 推特链接
        if settingState.atis_o and utils.inrect(x, y, (
            w * 128 / 1920, h * 1015 / 1080,
            w * 315 / 1920, h * 1042 / 1080
        )) and inSettingUI:
            webbrowser.open(const.PHIGROS_LINKS.TWITTER)
        
        # B站链接
        if settingState.atis_o and utils.inrect(x, y, (
            w * 376 / 1920, h * 1015 / 1080,
            w * 561 / 1920, h * 1042 / 1080
        )) and inSettingUI:
            webbrowser.open(const.PHIGROS_LINKS.BILIBILI)
        
        # QQ链接
        if settingState.atis_o and utils.inrect(x, y, (
            w * 626 / 1920, h * 1015 / 1080,
            w * 856 / 1920, h * 1042 / 1080
        )) and inSettingUI:
            webbrowser.open(const.PHIGROS_LINKS.QQ)
        
        # Github链接
        if settingState.atis_o and utils.inrect(x, y, (
            w * 881 / 1920, h * 1015 / 1080,
            w * 1079 / 1920, h * 1042 / 1080
        )) and inSettingUI:
            webbrowser.open(const.PHIGROS_LINKS.GITHUB)
        
        # 开源许可证的关闭按钮
        if utils.inrect(x, y, (0, 0, ButtonWidth, ButtonHeight)) and ShowOpenSource and time.time() - ShowOpenSourceSt > 0.15:
            ShowOpenSource, ShowOpenSourceSt = False, float("nan")
            CloseOpenSource, CloseOpenSourceSt = True, time.time()
    
    def settingMainReleaseCallback(x, y):
        nonlocal showAvatars, showAvatarsSt
        nonlocal showBackgrounds, showBackgroundsSt
        
        if settingState.atis_a and showAvatars and utils.getLineLength(x, y, *lastClickChooseAvatarOrBackgroundPos) <= (w + h) / 400:
            for v, r in chooseRects["avatars"].items():
                if utils.inrect(x, y, r):
                    showAvatars, showAvatarsSt = False, time.time()
                    setUserData("userdata-userAvatar", assetConfig["avatars"][v])
                    saveUserData(userData)
                    updateUserAvatar()
        
        if settingState.atis_a and showBackgrounds and utils.getLineLength(x, y, *lastClickChooseAvatarOrBackgroundPos) <= (w + h) / 400:
            for v, r in chooseRects["backgrounds"].items():
                if utils.inrect(x, y, r):
                    showBackgrounds, showBackgroundsSt = False, time.time()
                    setUserData("userdata-userBackground", assetConfig["backgrounds"][v])
                    saveUserData(userData)
                    updatebg()
    
    settingMainClickEvent = phigame_obj.ClickEvent(
        rect = (0, 0, w, h),
        callback = settingMainClickCallback,
        once = False
    )
    eventManager.regClickEvent(settingMainClickEvent)
    settingMainReleaseEvent = phigame_obj.ReleaseEvent(
        callback = settingMainReleaseCallback
    )
    eventManager.regReleaseEvent(settingMainReleaseEvent)

    settingDx = [0.0, 0.0, 0.0]
    
    def getShadowDiagonalXByY(y: float):
        return w * utils.getDPower(w, h, 75) * ((h - y) / h)
    
    def drawOtherSettingButton(x0: float, y0: float, x1: float, y1: float, dpower: float):
        root.run_js_code(
            f"ctx.drawDiagonalRectangle(\
                {x0}, {y0},\
                {x1}, {y1},\
                {dpower}, '#FFFFFF'\
            );",
            wait_execute = True
        )
        
        drawImage(
            "Arrow_Right_Black",
            x0 + (x1 - x0) / 2 - SettingUIOtherIconWidth / 2,
            y0 + (y1 - y0) / 2 - SettingUIOtherIconHeight / 2,
            SettingUIOtherIconWidth,
            SettingUIOtherIconHeight,
            wait_execute = True
        )
    
    otherSettingButtonRects = [
        (
            w * (0.0515625 + 0.0265625 + 0.25) + getShadowDiagonalXByY(h * 0.575), h * 0.575,
            w * (0.0515625 + 0.0265625 + 0.25 + 0.046875) + getShadowDiagonalXByY(h * 0.575), h * (0.575 + 0.05)
        ),
        (
            w * (0.0515625 + 0.0265625 + 0.25) + getShadowDiagonalXByY(h * 0.675), h * 0.675,
            w * (0.0515625 + 0.0265625 + 0.25 + 0.046875) + getShadowDiagonalXByY(h * 0.675), h * (0.675 + 0.05)
        ),
        (
            w * (0.0515625 + 0.0265625 + 0.25) + getShadowDiagonalXByY(h * 0.775), h * 0.775,
            w * (0.0515625 + 0.0265625 + 0.25 + 0.046875) + getShadowDiagonalXByY(h * 0.775), h * (0.775 + 0.05)
        ),
        (
            w * (0.0515625 + 0.0265625 + 0.4015625 + 0.25) + getShadowDiagonalXByY(h * 0.575), h * 0.575,
            w * (0.0515625 + 0.0265625 + 0.4015625 + 0.25 + 0.046875) + getShadowDiagonalXByY(h * 0.575), h * (0.575 + 0.05)
        ),
        (
            w * (0.0515625 + 0.0265625 + 0.4015625 + 0.25) + getShadowDiagonalXByY(h * 0.675), h * 0.675,
            w * (0.0515625 + 0.0265625 + 0.4015625 + 0.25 + 0.046875) + getShadowDiagonalXByY(h * 0.675), h * (0.675 + 0.05)
        )
    ]
    
    def drawPlaySetting(dx: float, alpha: float):
        nonlocal CalibrationClickSoundPlayed, CalibrationClickEffectLines
        nonlocal CalibrationClickEffects
        
        if alpha == 0.0: return
        
        root.run_js_code(
            f"ctx.save(); ctx.translate({-dx}, 0); ctx.globalAlpha = {alpha};",
            wait_execute = True
        )
        
        lastMaxVY = settingUIPlaySlideControler.maxValueY
        settingUIPlaySlideControler.maxValueY = renderPhigrosWidgets(
            list(PlaySettingWidgets.values()),
            w * 0.175, h * 0.175,
            settingPlayWidgetsDy,
            lambda x: getShadowDiagonalXByY(h - x),
            w * 0.3953125,
            h * (180 / 1080), h * (1015 / 1080)
        ) - h * (835 / 1080) # 这里为什么要减, ???
        
        if settingUIPlaySlideControler.maxValueY != lastMaxVY:
            settingUIPlaySlideControler.check()
        
        lineColor = "255, 255, 170" if getUserData("setting-enableFCAPIndicator") else "255, 255, 255"
        
        ctxSave(wait_execute=True)
        ctxBeginPath(wait_execute=True)
        root.run_js_code(
            f"ctx.diagonalRectangle(\
                {",".join(map(str, ShadowRect))},\
                {ShadowDPower}\
            );",
            wait_execute = True
        )
        ctxRect(0, 0, w, h, wait_execute=True)
        ctxClip("evenodd", wait_execute=True)
        root.run_js_code( # 2 layers alpha
            f"ctx.drawLineEx(\
                {0}, {h * 0.8},\
                {w}, {h * 0.8},\
                {h * const.LINEWIDTH.PHI}, 'rgba({lineColor}, {alpha})'\
            );",
            wait_execute = True
        )
        ctxRestore(wait_execute=True)
        
        CalibrationMusicPosition = mixer.music.get_pos()
        if CalibrationMusicPosition > 0.0:
            CalibrationMusicPosition += getUserData("setting-chartOffset") / 1000
            CalibrationMusicPosition %= 2.0
            noteWidth = w * const.NOTE_DEFAULTSIZE * getUserData("setting-noteScale")
            noteHeight = noteWidth * Resource["Notes"]["Tap"].height / Resource["Notes"]["Tap"].width
            if CalibrationMusicPosition < 1.0:
                noteY = h * 0.85 * CalibrationMusicPosition - h * 0.05
                drawImage(
                    "Note_Tap",
                    w * 0.75 - noteWidth / 2, noteY - noteHeight / 2,
                    noteWidth, noteHeight,
                    wait_execute = True
                )
                if CalibrationClickSoundPlayed:
                    CalibrationClickSoundPlayed = False
            else:
                if not CalibrationClickSoundPlayed:
                    CalibrationClickSoundPlayed = True
                    if getUserData("setting-enableClickSound"):
                        Resource["CalibrationHit"].play()
                    CalibrationClickEffects.append((time.time(), getUserData("setting-noteScale")))
            
            for st, size in CalibrationClickEffects:
                p = (time.time() - st) / 0.5
                if p > 1.0: continue
                
                phicore.w = w
                random.seed(st)
                random.seed(random.uniform(-st, st))
                phicore.processClickEffectBase(
                    x = w * 0.75, y = h * 0.8, rotate = 0.0,
                    p = p, rblocks = None,
                    perfect = True,
                    noteWidth = w * const.NOTE_DEFAULTSIZE * size,
                    root = root
                )
        
        for t, p in CalibrationClickEffectLines: # vn, ? (time, mixer_pos)
            ap = (time.time() - t) / 1.1
            if ap > 1.0: continue
            
            y = h * 0.85 * ((p + getUserData("setting-chartOffset")) % 2.0) - h * 0.05
            lw = w * ap * 3.0
            root.run_js_code( # 这里alpha值化简了
                f"ctx.drawLineEx(\
                    {w * 0.75 - lw / 2}, {y},\
                    {w * 0.75 + lw / 2}, {y},\
                    {h * const.LINEWIDTH.PHI * 0.75}, 'rgba(255, 255, 255, {(ap - 1.0) ** 2})'\
                );",
                wait_execute = True
            )
        
        CalibrationClickEffectLines = list(filter(lambda x: time.time() - x[0] <= 1.1, CalibrationClickEffectLines))
        CalibrationClickEffects = list(filter(lambda x: time.time() - x[0] <= 0.5, CalibrationClickEffects))
        
        root.run_js_code(
            f"ctx.restore();",
            wait_execute = True
        )
    
    def drawAccountAndCountSetting(dx: float, alpha: float):
        nonlocal editUserNameRect, editIntroductionRect
        nonlocal editAvatarRect, editBackgroundRect
        nonlocal loginButtonRect
        
        if alpha == 0.0: return
        
        root.run_js_code(
            f"ctx.save(); ctx.translate({- dx}, 0); ctx.globalAlpha = {alpha};",
            wait_execute = True
        )
        
        drawText(
            w * 0.1765625, h * 0.2,
            "玩家信息",
            font = f"{(w + h) / 75}px pgrFont",
            textAlign = "left",
            textBaseline = "bottom",
            fillStyle = "rgb(255, 255, 255)",
            wait_execute = True
        )
        
        root.run_js_code(
            f"ctx.drawDiagonalRectangleClipImage(\
                {w * 0.0796875}, {h * 0.225},\
                {w * 0.940625}, {h * 0.65},\
                {root.get_img_jsvarname("userBackground")},\
                0, {(h * 0.425 - w * 0.8609375 / 16 * 9) / 2},\
                {w * 0.8609375}, {w * 0.8609375 / 16 * 9},\
                {utils.getDPower(w * 0.8609375, h * 0.425, 75)}, 1.0\
            );",
            wait_execute = True
        )
        
        root.run_js_code(
            f"ctx.drawDiagonalRectangle(\
                {w * 0.0796875}, {h * 0.225},\
                {w * 0.940625}, {h * 0.65},\
                {utils.getDPower(w * 0.8609375, h * 0.425, 75)},\
                'rgba(0, 0, 0, 0.375)'\
            );",
            wait_execute = True
        )
        
        if editingUserData:
            editBackgroundIconSize = (w + h) * 0.007
            editBackgroundRect = (
                w * 0.8796875, h * (257 / 1080),
                w * 0.93125, h * (301 / 1080)
            )
            editBackgroundRectSize = utils.getSizeByRect(editBackgroundRect)
            root.run_js_code(
                f"ctx.drawDiagonalRectangle(\
                    {",".join(map(str, editBackgroundRect))},\
                    {utils.getDPower(*editBackgroundRectSize, 75)},\
                    'rgb(255, 255, 255)'\
                );",
                wait_execute = True
            )
            
            drawImage(
                "edit",
                editBackgroundRect[0] + editBackgroundRectSize[0] / 2 - editBackgroundIconSize / 2,
                editBackgroundRect[1] + editBackgroundRectSize[1] / 2 - editBackgroundIconSize / 2,
                editBackgroundIconSize, editBackgroundIconSize,
                wait_execute = True
            )
        
        leftBlackDiagonalX = 0.538
        root.run_js_code(
            f"ctx.drawDiagonalRectangle(\
                {w * 0.0796875}, {h * 0.225},\
                {w * ((0.940625 - 0.0796875) * leftBlackDiagonalX + 0.0796875)}, {h * 0.65},\
                {utils.getDPower(w * ((0.940625 - 0.0796875) * leftBlackDiagonalX), h * 0.425, 75)},\
                'rgba(0, 0, 0, 0.25)'\
            );",
            wait_execute = True
        )
        
        root.run_js_code(
            f"ctx.drawDiagonalRectangle(\
                {w * 0.121875}, {h * (283 / 1080)},\
                {w * 0.465625}, {h * (397 / 1080)},\
                {utils.getDPower(w * 0.34375, h * (114 / 1080), 75)},\
                'rgba(0, 0, 0, 0.9)'\
            );",
            wait_execute = True
        )
        
        avatarSize = max(w * 0.096875, h * (120 / 1080))
        avatarRect = (
            w * 0.128125, h * (280 / 1080),
            w * 0.225, h * (400 / 1080)
        )
        avatarWidth, avatarHeight = utils.getSizeByRect(avatarRect)
        root.run_js_code(
            f"ctx.drawDiagonalRectangleClipImage(\
                {",".join(map(str, avatarRect))},\
                {root.get_img_jsvarname("userAvatar")},\
                {(avatarWidth - avatarSize) / 2},\
                {(avatarHeight - avatarSize) / 2},\
                {avatarSize}, {avatarSize},\
                {utils.getDPower(avatarWidth, avatarHeight, 75)}, 1.0\
            );",
            wait_execute = True
        )
        
        if editingUserData:
            editAvatarIconSize = (w + h) * 0.007
            editAvatarRect = (
                avatarRect[0] + avatarWidth * (105 / 185),
                avatarRect[1],
                avatarRect[2],
                avatarRect[1] + avatarHeight * (1 / 3)
            )
            editAvatarRectSize = utils.getSizeByRect(editAvatarRect)
            root.run_js_code(
                f"ctx.drawDiagonalRectangle(\
                    {",".join(map(str, editAvatarRect))},\
                    {utils.getDPower(*editAvatarRectSize, 75)},\
                    'rgb(255, 255, 255)'\
                );",
                wait_execute = True
            )
            
            drawImage(
                "edit",
                editAvatarRect[0] + editAvatarRectSize[0] / 2 - editAvatarIconSize / 2,
                editAvatarRect[1] + editAvatarRectSize[1] / 2 - editAvatarIconSize / 2,
                editAvatarIconSize, editAvatarIconSize,
                wait_execute = True
            )
        
        drawText(
            w * 0.234375, h * (340 / 1080),
            getUserData("userdata-userName"),
            font = f"{userName_FontSize}px pgrFont",
            textAlign = "left",
            textBaseline = "middle",
            fillStyle = "rgb(255, 255, 255)",
            wait_execute = True
        )
        
        rankingScoreRect = (
            w * 0.465625 - (w * 0.34375) * utils.getDPower(w * 0.34375, h * (114 / 1080), 75),
            h * (357 / 1080),
            w * 0.5140625,
            h * (397 / 1080)
        )
        root.run_js_code( # 这个矩形真头疼...
            f"ctx.drawDiagonalRectangle(\
                {",".join(map(str, rankingScoreRect))},\
                {utils.getDPower(rankingScoreRect[2] - rankingScoreRect[0], rankingScoreRect[3] - rankingScoreRect[1], 75)},\
                'rgb(255, 255, 255)'\
            );",
            wait_execute = True
        )
        
        drawText(
            (rankingScoreRect[0] + rankingScoreRect[2]) / 2, (rankingScoreRect[1] + rankingScoreRect[3]) / 2,
            f"{getUserData("userdata-rankingScore"):.2f}",
            font = f"{(rankingScoreRect[3] - rankingScoreRect[1]) * 0.8}px pgrFont",
            textAlign = "center",
            textBaseline = "middle",
            fillStyle = "rgb(83, 83, 83)",
            wait_execute = True
        )
        
        selfIntroduction_fontSize = (w + h) / 135
        root.run_js_code(
            f"ctx.drawRectMultilineText(\
                {w * 0.1484375}, {h * (447 / 1080)},\
                {w * 0.4546875}, {h * (660 / 1080)},\
                {repr(getUserData("userdata-selfIntroduction"))},\
                'rgb(255, 255, 255)', '{selfIntroduction_fontSize}px pgrFont',\
                {selfIntroduction_fontSize}, 1.15\
            );",
            wait_execute = True
        )
        
        editButtonRect = (
            w * 0.85625, h * (181 / 1080),
            w * 0.921875, h * (220 / 1080)
        )
        root.run_js_code(
            f"ctx.drawDiagonalRectangle(\
                {",".join(map(str, editButtonRect))},\
                {utils.getDPower(editButtonRect[2] - editButtonRect[0], editButtonRect[3] - editButtonRect[1], 75)},\
                'rgb(255, 255, 255)'\
            );",
            wait_execute = True
        )
        
        drawText(
            (editButtonRect[0] + editButtonRect[2]) / 2, (editButtonRect[1] + editButtonRect[3]) / 2,
            "编辑" if not editingUserData else "完成",
            font = f"{(editButtonRect[3] - editButtonRect[1]) * 0.7}px pgrFont",
            textAlign = "center",
            textBaseline = "middle",
            fillStyle = "rgb(83, 83, 83)",
            wait_execute = True
        )
        
        drawText(
            w * 0.46875, h * (805 / 1080),
            "登录以使用云存档功能",
            font = f"{(w + h) / 90}px pgrFont",
            textAlign = "center",
            textBaseline = "middle",
            fillStyle = f"rgba(255, 255, 255, {1.0 if not editingUserData else 0.75})",
            wait_execute = True
        )
        
        loginButtonRect = (
            w * 0.4171875, h * (860 / 1080),
            w * 0.5109375, h * (910 / 1080)
        )
        root.run_js_code(
            f"ctx.drawDiagonalRectangle(\
                {",".join(map(str, loginButtonRect))},\
                {utils.getDPower(loginButtonRect[2] - loginButtonRect[0], loginButtonRect[3] - loginButtonRect[1], 75)},\
                'rgba(255, 255, 255, {1.0 if not editingUserData else 0.75})'\
            );",
            wait_execute = True
        )
        
        root.run_js_code(
            f"ctx.drawDiagonalRectangleClipImage(\
                {",".join(map(str, loginButtonRect))},\
                {root.get_img_jsvarname("taptap")},\
                {((loginButtonRect[2] - loginButtonRect[0]) - TapTapIconWidth) / 2},\
                {((loginButtonRect[3] - loginButtonRect[1]) - TapTapIconHeight) / 2},\
                {TapTapIconWidth}, {TapTapIconHeight},\
                {utils.getDPower(loginButtonRect[2] - loginButtonRect[0], loginButtonRect[3] - loginButtonRect[1], 75)},\
                {1.0 if not editingUserData else 0.75}\
            );",
            wait_execute = True
        )
        
        chartDataDifRect = (
            w * 0.5015625, h * (589 / 1080),
            w * 0.5765625, h * (672 / 1080)
        )
        root.run_js_code(
            f"ctx.drawDiagonalRectangle(\
                {",".join(map(str, chartDataDifRect))},\
                {utils.getDPower(chartDataDifRect[2] - chartDataDifRect[0], chartDataDifRect[3] - chartDataDifRect[1], 75)},\
                'rgb(255, 255, 255)'\
            );",
            wait_execute = True
        )
        
        drawText(
            (chartDataDifRect[0] + chartDataDifRect[2]) / 2, (chartDataDifRect[1] + chartDataDifRect[3]) / 2,
            "IN",
            font = f"{(chartDataDifRect[3] - chartDataDifRect[1]) * 0.55}px pgrFont",
            textAlign = "center",
            textBaseline = "middle",
            fillStyle = "rgb(50, 50, 50)",
            wait_execute = True
        )
        
        chartDataRect = (
            chartDataDifRect[2] - utils.getDPower(chartDataDifRect[2] - chartDataDifRect[0], chartDataDifRect[3] - chartDataDifRect[1], 75) * (chartDataDifRect[2] - chartDataDifRect[0]) * (77 / 85),
            chartDataDifRect[1] + (chartDataDifRect[3] - chartDataDifRect[1]) * (9 / 85),
            w * 0.871875,
            chartDataDifRect[1] + (chartDataDifRect[3] - chartDataDifRect[1]) * (77 / 85),
        )
        root.run_js_code(
            f"ctx.drawDiagonalRectangle(\
                {",".join(map(str, chartDataRect))},\
                {utils.getDPower(chartDataRect[2] - chartDataRect[0], chartDataRect[3] - chartDataRect[1], 75)},\
                'rgb(0, 0, 0, 0.45)'\
            );",
            wait_execute = True
        )
        
        def _drawChartDataItem(x: float, text: str):
            root.run_js_code(
                f"ctx.save(); ctx.font = '{(w + h) / 125}px pgrFont'; SlashWidth = ctx.measureText('/').width; ctx.restore();",
                wait_execute = True
            )
            
            textHeight = h * (635 / 1080)
            
            root.run_js_code(
                f"ctx.drawTextEx(\
                    '/',\
                    {x}, {textHeight}, '{(w + h) / 125}px pgrFont',\
                    'rgb(255, 255, 255)', 'center', 'bottom'\
                );",
                wait_execute = True
            )
            
            root.run_js_code(
                f"ctx.drawTextEx(\
                    '-',\
                    {x} + SlashWidth, {textHeight}, '{(w + h) / 125}px pgrFont',\
                    'rgb(255, 255, 255)', 'left', 'bottom'\
                );",
                wait_execute = True
            )
            
            root.run_js_code(
                f"ctx.drawTextEx(\
                    '0',\
                    {x} - SlashWidth, {textHeight}, '{(w + h) / 85}px pgrFont',\
                    'rgb(255, 255, 255)', 'right', 'bottom'\
                );",
                wait_execute = True
            )
            
            drawText(
                x, h * (648 / 1080),
                text,
                font = f"{(w + h) / 180}px pgrFont",
                textAlign = "center",
                textBaseline = "middle",
                fillStyle = "rgb(255, 255, 255)",
                wait_execute = True
            )
        
        _drawChartDataItem(w * 0.621875, "Cleared")
        _drawChartDataItem(w * 0.71875, "Full Combo")
        _drawChartDataItem(w * 0.8140625, "Phi")
        
        if editingUserData:
            def _strokeRect(rect):
                root.run_js_code(
                    f"ctx.strokeRectEx(\
                        {rect[0]}, {rect[1]},\
                        {rect[2] - rect[0]}, {rect[3] - rect[1]},\
                        'rgb(255, 255, 255)', {(w + h) / 711.45141919810}\
                    );",
                    wait_execute = True
                )
                
            editUserNameRect = (
                w * 0.2328125, h * (303 / 1080),
                w * 0.44375, h * (376 / 1080)
            )
            
            editIntroductionRect = (
                w * 0.14375, h * (440 / 1080),
                w * 0.45625, h * (660 / 1080)
            )
            
            _strokeRect(editUserNameRect)
            _strokeRect(editIntroductionRect)
        
        def _drawChooseDialog(
            p: float, text: str, imgs: list[str],
            imgwidth: float, imgheight: float,
            imgx_padding: float, imgy_padding: float,
            imgsx: float, imgsy: float,
            linemax: int, dialogrectname: str
        ):
            top = h - (905 / 1080) * h * p
            
            settingShadowRect = const.PHIGROS_SETTING_SHADOW_XRECT_MAP[const.PHIGROS_SETTING_STATE.ACCOUNT_AND_COUNT]
            settingShadowDPower = utils.getDPower((settingShadowRect[1] - settingShadowRect[0]) * w, h, 75)
            settingShadowDWidth = (settingShadowRect[1] - settingShadowRect[0]) * w * settingShadowDPower
            chooseDialogLeftX = settingShadowRect[0] * w
            chooseDialogRightX = settingShadowRect[1] * w - settingShadowDWidth + settingShadowDWidth * (h - top) / h
            chooseDialogRect = tuple(map(int, (
                chooseDialogLeftX, top,
                chooseDialogRightX, h,
            )))
            
            root.run_js_code(
                f"ctx.save(); ctx.clipDiagonalRectangle(\
                    {",".join(map(str, chooseDialogRect))},\
                    {utils.getDPower(*utils.getSizeByRect(chooseDialogRect), 75)},\
                );",
                wait_execute = True
            )
            drawBackground()
            root.run_js_code("ctx.restore();", wait_execute=True)
            
            root.run_js_code(
                f"ctx.drawDiagonalRectangle(\
                    {",".join(map(str, chooseDialogRect))},\
                    {utils.getDPower(*utils.getSizeByRect(chooseDialogRect), 75)},\
                    'rgba(0, 0, 0, 0.65)'\
                );",
                wait_execute = True
            )
            
            textX = chooseDialogLeftX + settingShadowDWidth * (h - top) / h + w * 0.015625
            textY = top + h * (53 / 1080)
            drawText(
                textX, textY,
                text,
                font = f"{(w + h) / 75}px pgrFont",
                textAlign = "left",
                textBaseline = "middle",
                fillStyle = "rgb(255, 255, 255)",
                wait_execute = True
            )
            
            closeButtonCenterPoint = (
                chooseDialogRightX - w * 0.0421875,
                top + h * (50 / 1080)
            )
            closeButtonSize = (w + h) * 0.014
            drawImage(
                "close",
                closeButtonCenterPoint[0] - closeButtonSize / 2,
                closeButtonCenterPoint[1] - closeButtonSize / 2,
                closeButtonSize, closeButtonSize,
                wait_execute = True
            )
            
            scdy = settingUIChooseAvatarAndBackgroundSlideControler.getDy()
            imgsy += scdy
            imgsx -= (ShadowXRect[1] - ShadowXRect[0]) * w * ShadowDPower * scdy / h
            imgsx = imgsx + settingShadowDWidth * (h - top) / h + w * 0.015625
            imgx, imgy = imgsx, imgsy + top
            imgdp = utils.getDPower(imgwidth, imgheight, 75)
            lcount = 0
            
            clipy0, clipy1 = top + h * (100 / 1080), h
            root.run_js_code(f"ctx.save(); ctx.clipRect(0.0, {min(clipy0, clipy1)}, {w}, {max(clipy0, clipy1)});", wait_execute = True)
            
            for imgindex, img in enumerate(imgs):
                if imgy >= 0:
                    root.run_js_code(
                        f"ctx.drawDiagonalRectangleClipImageOnlyHeight(\
                            {imgx}, {imgy},\
                            {imgx + imgwidth}, {imgy + imgheight},\
                            {root.get_img_jsvarname(img)},\
                            {imgheight}, {imgdp}, 1.0\
                        );",
                        wait_execute = True
                    )
                
                if showAvatars or showBackgrounds:
                    chooseRects[dialogrectname][imgindex] = (
                        imgx, imgy,
                        imgx + imgwidth, imgy + imgheight
                    )
                
                imgx += imgwidth + imgx_padding
                lcount += 1
                if lcount >= linemax:
                    imgsx -= (ShadowXRect[1] - ShadowXRect[0]) * w * ShadowDPower * (imgheight + imgy_padding) / h
                    imgx = imgsx
                    imgy += imgheight + imgy_padding
                    lcount = 0
                
                if imgy >= h:
                    break
            
            settingUIChooseAvatarAndBackgroundSlideControler.setDx(0.0)
            settingUIChooseAvatarAndBackgroundSlideControler.maxValueY = (
                math.ceil(len(imgs) / linemax) * (imgheight + imgy_padding)
                - imgy_padding
                - (h - top)
                + (imgsy - scdy)
                + h * (91 / 1080)
            )
            
            root.run_js_code(f"ctx.restore();", wait_execute = True)
        
        avatar_imnames = [f"avatar_{i}" for i in range(len(assetConfig["avatars"]))]
        background_imnames = [f"background_{i}" for i in range(len(assetConfig["backgrounds"]))]
        
        if showAvatars:
            sa_p = utils.fixorp((time.time() - showAvatarsSt) / 1.25)
            sa_p = 1.0 - (1.0 - sa_p) ** 12
        elif not showAvatars and time.time() - showAvatarsSt <= 1.25:
            sa_p = (time.time() - showAvatarsSt) / 1.25
            sa_p = (sa_p - 1.0) ** 12
        else: sa_p = None
        
        if showBackgrounds:
            sb_p = utils.fixorp((time.time() - showBackgroundsSt) / 1.25)
            sb_p = 1.0 - (1.0 - sb_p) ** 12
        elif not showBackgrounds and time.time() - showBackgroundsSt <= 1.25:
            sb_p = (time.time() - showBackgroundsSt) / 1.25
            sb_p = (sb_p - 1.0) ** 12
        else: sb_p = None
        
        if sa_p is not None:
            _drawChooseDialog(
                sa_p, "选择头像", avatar_imnames,
                w * 0.14375, h * (185 / 1080),
                0.0, h * (38 / 1080),
                w * (32 / 1920), h * (120 / 1080),
                5, "avatars"
            )
        if sb_p is not None:
            _drawChooseDialog(
                sb_p, "选择背景", background_imnames,
                w * 0.3765625, h * (200 / 1080),
                w * -0.0078125, h * (23 / 1080),
                w * (10 / 1920), h * (120 / 1080),
                2, "backgrounds"
            )
        
        root.run_js_code(
            f"ctx.restore();",
            wait_execute = True
        )

    def drawOtherSetting(dx: float, alpha: float):
        if alpha == 0.0: return
        
        root.run_js_code(
            f"ctx.save(); ctx.translate({- dx}, 0); ctx.globalAlpha = {alpha};",
            wait_execute = True
        )

        phiIconWidth = w * 0.215625
        phiIconHeight = phiIconWidth / Resource["phigros"].width * Resource["phigros"].height
        drawImage(
            "phigros",
            w * 0.3890625 - phiIconWidth / 2,
            h * ((0.275 + 371 / 1080) / 2) - phiIconHeight / 2,
            phiIconWidth, phiIconHeight,
            wait_execute = True
        )
        
        root.run_js_code(
            f"ctx.drawLineEx(\
                {w * 0.5296875}, {h * 0.275},\
                {w * 0.5296875}, {h * (371 / 1080)},\
                {(w + h) / 2000}, 'rgb(138, 138, 138, 0.95)'\
            );",
            wait_execute = True
        )
        
        drawText(
            w * 0.5703125, h * (308 / 1080),
            f"Version: {const.PHIGROS_VERSION}",
            font = f"{(w + h) /125}px pgrFont",
            textAlign = "left",
            textBaseline = "middle",
            fillStyle = "rgb(138, 138, 138, 0.95)",
            wait_execute = True
        )
        
        drawText(
            w * 0.5703125, h * (361 / 1080),
            f"Device: {const.DEVICE}",
            font = f"{(w + h) /125}px pgrFont",
            textAlign = "left",
            textBaseline = "middle",
            fillStyle = "rgb(138, 138, 138, 0.95)",
            wait_execute = True
        )
        
        settingOtherButtonDPower = utils.getDPower(90, 50, 75)
        
        drawText(
            w * (0.0515625 + 0.0265625) + getShadowDiagonalXByY(h * 0.575),
            h * 0.575,
            "音频问题疑难解答",
            font = f"{(w + h) / 90}px pgrFont",
            textAlign = "left",
            textBaseline = "top",
            fillStyle = "rgb(255, 255, 255)",
            wait_execute = True
        )
        
        drawText(
            w * (0.0515625 + 0.0265625 + 0.4015625) + getShadowDiagonalXByY(h * 0.575),
            h * 0.575,
            "开源许可证",
            font = f"{(w + h) / 90}px pgrFont",
            textAlign = "left",
            textBaseline = "top",
            fillStyle = "rgb(255, 255, 255)",
            wait_execute = True
        )
        
        drawText(
            w * (0.0515625 + 0.0265625) + getShadowDiagonalXByY(h * 0.675),
            h * 0.675,
            "观看教学",
            font = f"{(w + h) / 90}px pgrFont",
            textAlign = "left",
            textBaseline = "top",
            fillStyle = "rgb(255, 255, 255)",
            wait_execute = True
        )
        
        drawText(
            w * (0.0515625 + 0.0265625 + 0.4015625) + getShadowDiagonalXByY(h * 0.675),
            h * 0.675,
            "隐私政策",
            font = f"{(w + h) / 90}px pgrFont",
            textAlign = "left",
            textBaseline = "top",
            fillStyle = "rgb(255, 255, 255)",
            wait_execute = True
        )
        
        drawText(
            w * (0.0515625 + 0.0265625) + getShadowDiagonalXByY(h * 0.775),
            h * 0.775,
            "关于我们",
            font = f"{(w + h) / 90}px pgrFont",
            textAlign = "left",
            textBaseline = "top",
            fillStyle = "rgb(255, 255, 255)",
            wait_execute = True
        )
        
        for i in otherSettingButtonRects:
            drawOtherSettingButton(*i, settingOtherButtonDPower)
        
        drawText(
            w * 0.803125,
            h * (1031 / 1080),
            const.OTHERSERTTING_RIGHTDOWN_TEXT,
            font = f"{(w + h) / 135}px pgrFont",
            textAlign = "right",
            textBaseline = "middle",
            fillStyle = "rgba(255, 255, 255, 0.5)",
            wait_execute = True
        )
        
        drawImage(
            "twitter",
            w * 0.0734375 - SettingUIOtherIconWidth / 2,
            h * (1031 / 1080) - SettingUIOtherDownIconHeight_Twitter / 2,
            SettingUIOtherDownIconWidth,
            SettingUIOtherDownIconHeight_Twitter,
            wait_execute = True
        )
        
        drawText(
            w * 0.0875, h * (1031 / 1080),
            const.OTHER_SETTING_LB_STRINGS.TWITTER,
            font = f"{(w + h) / 135}px pgrFont",
            textAlign = "left",
            textBaseline = "middle",
            fillStyle = "rgba(255, 255, 255, 0.5)",
            wait_execute = True
        )
        
        drawImage(
            "bilibili",
            w * 0.203125 - SettingUIOtherIconWidth / 2,
            h * (1031 / 1080) - SettingUIOtherDownIconHeight_Bilibili / 2,
            SettingUIOtherDownIconWidth,
            SettingUIOtherDownIconHeight_Bilibili,
            wait_execute = True
        )
        
        drawText(
            w * 0.2171875, h * (1031 / 1080),
            const.OTHER_SETTING_LB_STRINGS.BILIBILI,
            font = f"{(w + h) / 135}px pgrFont",
            textAlign = "left",
            textBaseline = "middle",
            fillStyle = "rgba(255, 255, 255, 0.5)",
            wait_execute = True
        )
        
        drawImage(
            "qq",
            w * 0.3328125 - SettingUIOtherIconWidth / 2 * 0.85,
            h * (1031 / 1080) - SettingUIOtherDownIconHeight_QQ / 2 * 0.85,
            SettingUIOtherDownIconWidth * 0.85,
            SettingUIOtherDownIconHeight_QQ * 0.85,
            wait_execute = True
        )
        
        drawText(
            w * 0.346875, h * (1031 / 1080),
            const.OTHER_SETTING_LB_STRINGS.QQ,
            font = f"{(w + h) / 135}px pgrFont",
            textAlign = "left",
            textBaseline = "middle",
            fillStyle = "rgba(255, 255, 255, 0.5)",
            wait_execute = True
        )
        
        drawImage(
            "github",
            w * 0.4654375 - SettingUIOtherIconWidth / 2,
            h * (1031 / 1080) - SettingUIOtherDownIconHeight_Github / 2,
            SettingUIOtherDownIconWidth,
            SettingUIOtherDownIconHeight_Github,
            wait_execute = True
        )
        
        drawText(
            w * 0.4795, h * (1031 / 1080),
            const.OTHER_SETTING_LB_STRINGS.GITHUB,
            font = f"{(w + h) / 135}px pgrFont",
            textAlign = "left",
            textBaseline = "middle",
            fillStyle = "rgba(255, 255, 255, 0.5)",
            wait_execute = True
        )
        
        root.run_js_code(
            f"ctx.restore();",
            wait_execute = True
        )
    
    SettingPlayWidgetEventManager.widgets.clear()
    PlaySettingWidgets.clear()
    PlaySettingWidgets.update({
        "OffsetLabel": phigame_obj.PhiLabel(
            left_text = "谱面延时",
            right_text = "",
            fontsize = (w + h) / 75,
            color = "#FFFFFF"
        ),
        "OffsetSlider": phigame_obj.PhiSlider(
            tonext = h * (-67 / 1080),
            value = getUserData("setting-chartOffset"),
            number_points = (
                (0.0, -400.0),
                (0.4, 0.0),
                (1.0, 600.0)
            ),
            lr_button = True,
            sliderUnit = 5.0,
            conUnit = 5.0,
            numberType = int,
            command = updateConfig
        ),
        "OffsetTip": phigame_obj.PhiLabel(
            left_text = "",
            right_text = "",
            fontsize = (w + h) / 150,
            color = "rgba(255, 255, 255, 0.6)"
        ),
        "NoteScaleLabel": phigame_obj.PhiLabel(
            left_text = "按键缩放",
            right_text = "",
            fontsize = (w + h) / 75,
            color = "#FFFFFF"
        ),
        "NoteScaleSlider": phigame_obj.PhiSlider(
            value = getUserData("setting-noteScale"),
            number_points = ((0.0, 1.0), (1.0, 1.3)),
            lr_button = False,
            command = updateConfig
        ),
        "BackgroundDimLabel": phigame_obj.PhiLabel(
            left_text = "背景亮度",
            right_text = "",
            fontsize = (w + h) / 75,
            color = "#FFFFFF"
        ),
        "BackgroundDimSlider": phigame_obj.PhiSlider(
            value = getUserData("setting-backgroundDim"),
            number_points = ((0.0, 0.05), (1.0, 0.4)),
            lr_button = False,
            command = updateConfig
        ),
        "ClickSoundCheckbox": phigame_obj.PhiCheckbox(
            text = "打开打击音效",
            fontsize = (w + h) / 75,
            checked = getUserData("setting-enableClickSound"),
            command = updateConfig
        ),
        "MusicVolumeLabel": phigame_obj.PhiLabel(
            left_text = "音乐音量",
            right_text = "",
            fontsize = (w + h) / 75,
            color = "#FFFFFF"
        ),
        "MusicVolumeSlider": phigame_obj.PhiSlider(
            value = getUserData("setting-musicVolume"),
            number_points = ((0.0, 0.0), (1.0, 1.0)),
            lr_button = False,
            command = updateConfig
        ),
        "UISoundVolumeLabel": phigame_obj.PhiLabel(
            left_text = "界面音效音量",
            right_text = "",
            fontsize = (w + h) / 75,
            color = "#FFFFFF"
        ),
        "UISoundVolumeSlider": phigame_obj.PhiSlider(
            value = getUserData("setting-uiVolume"),
            number_points = ((0.0, 0.0), (1.0, 1.0)),
            lr_button = False,
            command = updateConfig
        ),
        "ClickSoundVolumeLabel": phigame_obj.PhiLabel(
            left_text = "打击音效音量",
            right_text = "",
            fontsize = (w + h) / 75,
            color = "#FFFFFF"
        ),
        "ClickSoundVolumeSlider": phigame_obj.PhiSlider(
            value = getUserData("setting-clickSoundVolume"),
            number_points = ((0.0, 0.0), (1.0, 1.0)),
            lr_button = False,
            command = updateConfig
        ),
        "MorebetsAuxiliaryCheckbox": phigame_obj.PhiCheckbox(
            text = "开启多押辅助",
            fontsize = (w + h) / 75,
            checked = getUserData("setting-enableMorebetsAuxiliary"),
            command = updateConfig
        ),
        "FCAPIndicatorCheckbox": phigame_obj.PhiCheckbox(
            text = "开启FC/AP指示器",
            fontsize = (w + h) / 75,
            checked = getUserData("setting-enableFCAPIndicator"),
            command = updateConfig
        ),
        "LowQualityCheckbox": phigame_obj.PhiCheckbox(
            text = "低分辨率模式",
            fontsize = (w + h) / 75,
            checked = getUserData("setting-enableLowQuality"),
            command = updateConfig
        ),
        "SceneTransitionAnimationCheckbox": phigame_obj.PhiCheckbox(
            text = "开启场景过渡动画",
            fontsize = (w + h) / 75,
            checked = getUserData("setting-enableSceneTransitionAnimation"),
            command = updateConfig
        ),
        "TrigridCheckbox": phigame_obj.PhiCheckbox(
            text = "启用 Trigrid",
            fontsize = (w + h) / 75,
            checked = getUserData("setting-enableTrigrid"),
            command = updateConfig
        ),
        # "importArchiveFromPhigros": phigame_obj.PhiButton(
        #     tonext = 0,
        #     text = "从 Phigros 官方导入游戏存档",
        #     fontsize = (w + h) / 125,
        #     width = w * 0.2,
        #     command = importArchiveFromPhigros,
        #     anchor = "left"
        # ),
    })
    
    SettingPlayWidgetEventManager.widgets.clear()
    SettingPlayWidgetEventManager.widgets.extend(PlaySettingWidgets.values())
    updateConfig()
    updatebg()
    settingRenderSt = time.time()
    
    while True:
        clearCanvas(wait_execute = True)
        
        drawBackground()
        
        root.run_js_code(
            f"ctx.fillRectEx(\
                0, 0, {w}, {h},\
                'rgba(0, 0, 0, 0.5)'\
            );",
            wait_execute = True
        )
        
        ShadowXRect = settingState.getShadowRect()
        ShadowRect = (
            ShadowXRect[0] * w, 0.0,
            ShadowXRect[1] * w, h
        )
        ShadowDPower = utils.getDPower(ShadowRect[2] - ShadowRect[0], h, 75)
        
        root.run_js_code(
            f"ctx.drawDiagonalRectangle(\
                {",".join(map(str, ShadowRect))},\
                {ShadowDPower}, 'rgba(0, 0, 0, 0.2)'\
            );",
            wait_execute = True
        )
        
        BarWidth = settingState.getBarWidth() * w
        BarHeight = h * (2 / 27)
        BarDPower = utils.getDPower(BarWidth, BarHeight, 75)
        BarRect = (
            w * 0.153125, h * 0.025,
            w * 0.153125 + BarWidth, h * 0.025 + BarHeight
        )
        
        root.run_js_code(
            f"ctx.drawDiagonalRectangle(\
                {",".join(map(str, BarRect))},\
                {BarDPower}, 'rgba(0, 0, 0, 0.45)'\
            );",
            wait_execute = True
        )
        
        BarAlpha = 1.0 if not editingUserData else 0.5
        
        LabelWidth = settingState.getLabelWidth() * w
        LabelHeight = h * (113 / 1080)
        LabelDPower = utils.getDPower(LabelWidth, LabelHeight, 75)
        LabelX = settingState.getLabelX() * w
        LabelRect = (
            LabelX, h * 1 / 108,
            LabelX + LabelWidth, h * 1 / 108 + LabelHeight
        )
        
        root.run_js_code(
            f"ctx.drawDiagonalRectangle(\
                {",".join(map(str, LabelRect))},\
                {LabelDPower}, '{"rgb(255, 255, 255)" if not editingUserData else "rgb(192, 192, 192)"}'\
            );",
            wait_execute = True
        )
        
        PlayTextColor = settingState.getTextColor(const.PHIGROS_SETTING_STATE.PLAY) + (BarAlpha, )
        AccountAndCountTextColor = settingState.getTextColor(const.PHIGROS_SETTING_STATE.ACCOUNT_AND_COUNT) + (BarAlpha, )
        OtherTextColor = settingState.getTextColor(const.PHIGROS_SETTING_STATE.OTHER) + (BarAlpha, )
        PlayTextFontScale = settingState.getTextScale(const.PHIGROS_SETTING_STATE.PLAY)
        AccountAndCountTextFontScale = settingState.getTextScale(const.PHIGROS_SETTING_STATE.ACCOUNT_AND_COUNT)
        OtherTextFontScale = settingState.getTextScale(const.PHIGROS_SETTING_STATE.OTHER)
        settingTextY = h * 0.025 + BarHeight / 2
                
        drawText(
            w * 0.209375, settingTextY,
            "游玩",
            font = f"{(w + h) / 100 * PlayTextFontScale}px pgrFont",
            textAlign = "center",
            textBaseline = "middle",
            fillStyle = f"rgba{PlayTextColor}",
            wait_execute = True
        )
        
        drawText(
            w * 0.3296875, settingTextY,
            "账号与统计",
            font = f"{(w + h) / 100 * AccountAndCountTextFontScale}px pgrFont",
            textAlign = "center",
            textBaseline = "middle",
            fillStyle = f"rgba{AccountAndCountTextColor}",
            wait_execute = True
        )
        
        drawText(
            w * 0.4484375, settingTextY,
            "其他",
            font = f"{(w + h) / 100 * OtherTextFontScale}px pgrFont",
            textAlign = "center",
            textBaseline = "middle",
            fillStyle = f"rgba{OtherTextColor}",
            wait_execute = True
        )
        
        settingState.render(drawPlaySetting, drawAccountAndCountSetting, drawOtherSetting, ShadowXRect[0], w, settingDx)
        
        drawButton("ButtonLeftBlack", "Arrow_Left", (0, 0))
        
        if ShowOpenSource or CloseOpenSource:
            if CloseOpenSource:
                if time.time() - CloseOpenSourceSt >= 0.35:
                    CloseOpenSource, CloseOpenSourceSt = False, float("nan")
                    inSettingUI = True
                    root.run_js_code(f"mask.style.backdropFilter = 'blur(0px)';", wait_execute = True)
                    root.run_js_code("dialog_canvas_ctx.clear()", wait_execute = True)
            
            if ShowOpenSource:
                p = utils.fixorp((time.time() - ShowOpenSourceSt) / 0.15)
                p = 1.0 - (1.0 - p) ** 3
            else: # CloseOpenSource
                p = utils.fixorp((time.time() - CloseOpenSourceSt) / 0.35)
                p = abs(p - 1.0) ** 3
            
            if ShowOpenSource or CloseOpenSource:
                root.run_js_code("_ctxBak = ctx; ctx = dialog_canvas_ctx; dialog_canvas_ctx.clear();", wait_execute = True)
                
                root.run_js_code(f"mask.style.backdropFilter = 'blur({(w + h) / 75 * p}px)';", wait_execute = True)
                root.run_js_code(f"ctx.save(); ctx.globalAlpha = {p};", wait_execute = True)
                
                root.run_js_code(f"ctx.fillRectEx(0, 0, {w}, {h}, 'rgba(0, 0, 0, 0.5)');", wait_execute = True)
                root.run_js_code(
                    f"ctx.drawRectMultilineText(\
                        {w * 0.2}, {settingUIOpenSourceLicenseSlideControler.getDy() + h * (143 / 1080)}, {w * 0.8}, {h},\
                        {repr(const.PHI_OPENSOURCELICENSE)},\
                        'rgb(255, 255, 255)', '{(w + h) / 145}px pgrFont', {(w + h) / 145}, 1.25\
                    );",
                    wait_execute = True
                )
                drawButton("ButtonLeftBlack", "Arrow_Left", (0, 0))
                
                root.run_js_code("ctx.restore();", wait_execute = True)
                
                root.run_js_code("ctx = _ctxBak; _ctxBak = null;", wait_execute = True)
                
        if time.time() - settingRenderSt < 1.25:
            p = (time.time() - settingRenderSt) / 1.25
            root.run_js_code(
                f"ctx.fillRectEx(\
                    0, 0, {w}, {h},\
                    'rgba(0, 0, 0, {(1.0 - p) ** 2})'\
                );",
                wait_execute = True
            )
        
        if tonextUI and time.time() - tonextUISt < 0.75:
            p = (time.time() - tonextUISt) / 0.75
            root.run_js_code(
                f"ctx.fillRectEx(\
                    0, 0, {w}, {h},\
                    'rgba(0, 0, 0, {1.0 - (1.0 - p) ** 2})'\
                );",
                wait_execute = True
            )
        elif tonextUI:
            clearCanvas(wait_execute = True)
            root.run_js_wait_code()
            Thread(target=nextUI, daemon=True).start()
            break
        
        root.run_js_wait_code()
    
    inSettingUI = False
    settingState = None
    SettingPlayWidgetEventManager.widgets.clear()
    PlaySettingWidgets.clear()
    bgrespacker.unload(bgrespacker.getnames())
    
def audioQARender():
    global dspSettingWidgets
    
    audioQARenderSt = time.time()
    nextUI, tonextUI, tonextUISt = None, False, float("nan")
    clickedBackButton = False
    
    def clickBackButtonCallback(*args):
        nonlocal clickedBackButton
        nonlocal nextUI, tonextUI, tonextUISt
        
        if not clickedBackButton:
            eventManager.unregEvent(clickBackButtonEvent)
            nextUI, tonextUI, tonextUISt = settingRender, True, time.time()
            mixer.music.fadeout(500)
            Resource["UISound_4"].play()
    
    clickBackButtonEvent = phigame_obj.ClickEvent(
        rect = (0, 0, ButtonWidth, ButtonHeight),
        callback = clickBackButtonCallback,
        once = False
    )
    eventManager.regClickEvent(clickBackButtonEvent)
    
    dspSettingWidgetEventManager.widgets.clear()
    dspSettingWidgets.clear()
    dspSettingWidgets.update({
        "ValueLabel": phigame_obj.PhiLabel(
            left_text = "Audio Mixer Buffer",
            right_text = "",
            fontsize = (w + h) / 75,
            color = "#FFFFFF"
        ),
        "ValueSlider": phigame_obj.PhiSlider(
            value = getUserData("internal-dspBufferExponential"),
            number_points = [(0.0, 7.0), (1.0, 12.0)],
            lr_button = False,
            sliderUnit = 1.0,
            numberType = int,
            command = updateConfig
        ),
        "PlayButton": phigame_obj.PhiButton(
            text = "播放音频",
            fontsize = (w + h) / 75,
            width = w * 0.19375,
            command = lambda: (mixer.music.load("./resources/TouchToStart.mp3"), mixer.music.play())
        )
    })
    
    dspSettingWidgetEventManager.widgets.clear()
    dspSettingWidgetEventManager.widgets.extend(dspSettingWidgets.values())
    updateConfig()
    
    while True:
        clearCanvas(wait_execute = True)
        
        drawBackground()
        
        root.run_js_code(
            f"ctx.fillRectEx(\
                0, 0, {w}, {h},\
                'rgba(0, 0, 0, 0.5)'\
            );",
            wait_execute = True
        )
        
        shadowRect = (
            w * 0.1015625, 0.0,
            w * 0.9, h
        )
        root.run_js_code(
            f"ctx.drawDiagonalRectangle(\
                {",".join(map(str, shadowRect))},\
                {utils.getDPower(*utils.getSizeByRect(shadowRect), 75)}, 'rgba(0, 0, 0, 0.25)'\
            );",
            wait_execute = True
        )
    
        renderPhigrosWidgets(
            dspSettingWidgets.values(), w * 0.275, h * (665 / 1080), 0.0,
            lambda y: ((y - h * (665 / 1080)) / h) * (utils.getSizeByRect(shadowRect)[0] * utils.getDPower(*utils.getSizeByRect(shadowRect), 75)),
            w * 0.425, 0.0, h
        )
        
        drawText(
            w * 0.3, h * (98 / 1080),
            "音频问题疑难解答",
            font = f"{(w + h) / 62.5}px pgrFont",
            textAlign = "left",
            textBaseline = "top",
            fillStyle = "rgb(255, 255, 255)",
            wait_execute = True
        )
        
        root.run_js_code(
            f"ctx.drawRectMultilineTextDiagonal(\
                {w * 0.28125}, {h * (241 / 1080)},\
                {w * 0.7984375}, {h}, {repr(const.DSP_SETTING_TIP)},\
                'rgb(255, 255, 255)',\
                '{(w + h) / 120}px pgrFont', {(w + h) / 120}, {- w * 0.0046875}, 1.25\
            );",
            wait_execute = True
        )
        
        drawButton("ButtonLeftBlack", "Arrow_Left", (0, 0))
                
        if time.time() - audioQARenderSt < 1.25:
            p = (time.time() - audioQARenderSt) / 1.25
            root.run_js_code(
                f"ctx.fillRectEx(\
                    0, 0, {w}, {h},\
                    'rgba(0, 0, 0, {(1.0 - p) ** 2})'\
                );",
                wait_execute = True
            )
        
        if tonextUI and time.time() - tonextUISt < 0.75:
            p = (time.time() - tonextUISt) / 0.75
            root.run_js_code(
                f"ctx.fillRectEx(\
                    0, 0, {w}, {h},\
                    'rgba(0, 0, 0, {1.0 - (1.0 - p) ** 2})'\
                );",
                wait_execute = True
            )
        elif tonextUI:
            clearCanvas(wait_execute = True)
            root.run_js_wait_code()
            Thread(target=nextUI, daemon=True).start()
            break
        
        root.run_js_wait_code()
    
    dspSettingWidgetEventManager.widgets.clear()
    dspSettingWidgets.clear()

def aboutUsRender():
    aboutUsRenderSt = time.time()
    nextUI, tonextUI, tonextUISt = None, False, float("nan")
    clickedStart = False
    clickedStartButtonTime = float("nan")
    skipStart = False
    skipStartButtonTime = float("nan")
    
    def skipEventCallback(*args):
        nonlocal skipStart, skipStartButtonTime
        
        skipStart, skipStartButtonTime = True, time.time()
    
    def CancalSkipEventCallback(*args):
        nonlocal skipStart, skipStartButtonTime
        
        skipStart, skipStartButtonTime = False, float("nan")
    
    def clickStartButtonCallback(*args):
        nonlocal clickedStart, clickedStartButtonTime
        
        if not clickedStart:
            clickedStart, clickedStartButtonTime = True, time.time()
    
    skipEvent = eventManager.regClickEventFs(skipEventCallback, False)
    skipEventRelease = eventManager.regReleaseEventFs(CancalSkipEventCallback)
    clickStartButtonEvent = eventManager.regClickEventFs(clickStartButtonCallback, False)
    
    while True:
        clearCanvas(wait_execute = True)
        
        if not clickedStart or time.time() - clickedStartButtonTime <= 0.75:
            phiIconWidth = w * 0.296875
            phiIconHeight = phiIconWidth / Resource["phigros"].width * Resource["phigros"].height
            alpha = 1.0 if clickedStartButtonTime != clickedStartButtonTime else ((time.time() - clickedStartButtonTime) / 0.75 - 1.0) ** 2
            
            drawAlphaImage(
                "phigros",
                w / 2 - phiIconWidth / 2, h / 2 - phiIconHeight / 2,
                phiIconWidth, phiIconHeight,
                alpha,
                wait_execute = True
            )
            
            drawText(
                w * 0.5015625, h * (733 / 1080),
                text = "t   o   u   c   h      t   o      s   t   a   r   t",
                font = f"{(w + h) / 80 * (1.0 + (math.sin(time.time() * 1.5) + 1.1) / 35)}px pgrFont",
                textAlign = "center",
                textBaseline = "middle",
                fillStyle = f"rgba(255, 255, 255, {alpha})",
                wait_execute = True
            )
        
        if clickedStart:
            if not mixer.music.get_busy():
                mixer.music.load("./resources/AboutUs.mp3")
                mixer.music.play(-1)
            dy = h - h * ((time.time() - clickedStartButtonTime) / 12.5)
            fontsize = (w + h) / 102.5
            root.run_js_code(
                f"aboutus_textheight = ctx.drawRectMultilineTextCenter(\
                    {w * 0.05}, {dy}, {w * 0.95}, {h},\
                    {repr(const.PHI_ABOUTUSTEXT)},\
                    'rgb(255, 255, 255)', '{fontsize}px pgrFont', {fontsize}, 1.4\
                );",
                wait_execute = True
            )
        else:
            dy, fontsize = h, 0.0
            root.run_js_code(f"aboutus_textheight = {h * 2.0};", wait_execute = True)
        
        if time.time() - aboutUsRenderSt < 1.25:
            p = (time.time() - aboutUsRenderSt) / 1.25
            root.run_js_code(
                f"ctx.fillRectEx(\
                    0, 0, {w}, {h},\
                    'rgba(0, 0, 0, {(1.0 - p) ** 2})'\
                );",
                wait_execute = True
            )
        
        if (skipStart and skipStartButtonTime == skipStartButtonTime) or (tonextUI and skipStartButtonTime == skipStartButtonTime):
            p = (time.time() - skipStartButtonTime) / 1.75 if (skipStart and skipStartButtonTime == skipStartButtonTime) else (1.0 - (time.time() - tonextUISt) / 0.75)
            drawText(
                w * 0.028125, h * (50 / 1080),
                "长按以跳过",
                font = f"{(w + h) / 80}px pgrFont",
                textAlign = "left",
                textBaseline = "top",
                fillStyle = f"rgba(255, 255, 255, {p})",
                wait_execute = True
            )
        
        if tonextUI and time.time() - tonextUISt < 0.75:
            p = (time.time() - tonextUISt) / 0.75
            root.run_js_code(
                f"ctx.fillRectEx(\
                    0, 0, {w}, {h},\
                    'rgba(0, 0, 0, {1.0 - (1.0 - p) ** 2})'\
                );",
                wait_execute = True
            )
        elif tonextUI:
            clearCanvas(wait_execute = True)
            root.run_js_wait_code()
            Thread(target=nextUI, daemon=True).start()
            break
        
        if skipStart and time.time() - skipStartButtonTime > 1.75:
            eventManager.unregEvent(skipEvent)
            eventManager.unregEvent(skipEventRelease)
            eventManager.unregEvent(clickStartButtonEvent)
            nextUI, tonextUI, tonextUISt = mainRender, True, time.time()
            mixer.music.fadeout(500)
            skipStart = False
        
        root.run_js_wait_code()
        if dy + root.run_js_code("aboutus_textheight;") < - fontsize and not tonextUI:
            eventManager.unregEvent(skipEvent)
            eventManager.unregEvent(skipEventRelease)
            eventManager.unregEvent(clickStartButtonEvent)
            nextUI, tonextUI, tonextUISt = mainRender, True, time.time()
            mixer.music.fadeout(500)

def chartPlayerRender(
    chartAudio: str,
    chartImage: str,
    chartFile: str,
    startAnimation: bool,
    chart_information: dict,
    blackIn: bool = False,
    foregroundFrameRender: typing.Callable[[], typing.Any] = lambda: None,
    renderRelaser: typing.Callable[[], typing.Any] = lambda: None,
    nextUI: typing.Callable[[], typing.Any] = lambda: None,
    font_options: typing.Optional[dict] = None,
    autoplay: bool = False,
    sid: typing.Optional[str] = None,
    mirror: bool = False,
    playLoadSuccess: bool = True,
    challengeMode: bool = False,
    loadingAnimationStartP: float = 0.0,
    loadingAnimationBlackIn: bool = False,
    showSettlementAnimation: bool = True
):
    global raw_audio_length
    global show_start_time
    global note_max_width, note_max_height
    global note_max_size_half
    
    loaded_event = ThreadEvent()
    threadres_loaded = ThreadEvent()
    
    def _fgrender():
        while not loaded_event.is_set():
            foregroundFrameRender()
            root.run_js_wait_code()
    
    ud_popuper = UserDataPopuper()
    chart_obj = const.SPEC_VALS.RES_NOLOADED
    raw_audio_length = const.SPEC_VALS.RES_NOLOADED
    
    def _threadres_loader():
        global raw_audio_length
        nonlocal chart_obj
        
        chartJsonData: dict = json.loads(open(chartFile, "r", encoding="utf-8").read())
        chart_obj = phichart.load(chartJsonData)
        mixer.music.load(chartAudio)
        raw_audio_length = mixer.music.get_length()
        
        threadres_loaded.set()
    
    def _doCoreConfig():
        global coreConfig
        
        coreConfig = phicore.PhiCoreConfig(
            SETTER = lambda vn, vv: globals().update({vn: vv}),
            root = root, w = w, h = h,
            chart_information = chart_information,
            chart_obj = chart_obj,
            Resource = Resource,
            globalNoteWidth = globalNoteWidth,
            note_max_size_half = note_max_size_half,
            raw_audio_length = raw_audio_length,
            clickeffect_randomblock_roundn = 0.0,
            chart_res = {},
            cksmanager = cksmanager,
            enable_clicksound = getUserData("setting-enableClickSound"),
            noautoplay = not autoplay, showfps = "--debug" in sys.argv,
            debug = "--debug" in sys.argv,
            combotips = "COMBO" if not autoplay else "AUTOPLAY",
            clicksound_volume = getUserData("setting-clickSoundVolume"),
            musicsound_volume = getUserData("setting-musicVolume")
        )
        phicore.CoreConfigure(coreConfig)
    
    Thread(target=_fgrender, daemon=True).start()
    
    globalNoteWidth = w * const.NOTE_DEFAULTSIZE * getUserData("setting-noteScale")
    note_max_width = max(globalNoteWidth * i for i in phira_respack.globalPack.dub_fixscale.values())
    note_max_height = max(
        [
            note_max_width / Resource["Notes"]["Tap"].width * Resource["Notes"]["Tap"].height,
            note_max_width / Resource["Notes"]["Tap_dub"].width * Resource["Notes"]["Tap_dub"].height,
            note_max_width / Resource["Notes"]["Drag"].width * Resource["Notes"]["Drag"].height,
            note_max_width / Resource["Notes"]["Drag_dub"].width * Resource["Notes"]["Drag_dub"].height,
            note_max_width / Resource["Notes"]["Flick"].width * Resource["Notes"]["Flick"].height,
            note_max_width / Resource["Notes"]["Flick_dub"].width * Resource["Notes"]["Flick_dub"].height,
            note_max_width / Resource["Notes"]["Hold_Head"].width * Resource["Notes"]["Hold_Head"].height,
            note_max_width / Resource["Notes"]["Hold_Head_dub"].width * Resource["Notes"]["Hold_Head_dub"].height,
            note_max_width / Resource["Notes"]["Hold_End"].width * Resource["Notes"]["Hold_End"].height
        ]
    )
    note_max_size_half = ((note_max_width ** 2 + note_max_height ** 2) ** 0.5) / 2
    
    chart_information["BackgroundDim"] = 1.0 - getUserData("setting-backgroundDim")
    Thread(target=_threadres_loader, daemon=True).start()
    respacker = webcv.PILResPacker(root)
    
    chart_image = Image.open(chartImage)
    if chart_image.mode != "RGB":
        chart_image = chart_image.convert("RGB")
    
    background_image_blur = chart_image.filter(ImageFilter.GaussianBlur(sum(chart_image.size) / 50))
    respacker.reg_img(chart_image, "chart_image")
    respacker.reg_img(background_image_blur, "background_blur")
    respacker.load(*respacker.pack())
    
    cksmanager = phicore.ClickSoundManager(Resource["Note_Click_Audio"])
    loaded_event.set()
    
    _doCoreConfig()
    phicore.enableMirror = mirror
    phicore.enableWatermark = False
    phicore.FCAPIndicator = getUserData("setting-enableFCAPIndicator")
    if startAnimation:
        if playLoadSuccess:
            LoadSuccess.play()
        phicore.loadingAnimation(False, foregroundFrameRender, font_options, loadingAnimationStartP, loadingAnimationBlackIn)
        threadres_loaded.wait()
        phicore.lineOpenAnimation()
    else:
        threadres_loaded.wait()
        
    renderRelaser()
    
    if phicore.noautoplay:
        pplm_proxy = phichart.PPLMProxy_CommonChart(chart_obj)
        
        pppsm = utils.PhigrosPlayManager(chart_obj.note_num)
        pplm = utils.PhigrosPlayLogicManager(
            pplm_proxy, pppsm,
            getUserData("setting-enableClickSound"),
            lambda ts: Resource["Note_Click_Audio"][ts].play(),
            globalNoteWidth * const.MPBJUDGE_RANGE_X,
            w, h,
            challengeMode
        )
        
        convertTime2Chart = lambda t: (t - globals().get("show_start_time", time.time())) - chart_obj.offset
        root.jsapi.set_attr("PhigrosPlay_KeyDown", lambda key: pplm.pc_click(convertTime2Chart(time.time()), key)) # 这里没写diswebview的判断, 希望别埋坑..
        root.jsapi.set_attr("PhigrosPlay_KeyUp", lambda key: pplm.pc_release(convertTime2Chart(time.time()), key))
        root.jsapi.set_attr("PhigrosPlay_TouchStart", lambda x, y, i: pplm.mob_touchstart(convertTime2Chart(time.time()), x / w, y / h, i))
        root.jsapi.set_attr("PhigrosPlay_TouchMove", lambda x, y, i: pplm.mob_touchmove(convertTime2Chart(time.time()), x / w, y / h, i))
        root.jsapi.set_attr("PhigrosPlay_TouchEnd", lambda i: pplm.mob_touchend(i))
            
        pplm.bind_events(root)
    else:
        pplm = None
    
    finishPlay = False
    show_start_time = time.time()
    _doCoreConfig()
    
    def space():
        nonlocal paused, pauseAnimationSt, pauseSt
        
        if not ((time.time() - chartPlayerRenderSt) > 1.25 and pauseP == 1.0):
            return
        
        if not paused:
            paused, pauseAnimationSt = True, time.time()
            mixer.music.pause()
            Resource["Pause"].play()
            pauseSt = time.time()
        else:
            paused, pauseAnimationSt = False, time.time()
    
    def clickEventCallback(x, y):
        global show_start_time
        nonlocal nextUI, tonextUI, tonextUISt
        nonlocal needSetPlayData
        
        if rendingAnimationSt != rendingAnimationSt: # nan, playing chart
            if not paused and utils.inrect(x, y, (
                w * 9.6 / 1920, h * -1.0 / 1080,
                w * 96 / 1920, h * 102.6 / 1080
            )):
                space()
            
            pauseUIButtonR = (w + h) * 0.0275
            if paused and utils.inrect(x, y, (
                w * 0.5 - w * 0.1109375 - pauseUIButtonR / 2,
                h * 0.5 - pauseUIButtonR / 2,
                w * 0.5 - w * 0.1109375 + pauseUIButtonR / 2,
                h * 0.5 + pauseUIButtonR / 2
            )):
                eventManager.unregEvent(clickEvent)
                tonextUI, tonextUISt = True, time.time()
                Resource["UISound_4"].play()
                
            elif paused and utils.inrect(x, y, (
                w * 0.5 - pauseUIButtonR / 2,
                h * 0.5 - pauseUIButtonR / 2,
                w * 0.5 + pauseUIButtonR / 2,
                h * 0.5 + pauseUIButtonR / 2
            )) and not challengeMode:
                eventManager.unregEvent(clickEvent)
                nextUIBak = nextUI
                nextUI, tonextUI, tonextUISt = lambda: chartPlayerRender(
                    chartAudio = chartAudio,
                    chartImage = chartImage,
                    chartFile = chartFile,
                    startAnimation = False,
                    chart_information = chart_information,
                    blackIn = True,
                    nextUI = nextUIBak,
                    autoplay = autoplay,
                    sid = sid,
                    mirror = mirror,
                    loadingAnimationStartP = loadingAnimationStartP
                ), True, time.time()
                
            elif paused and utils.inrect(x, y, (
                w * 0.5 + w * 0.1109375 - pauseUIButtonR / 2,
                h * 0.5 - pauseUIButtonR / 2,
                w * 0.5 + w * 0.1109375 + pauseUIButtonR / 2,
                h * 0.5 + pauseUIButtonR / 2
            )):
                space()
                
        if rendingAnimation is not phicore.settlementAnimationFrame or (time.time() - rendingAnimationSt) <= 0.5:
            return
        
        if utils.inrect(x, y, (
            0, 0,
            w * const.FINISH_UI_BUTTON_SIZE, w * const.FINISH_UI_BUTTON_SIZE / 190 * 145
        )):
            needSetPlayData = True
            eventManager.unregEvent(clickEvent)
            nextUIBak = nextUI
            nextUI, tonextUI, tonextUISt = lambda: chartPlayerRender(
                chartAudio = chartAudio,
                chartImage = chartImage,
                chartFile = chartFile,
                startAnimation = False,
                chart_information = chart_information,
                blackIn = True,
                nextUI = nextUIBak,
                autoplay = autoplay,
                sid = sid,
                mirror = mirror
            ), True, time.time()
            
        elif utils.inrect(x, y, (
            w - w * const.FINISH_UI_BUTTON_SIZE, h - w * const.FINISH_UI_BUTTON_SIZE / 190 * 145,
            w, h
        )):
            needSetPlayData = True
            eventManager.unregEvent(clickEvent)
            tonextUI, tonextUISt = True, time.time()
        
        if utils.inrect(x, y, avatar_rect):
            ud_popuper.change()
    
    clickEvent = eventManager.regClickEventFs(clickEventCallback, False)
    root.jsapi.set_attr("SpaceClicked", space)
    root.run_js_code("_SpaceClicked = (e) => {if (e.key == ' ' && !e.repeat) pywebview.api.call_attr('SpaceClicked');};")
    root.run_js_code("window.addEventListener('keydown', _SpaceClicked);")
    
    # 前面初始化时间太长了, 放这里
    needSetPlayData = False
    avatar_rect = const.EMPTY_RECT
    chartPlayerRenderSt = time.time()
    nextUI, tonextUI, tonextUISt = nextUI, False, float("nan")
    rendingAnimation = phicore.lineCloseAimationFrame
    rendingAnimationSt = float("nan")
    stoped = False
    paused, pauseAnimationSt, pauseSt = False, 0.0, float("nan")
    mixer.music.play()
    
    while True:
        pauseATime = 0.25 if paused else 3.0
        pauseP = utils.fixorp((time.time() - pauseAnimationSt) / pauseATime)
        pauseBgBlurP = (1.0 - (1.0 - pauseP) ** 4) if paused else 1.0 - pauseP ** 15
        root.run_js_code(f"mask.style.backdropFilter = 'blur({(w + h) / 100 * pauseBgBlurP}px)';", wait_execute = True)
        
        def _renderPauseUIButtons(p: float, dx: float):
            def _drawPauseButton(x: float, imname: str, scale: float, alpha: float = 1.0):
                ims = (w + h) * 0.0275
                setCtx("dialog_canvas_ctx")
                drawAlphaImage(
                    imname,
                    x - ims / 2, h / 2 - ims / 2,
                    ims * scale, ims * scale,
                    (1.0 - (1.0 - p) ** 2) * alpha,
                    wait_execute = True
                )
                setCtx("ctx")
            _drawPauseButton(w * 0.5 - w * 0.1109375 + dx, "PUIBack", 1.0)
            _drawPauseButton(w * 0.5 + dx, "PUIRetry", 1.0, 1.0 if not challengeMode else 0.5)
            _drawPauseButton(w * 0.5 + w * 0.1109375 + dx, "PUIResume", 0.95)
            
        root.run_js_code(f"dialog_canvas_ctx.clear();", wait_execute = True)
        if paused:
            _renderPauseUIButtons(pauseP, 0.0)
        else:
            pauseUIDrawPLP = 0.2 / 3.0
            if pauseP <= pauseUIDrawPLP:
                puiBsP = pauseP / pauseUIDrawPLP
                _renderPauseUIButtons(1.0 - puiBsP, - w / 15 * (puiBsP ** 4))
            fastEaseX = 3.75
            fastEase = lambda x: rpe_easing.ease_funcs[19](x * fastEaseX) if x <= 1 / fastEaseX else 1.0
            numberEase = lambda x: int(x) + fastEase(x % 1.0)
            root.run_js_code("_ctxBak = ctx; ctx = dialog_canvas_ctx;", wait_execute = True)
            def _drawNumber(number: str, dxv: float):
                if pauseP == 1.0: return
                x = w / 2 - w * 0.1109375 * dxv
                alpha = ((w / 2 - abs(w / 2 - x)) / (w / 2)) ** 25
                if pauseP >= 0.8:
                    alpha *= 1.0 - (1.0 - (1.0 - (pauseP - 0.8) / 0.2) ** 2)
                drawText(
                    x, h / 2,
                    number,
                    font = f"{(w + h) / 30}px pgrFont",
                    textAlign = "center",
                    textBaseline = "middle",
                    fillStyle = f"rgba(255, 255, 255, {alpha})",
                    wait_execute=True
                )
            _drawNumber("3", numberEase(pauseP * 3.0) - 1.0)
            _drawNumber("2", numberEase(pauseP * 3.0) - 2.0)
            _drawNumber("1", numberEase(pauseP * 3.0) - 3.0)
            root.run_js_code("ctx = _ctxBak; _ctxBak = null;", wait_execute = True)
        
        if not paused and pauseP == 1.0 and pauseSt == pauseSt and not mixer.music.get_busy():
            mixer.music.unpause()
            show_start_time += time.time() - pauseSt
            phicore.CoreConfigure(coreConfig)
            pauseSt = float("nan")
        
        if not paused and pauseP == 1.0:
            clearCanvas(wait_execute = True)
        
            if not stoped:
                now_t = time.time() - show_start_time
                checkOffset(now_t)
                extasks = phicore.renderChart_Common(now_t, False, False, pplm)
                break_flag = phicore.processExTask(extasks)
                
                if break_flag and not stoped:
                    finishPlay = True
                    
                    if not showSettlementAnimation:
                        if not tonextUI:
                            tonextUI, tonextUISt = True, time.time()
                    else:
                        phicore.settlementAnimationUserData.userName = getUserData("userdata-userName")
                        phicore.settlementAnimationUserData.rankingScore = getUserData("userdata-rankingScore")
                        phicore.settlementAnimationUserData.hasChallengeMode = getPlayDataItem("hasChallengeMode")
                        phicore.settlementAnimationUserData.challengeModeRank = getPlayDataItem("challengeModeRank")
                        
                        phicore.initSettlementAnimation(pplm, utils.gtpresp(getUserData("userdata-userAvatar")))
                        rendingAnimationSt = time.time()
                        stoped = True
            else:
                if rendingAnimation is phicore.lineCloseAimationFrame:
                    if time.time() - rendingAnimationSt <= 0.75:
                        rendingAnimation((time.time() - rendingAnimationSt) / 0.75, pplm.ppps.getCombo() if phicore.noautoplay else phicore.chart_obj.note_num, False)
                    else:
                        rendingAnimation, rendingAnimationSt = phicore.settlementAnimationFrame, time.time()
                        mixer.music.load("./resources/Over.mp3")
                        Thread(target=lambda: (time.sleep(0.25), mixer.music.play(-1)), daemon=True).start()
                
                if rendingAnimation is phicore.settlementAnimationFrame: # 不能用elif, 不然会少渲染一个帧
                    avatar_rect = rendingAnimation(
                        utils.fixorp((time.time() - rendingAnimationSt) / 3.5), False,
                        ud_popuper.isPopup, ud_popuper.p
                    )
        
        if time.time() - chartPlayerRenderSt < 1.25 and blackIn:
            p = (time.time() - chartPlayerRenderSt) / 1.25
            root.run_js_code(
                f"ctx.fillRectEx(\
                    0, 0, {w}, {h},\
                    'rgba(0, 0, 0, {(1.0 - p) ** 2})'\
                );",
                wait_execute = True
            )
        
        if tonextUI and time.time() - tonextUISt < 0.75:
            p = (time.time() - tonextUISt) / 0.75
            if not paused:
                root.run_js_code(
                    f"ctx.fillRectEx(\
                        0, 0, {w}, {h},\
                        'rgba(0, 0, 0, {1.0 - (1.0 - p) ** 2})'\
                    );",
                    wait_execute = True
                )
            else:
                root.run_js_code("_ctxBak = ctx; ctx = dialog_canvas_ctx;", wait_execute = True)
                root.run_js_code(
                    f"ctx.fillRectEx(\
                        0, 0, {w}, {h},\
                        'rgba(0, 0, 0, {1.0 - (1.0 - p) ** 2})'\
                    );",
                    wait_execute = True
                )
                root.run_js_code("ctx = _ctxBak; _ctxBak = null;", wait_execute = True)
        elif tonextUI:
            mixer.music.stop()
            clearCanvas(wait_execute = True)
            root.run_js_code(f"dialog_canvas_ctx.clear()", wait_execute = True)
            root.run_js_code(f"mask.style.backdropFilter = 'blur(0px)';", wait_execute = True)
            root.run_js_wait_code()
            
            if sid is not None and pplm is not None and needSetPlayData:
                setPlayData(
                    sid,
                    score = pplm.ppps.getScore(),
                    acc = pplm.ppps.getAcc(),
                    level = pplm.ppps.getLevelString()
                )
            
            mixer.music.set_volume(1.0)
            Thread(target=nextUI, daemon=True).start()
            break
        
        root.run_js_wait_code()
    
    if phicore.noautoplay:
        pplm.unbind_events(root)
        
    root.run_js_code("window.removeEventListener('keydown', _SpaceClicked);")
    phicore.initGlobalSettings()
    cksmanager.stop()
    respacker.unload(respacker.getnames())
    
    return pplm, finishPlay

def chooseChartRender(chapter_item: phigame_obj.Chapter, isChallengeMode: bool = False):
    illrespacker = webcv.LazyPILResPacker(root)
    for song in chapter_item.songs:
        illrespacker.reg_img(utils.gtpresp(song.image_lowres), f"songill_{song.songId}")
        illrespacker.reg_img(utils.gtpresp(song.image), f"songill_{song.songId}")
    
    avatar_img = Image.open(utils.gtpresp(getUserData("userdata-userAvatar")))
    illrespacker.reg_img(avatar_img, "user_avatar")
    illrespacker.load(*illrespacker.pack())
    
    chooseState = phigame_obj.ChartChooseUI_State(Resource["UISound_2"])
    chooseControler = phigame_obj.ChooseChartControler(chapter_item, w, h, Resource["UISound_5"], chooseState)
    eventManager.regClickEventFs(chooseControler.scter_mousedown, False)
    eventManager.regReleaseEvent(phigame_obj.ReleaseEvent(chooseControler.scter_mouseup))
    eventManager.regMoveEvent(phigame_obj.MoveEvent(chooseControler.scter_mousemove))
    
    resort = lambda: None
    chooseState.change_diff_callback = lambda: (chooseControler.set_level_callback(), resort(), setUserData("internal-lastDiffIndex", chooseState.diff_index), saveUserData(userData))
    startButtonAlpha = phigame_obj.valueTransformer(rpe_easing.ease_funcs[0])
    startButtonAlpha.target = 1.0 if not isChallengeMode else 0.5
    
    chooseChartRenderSt = time.time()
    nextUI, tonextUI, tonextUISt = None, False, float("nan")
    clickedBackButton = False
    immediatelyExitRender = False
    
    ud_popuper = UserDataPopuper()
    userNameConstFontSize = (w + h) / const.USERNAME_CONST_FONT
    userNamePadding = w * 0.01
    userNameWidth = root.run_js_code(f"ctx.getTextSize({repr(getUserData("userdata-userName"))}, '{userNameConstFontSize}px pgrFont')[0];") + userNamePadding * 2
    
    def unregEvents():
        eventManager.unregEvent(clickBackButtonEvent)
        eventManager.unregEvent(clickEvent)
        chooseControler.__del__()
        chooseControler.mixer.music.fadeout(500)
    
    def clickBackButtonCallback(*args):
        nonlocal clickedBackButton
        nonlocal nextUI, tonextUI, tonextUISt
        
        if not clickedBackButton:
            unregEvents()
            nextUI, tonextUI, tonextUISt = mainRender, True, time.time()
            mixer.music.fadeout(500)
            Resource["UISound_4"].play()
    
    clickBackButtonEvent = phigame_obj.ClickEvent(
        rect = (0, 0, ButtonWidth, ButtonHeight),
        callback = clickBackButtonCallback,
        once = False
    )
    eventManager.regClickEvent(clickBackButtonEvent)
    
    def drawParallax(x0: float, y0: float, x1: float, y1: float, full: bool = False):
        dpower = utils.getDPower(*utils.getSizeByRect((x0, y0, x1, y1)), 75)
        
        if full:
            x0 -= dpower * (x1 - x0)
            x1 += dpower * (x1 - x0)
            return drawParallax(x0, y0, x1, y1)
        
        for i in range(max(0, chooseControler.vaildNowCeil - 5), min(len(chapter_item.scsd_songs) - 1, chooseControler.vaildNowCeil + 5) + 1):
            root.run_js_code(f"{root.get_img_jsvarname(f"songill_{chapter_item.scsd_songs[i].songId}")}.lazy_load();", wait_execute=True)
        
        thisSong = chapter_item.scsd_songs[chooseControler.vaildNowCeil]
        nextSong = chapter_item.scsd_songs[chooseControler.vaildNowNextCeil]
        
        clipY = y1 - (chooseControler.vaildNowFloatIndex % 1) * (y1 - y0)
        
        ctxSave(wait_execute=True)
        ctxBeginPath(wait_execute=True)
        ctxRect(0, 0, w, clipY, wait_execute=True)
        ctxClip(wait_execute=True)
        parallaxN = 1.5
        thisSongDy = (clipY - y0) / parallaxN - (y1 - y0) / parallaxN
        thisSongDx = (x1 - x0) * dpower * (-thisSongDy / (y1 - y0))
        
        root.run_js_code(f"ctx.drawImageDx = {thisSongDx}; ctx.drawImageDy = {thisSongDy};", wait_execute=True)
        root.run_js_code(
            f"ctx.drawDiagonalRectangleClipImageOnlyHeight(\
                {",".join(map(str, (x0, y0, x1, y1)))},\
                {root.get_img_jsvarname(f"songill_{thisSong.songId}")},\
                {y1 - y0}, {dpower}, 1.0\
            );",
            wait_execute = True
        )
        root.run_js_code("ctx.drawImageDx = 0; ctx.drawImageDy = 0;", wait_execute=True)
        ctxRestore(wait_execute=True)
        
        ctxSave(wait_execute=True)
        ctxBeginPath(wait_execute=True)
        ctxRect(0, clipY, w, h, wait_execute=True)
        ctxClip(wait_execute=True)
        nextSongDy = (clipY - y0)
        nextSongDx = (x1 - x0) * dpower * (-nextSongDy / (y1 - y0))
        
        root.run_js_code(f"ctx.drawImageDx = {nextSongDx}; ctx.drawImageDy = {nextSongDy};", wait_execute=True)
        root.run_js_code(
            f"ctx.drawDiagonalRectangleClipImageOnlyHeight(\
                {",".join(map(str, (x0, y0, x1, y1)))},\
                {root.get_img_jsvarname(f"songill_{nextSong.songId}")},\
                {y1 - y0}, {dpower}, 1.0\
            );",
            wait_execute = True
        )
        root.run_js_code("ctx.drawImageDx = 0; ctx.drawImageDy = 0;", wait_execute=True)
        ctxRestore(wait_execute=True)
            
    def drawSongItems():
        nonlocal selectButtonRect
        nonlocal undoAreaRect
        
        ctxSave(wait_execute=True)
        ctxBeginPath(wait_execute=True)
        ctxRect(0, 0, w, h, wait_execute=True)
        ctxRect(*utils.xxyy_rect2_xywh(songShadowRect), wait_execute=True)
        ctxClip("evenodd", wait_execute=True)
        
        startDy = h * (434 / 1080) + chooseControler.itemNowDy * chooseControler.itemHeight
        nowDy = 0.0
        songIndex = 0
        chartsShadowWidth = utils.getSizeByRect(chartsShadowRect)[0]
        cuttedWidth = chartsShadowWidth * (1.0 - chartsShadowDPower)
        
        while (y := startDy + nowDy) < h + chooseControler.itemHeight:
            if songIndex > len(chapter_item.scsd_songs) - 1:
                break
            
            if y < -chooseControler.itemHeight:
                songIndex += 1
                nowDy += chooseControler.itemHeight
                continue
            
            x = w * -0.009375 + chartsShadowWidth * chartsShadowDPower * (1.0 - y / h)
            song = chapter_item.scsd_songs[songIndex]
            
            if math.isnan(song.chooseSongs_nameFontSize):
                phicore.root = root
                song.chooseSongs_nameFontSize = phicore.getFontSize(song.name, cuttedWidth * 0.6, (w + h) / 80, "pgrFont")
            
            drawText(
                x + w * 0.025, y,
                song.name,
                font = f"{song.chooseSongs_nameFontSize}px pgrFont",
                textAlign = "left",
                textBaseline = "middle",
                fillStyle = "white",
                wait_execute = True
            )
            
            if chooseState.diff_index <= len(song.difficulty) - 1:
                drawText(
                    x + cuttedWidth - w * 0.027625, y,
                    song.difficulty[chooseState.diff_index].strdiffnum,
                    font = f"{(w + h) / 57}px pgrFontThin",
                    textAlign = "right",
                    textBaseline = "middle",
                    fillStyle = "white",
                    wait_execute = True
                )
        
                sid = song.difficulty[chooseState.diff_index].unqique_id()
                diifpd = findPlayDataBySid(sid)
                levelimgname = diifpd["level"] if diifpd["level"] != "never_play" else "NEW"
                levelimg = Resource["levels"][levelimgname]
                levelimg_w = w * 0.05875 * 0.65
                levelimg_h = levelimg_w * levelimg.height / levelimg.width
                
                if levelimgname != "NEW":
                    drawImage(
                        f"Level_{levelimgname}",
                        x + cuttedWidth - w * 0.09375 - levelimg_w / 2,
                        y - levelimg_h / 2,
                        levelimg_w, levelimg_h,
                        wait_execute = True
                    )
            
            songIndex += 1
            nowDy += chooseControler.itemHeight
        
        ctxRestore(wait_execute=True)
        
        currectSong = chapter_item.scsd_songs[chooseControler.vaildNowIndex]
        drawText(
            w * 0.1, h * (415 / 1080),
            currectSong.name,
            font = f"{currectSong.chooseSongs_nameFontSize}px pgrFont",
            textAlign = "left",
            textBaseline = "middle",
            fillStyle = "white",
            wait_execute = True
        )
        
        if math.isnan(currectSong.currSong_composerFontSize):
            phicore.root = root
            currectSong.currSong_composerFontSize = phicore.getFontSize(currectSong.composer, cuttedWidth * 0.6, (w + h) / 80, "pgrFont") * 0.75
        
        drawText(
            w * 0.1, h * (470 / 1080),
            currectSong.composer,
            font = f"{currectSong.currSong_composerFontSize}px pgrFont",
            textAlign = "left",
            textBaseline = "middle",
            fillStyle = "white",
            wait_execute = True
        )

        previewParallaxRect = (
            w * 0.4375, h * (219 / 1080),
            w * 0.9453125, h * (733 / 1080)
        )
        previewParallaxRectWidth, previewParallaxRectHeight = utils.getSizeByRect(previewParallaxRect)
        previewParallaxRectDPower = utils.getDPower(*utils.getSizeByRect(previewParallaxRect), 75)
        drawParallax(*previewParallaxRect)
        
        if chooseState.is_mirror:
            mirrorIconLeft = (
                previewParallaxRect[0] + 
                previewParallaxRectWidth * previewParallaxRectDPower
            ) - const.MIRROR_ICON_LEFT * MirrorIconWidth
            
            drawImage(
                "mirror",
                mirrorIconLeft, previewParallaxRect[1],
                MirrorIconWidth, MirrorIconHeight,
                wait_execute = True
            )

        level_bar_right = w * chooseControler.level_bar_rightx.value
        level_bar_rect = (
            w * 0.41875, h * (779 / 1080),
            level_bar_right, h * (857 / 1080)
        )
        level_bar_dpower = utils.getDPower(*utils.getSizeByRect(level_bar_rect), 75)
        
        with utils.shadowDrawer("rgba(0, 0, 0, 0.5)", (w + h) / 125):
            root.run_js_code(
                f"ctx.drawDiagonalRectangle(\
                    {",".join(map(str, level_bar_rect))},\
                    {level_bar_dpower},\
                    'rgb(255, 255, 255)'\
                );",
                wait_execute = True
            )
        
        level_choose_block_left = w * chooseControler.level_choose_x.value
        level_choose_block_rect = (
            level_choose_block_left, h * (775 / 1080),
            level_choose_block_left + w * const.LEVEL_CHOOSE_BLOCK_WIDTH, h * (861 / 1080)
        )
        
        now_choosediffnum = str(int(chooseControler.level_diffnumber.value))
        level_choose_block_center = utils.getCenterPointByRect(level_choose_block_rect)
        
        def drawChooseBarDiff(x: float, diffnum: str, diffname: str, color: str):
            drawText(
                x,
                level_choose_block_center[1] - utils.getSizeByRect(level_choose_block_rect)[1] * (3 / 14) / 2,
                diffnum,
                font = f"{(w + h) / 85}px pgrFont",
                textAlign = "center",
                textBaseline = "middle",
                fillStyle = color,
                wait_execute = True
            )
            
            drawText(
                x,
                level_choose_block_center[1] + utils.getSizeByRect(level_choose_block_rect)[1] * (17 / 43) / 2,
                diffname,
                font = f"{(w + h) / 157.4}px pgrFont",
                textAlign = "center",
                textBaseline = "middle",
                fillStyle = color,
                wait_execute = True
            )
        
        ctxSave(wait_execute=True)
        root.run_js_code(f"ctx.clipDiagonalRectangle({",".join(map(str, level_bar_rect))}, {level_bar_dpower});", wait_execute=True)
        for i in range(len(currectSong.difficulty)):
            diff = currectSong.difficulty[i]
            drawChooseBarDiff(
                w * chooseControler.chooselevel_textsx[i].value,
                diff.strdiffnum,
                diff.name,
                "rgb(0, 0, 0)"
            )
        ctxRestore(wait_execute=True)
            
        with utils.shadowDrawer("rgba(0, 0, 0, 0.25)", (w + h) / 135):
            root.run_js_code(
                f"ctx.drawDiagonalRectangle(\
                    {",".join(map(str, level_choose_block_rect))},\
                    {utils.getDPower(*utils.getSizeByRect(level_choose_block_rect), 75)},\
                    'rgb{chooseControler.get_level_color()}'\
                );",
                wait_execute = True
            )
        
        drawChooseBarDiff(
            level_choose_block_center[0],
            now_choosediffnum,
            currectSong.difficulty[min(chooseState.diff_index, len(currectSong.difficulty) - 1)].name,
            "rgb(255, 255, 255)"
        )
        
        if isChallengeMode:
            selectButtonLeftX = diffchoosebarRect[2] - w * 0.1125
            selectPadding = (w * 0.0046875, h * (3 / 1080))
            selectButtonRect = (
                selectButtonLeftX - selectPadding[0],
                diffchoosebarRect[1] - selectPadding[1],
                diffchoosebarRect[2] - selectPadding[0],
                diffchoosebarRect[3] + selectPadding[1]
            )
            
            root.run_js_code(
                f"ctx.drawDiagonalRectangle(\
                    {",".join(map(str, selectButtonRect))},\
                    {utils.getDPower(*utils.getSizeByRect(selectButtonRect), 75)},\
                    'rgba(255, 255, 255, {chooseControler.challengeModeSelectButtonAlpha.value})'\
                );",
                wait_execute = True
            )
            
            selectButtonCenter = utils.getCenterPointByRect(selectButtonRect)
            
            drawText(
                *selectButtonCenter,
                "Select",
                font = f"{(w + h) / 95}px pgrFont",
                textAlign = "center",
                textBaseline = "middle",
                fillStyle = f"rgba(0, 0, 0, {chooseControler.challengeModeSelectTextAlpha.value})",
                wait_execute = True
            )
            
            drawAlphaImage(
                "challengeModeChecked",
                selectButtonCenter[0] - challengeModeCheckedWidth / 2,
                selectButtonCenter[1] - challengeModeCheckedHeight / 2,
                challengeModeCheckedWidth, challengeModeCheckedHeight,
                1.0 - chooseControler.challengeModeSelectTextAlpha.value,
                wait_execute = True
            )
            
            getx_fromy = lambda y: previewParallaxRect[0] + (1.0 - (y - previewParallaxRect[1]) / (previewParallaxRect[3] - previewParallaxRect[1])) * previewParallaxRectWidth * previewParallaxRectDPower
            undoArea_y0 = previewParallaxRect[1] + previewParallaxRectHeight * (250 / 380)
            undoArea_y1 = previewParallaxRect[1] + previewParallaxRectHeight * ((250 + 95) / 380)
            undoArea_x0 = getx_fromy(undoArea_y1)
            undoArea_x1 = getx_fromy(undoArea_y0) + w * 0.0578125
            undoAreaRect = (
                undoArea_x0, undoArea_y0,
                undoArea_x1, undoArea_y1
            )
            undoAreaDPower = utils.getDPower(*utils.getSizeByRect(undoAreaRect), 75)
            undoAreaCenter = utils.getCenterPointByRect(undoAreaRect)
            
            root.run_js_code(
                f"ctx.drawDiagonalRectangle(\
                    {",".join(map(str, undoAreaRect))},\
                    {undoAreaDPower},\
                    'rgba(0, 0, 0, 0.525)'\
                );",
                wait_execute = True
            )
            
            drawImage(
                "Undo",
                undoAreaCenter[0] - UndoIconWidth / 2 + w * 0.0016875,
                undoAreaCenter[1] - UndoIconHeight / 2 - (undoAreaRect[3] - undoAreaRect[1]) / 8,
                UndoIconWidth, UndoIconHeight,
                wait_execute = True
            )
            
            drawText(
                undoAreaCenter[0] - w * 0.0016875 * 1.4,
                undoAreaCenter[1] + (undoAreaRect[3] - undoAreaRect[1]) / 4.5,
                "UNDO",
                font = f"{(w + h) / 125}px pgrFont",
                textAlign = "center",
                textBaseline = "middle",
                fillStyle = "white",
                wait_execute = True
            )
            
            selection_illu_pady = h * (10 / 1080)
            selection_illu_y0 = undoAreaRect[1] - selection_illu_pady
            selection_illu_y1 = undoAreaRect[3] + selection_illu_pady
            undoarea_smallwidth = (undoAreaRect[2] - undoAreaRect[0]) * (1.0 - undoAreaDPower)
            selection_illu_allwidth = previewParallaxRectWidth * (1.0 - previewParallaxRectDPower) - undoarea_smallwidth
            selection_illu_item_smallwidth = selection_illu_allwidth / 3
            selection_illu_item_dpower_width = (selection_illu_y1 - selection_illu_y0) / math.tan(math.radians(75))
            selection_illu_item_full_width = selection_illu_item_smallwidth + selection_illu_item_dpower_width
            selection_illu_start_x = getx_fromy(selection_illu_y1) + undoarea_smallwidth
            selection_illu_now_dx = 0
            
            for i in range(3):
                this_illu_rect = (
                    selection_illu_start_x + selection_illu_now_dx,
                    selection_illu_y0,
                    selection_illu_start_x + selection_illu_now_dx + selection_illu_item_full_width + 1,
                    selection_illu_y1
                )
                this_illu_rect_size = utils.getSizeByRect(this_illu_rect)
                this_illu_rect_dpower = utils.getDPower(*this_illu_rect_size, 75)
                
                try:
                    song, diff = chooseControler.challengeModeSelections[i]
                    root.run_js_code(
                        f"ctx.drawDiagonalRectangleClipImageOnlyHeight(\
                            {",".join(map(str, this_illu_rect))},\
                            {root.get_img_jsvarname(f"songill_{song.songId}")},\
                            {this_illu_rect_size[1]}, {this_illu_rect_dpower}, 1.0\
                        );",
                        wait_execute = True
                    )
                    
                    challmode_diff_y0 = this_illu_rect[1] + this_illu_rect_size[1] * (80 / 110)
                    challmode_diff_y1 = this_illu_rect[3]
                    challmode_diff_x1 = this_illu_rect[2] - (challmode_diff_y0 - this_illu_rect[1]) / this_illu_rect_size[1] * this_illu_rect_size[0] * this_illu_rect_dpower
                    challmode_diff_x0 = challmode_diff_x1 - this_illu_rect_size[0] * (58 / 200)
                    challmode_diff_rect = (
                        challmode_diff_x0, challmode_diff_y0,
                        challmode_diff_x1, challmode_diff_y1
                    )
                    challmode_diff_rect_color = const.LEVEL_COLOR_MAP[song.difficulty.index(diff)]
                    
                    root.run_js_code(
                        f"ctx.drawDiagonalRectangle(\
                            {",".join(map(str, challmode_diff_rect))},\
                            {utils.getDPower(*utils.getSizeByRect(challmode_diff_rect), 75)},\
                            'rgb{challmode_diff_rect_color}'\
                        );",
                        wait_execute = True
                    )
                    
                    drawText(
                        *utils.getCenterPointByRect(challmode_diff_rect),
                        diff.strdiffnum,
                        font = f"{(w + h) / 100}px pgrFont",
                        textAlign = "center",
                        textBaseline = "middle",
                        fillStyle = "white",
                        wait_execute = True
                    )
                except IndexError:
                    root.run_js_code(
                        f"ctx.drawDiagonalRectangle(\
                            {",".join(map(str, this_illu_rect))},\
                            {this_illu_rect_dpower},\
                            'black'\
                        );",
                        wait_execute = True
                    )
                    
                    empty_song_text = ["1st", "2nd", "3rd"][i]
                    drawText(
                        *utils.getCenterPointByRect(this_illu_rect),
                        empty_song_text,
                        font = f"{(w + h) / 80}px pgrFont",
                        textAlign = "center",
                        textBaseline = "middle",
                        fillStyle = "white",
                        wait_execute = True
                    )
                
                selection_illu_now_dx += selection_illu_item_smallwidth
        
        sid = currectSong.difficulty[min(chooseState.diff_index, len(currectSong.difficulty) - 1)].unqique_id()
        diifpd = findPlayDataBySid(sid)
        levelimgname = diifpd["level"] if diifpd["level"] != "never_play" else "NEW"
        levelimg = Resource["levels"][levelimgname]
        levelimg_w = w * 0.05875
        levelimg_h = levelimg_w * levelimg.height / levelimg.width
        
        if not isChallengeMode:
            drawImage(
                f"Level_{levelimgname}",
                w * 0.838625 - levelimg_w / 2,
                h * (798 / 1080) - levelimg_h / 2,
                levelimg_w, levelimg_h,
                wait_execute = True
            )
            
            drawText(
                w * 0.7640625,
                h * (817 / 1080),
                f"{int(diifpd["score"] + 0.5):>07}",
                font = f"{(w + h) / 60}px pgrFontThin",
                textAlign = "right",
                textBaseline = "middle",
                fillStyle = "rgb(255, 255, 255)",
                wait_execute = True
            )
            
            drawText(
                w * 0.81,
                h * (828 / 1080),
                f"{(diifpd["acc"] * 100):>05.2f}%",
                font = f"{(w + h) / 154}px pgrFontThin",
                textAlign = "right",
                textBaseline = "middle",
                fillStyle = "rgb(255, 255, 255)",
                wait_execute = True
            )
        
        if chooseState.diff_index > len(currectSong.difficulty) - 1:
            return
        
        diff = currectSong.difficulty[chooseState.diff_index]
        
        drawText(
            w * 0.390655, h * (419 / 1080),
            diff.strdiffnum,
            font = f"{(w + h) / 44.5}px pgrFont",
            textAlign = "center",
            textBaseline = "middle",
            fillStyle = "rgb(50, 50, 50)",
            wait_execute = True
        )
        
        drawText(
            w * 0.390655, h * (466 / 1080),
            diff.name,
            font = f"{(w + h) / 125}px pgrFont",
            textAlign = "center",
            textBaseline = "middle",
            fillStyle = "rgb(50, 50, 50)",
            wait_execute = True
        )
    
    get_now_sortmethod = lambda: (chooseState.sort_reverse, chooseState.sort_method, chooseState.diff_index)
    last_sort_method = get_now_sortmethod()
    def resort():
        nonlocal last_sort_method
        
        this_sort_method = get_now_sortmethod()
        if this_sort_method == last_sort_method:
            return
        
        song = chapter_item.scsd_songs[chooseControler.vaildNowIndex]
        chapter_item.scsd_songs[:] = chooseState.dosort(
            chapter_item,
            lambda song: findPlayDataBySid(
                song.difficulty[chooseState.diff_index].unqique_id()
            )["score"] if chooseState.diff_index <= len(song.difficulty) - 1 else -1.0
        )
        chooseControler.setto_index(chapter_item.scsd_songs.index(song))
        last_sort_method = this_sort_method

    def clickEventCallback(x, y):
        nonlocal nextUI, tonextUI, tonextUISt
        nonlocal immediatelyExitRender
        
        # 反转排序
        if utils.inrect(x, y, (
            w * 0.14843750, h * (72 / 1080),
            w * 0.14843750 + SortIconWidth, h * (72 / 1080) + SortIconHeight
        )):
            chooseState.sort_reverse = not chooseState.sort_reverse
            resort()
            Resource["UISound_5"].play()
        
        # 下一个排序方法
        if utils.inrect(x, y, (
            w * 0.16875, h * (69 / 1080),
            w * 0.1953125, h * (96 / 1080)
        )):
            chooseState.next_sort_method()
            resort()
            Resource["UISound_5"].play()
        
        # 镜像
        if utils.inrect(x, y, mirrorButtonRect) and not isChallengeMode:
            chooseState.change_mirror()
        
        # 自动游玩
        if utils.inrect(x, y, autoplayButtonRect) and not isChallengeMode:
            chooseState.change_autoplay()
        
        # 随机
        if utils.inrect(x, y, (
            w * 0.375825 - RandomIconWidth / 2,
            h * (53 / 1080) - RandomIconHeight / 2,
            w * 0.375825 + RandomIconWidth / 2,
            h * (53 / 1080) + RandomIconHeight / 2
        )):
            chooseControler.setto_index_ease(random.randint(0, len(chapter_item.scsd_songs) - 1))
        
        # 设置
        if utils.inrect(x, y, (
            w * 0.4476315 - ChartChooseSettingIconWidth / 2,
            h * (53 / 1080) - ChartChooseSettingIconHeight / 2,
            w * 0.4476315 + ChartChooseSettingIconWidth / 2,
            h * (53 / 1080) + ChartChooseSettingIconHeight / 2
        )):
            unregEvents()
            nextUI, tonextUI, tonextUISt = lambda: settingRender(lambda: chooseChartRender(chapter_item, isChallengeMode)), True, time.time()
            mixer.music.fadeout(500)
            Resource["UISound_2"].play()
        
        # 难度选择
        song = chapter_item.scsd_songs[chooseControler.vaildNowIndex]
        xlist = const.LEVEL_CHOOSE_XMAP[len(song.difficulty) - 1]
        for i, leftx in enumerate(xlist):
            leftx *= w
            rect = (
                leftx, h * (775 / 1080),
                leftx + w * 0.0546875, h * (861 / 1080)
            )
            
            if utils.indrect(x, y, rect, utils.getDPower(*utils.getSizeByRect(rect), 75)):
                chooseState.change_diff_byuser(i)
        
        # 开始 - 普通模式
        if utils.indrect(x, y, playButtonRect, utils.getDPower(*utils.getSizeByRect(playButtonRect), 75)) and not isChallengeMode:
            unregEvents()
            
            song = chapter_item.scsd_songs[chooseControler.vaildNowIndex]
            diff = song.difficulty[min(chooseState.diff_index, len(song.difficulty) - 1)]
            chart_information = {
                "Name": song.name,
                "Artist": song.composer,
                "Level": f"{diff.name}  Lv.{diff.strdiffnum}",
                "Illustrator": song.iller,
                "Charter": diff.charter,
                "BackgroundDim": None
            }
            
            immediatelyExitRender = True
            chartPlayerRender(
                chartAudio = utils.gtpresp(diff.chart_audio),
                chartImage = utils.gtpresp(diff.chart_image),
                chartFile = utils.gtpresp(diff.chart_file),
                startAnimation = True,
                chart_information = chart_information,
                foregroundFrameRender = lambda: _render(False),
                renderRelaser = _release_illu,
                nextUI = lambda: chooseChartRender(chapter_item, isChallengeMode),
                font_options = {
                    "songNameFontSize": song.chooseSongs_nameFontSize,
                    "songComposerFontSize": song.currSong_composerFontSize,
                    "levelNumberFontSize": (w + h) / 44.5,
                    "levelNameFontSize": (w + h) / 125
                },
                autoplay = chooseState.is_autoplay,
                sid = diff.unqique_id(),
                mirror = chooseState.is_mirror
            )
        
        # 开始 - 课题模式
        if utils.indrect(x, y, playButtonRect, utils.getDPower(*utils.getSizeByRect(playButtonRect), 75)) and isChallengeMode and len(chooseControler.challengeModeSelections) == 3:
            unregEvents()
            LoadSuccess.play()
            nextUI = lambda: challengeModeRender(chooseControler.challengeModeSelections, lambda: chooseChartRender(chapter_item, isChallengeMode))
            tonextUI, tonextUISt = True, time.time()
        
        # 展开/关闭 用户头像名称rks
        if utils.inrect(x, y, avatar_rect):
            ud_popuper.change()
        
        # 课题模式 - 选中
        if utils.inrect(x, y, selectButtonRect) and isChallengeMode:
            if len(chooseControler.challengeModeSelections) >= 3:
                return
            
            song = chapter_item.scsd_songs[chooseControler.vaildNowIndex]
            diff = song.difficulty[min(chooseState.diff_index, len(song.difficulty) - 1)]
            if (song, diff) in chooseControler.challengeModeSelections:
                return
            
            chooseControler.challengeModeSelections.append((song, diff))
            Resource["UISound_2"].play()
            chooseControler.challenge_mode_select_change_callback()
            startButtonAlpha.target = 1.0 if len(chooseControler.challengeModeSelections) == 3 else 0.5

        # 课题模式 - UNDO
        if utils.inrect(x, y, undoAreaRect) and isChallengeMode:
            if not chooseControler.challengeModeSelections:
                return
            
            chooseControler.challengeModeSelections.pop()
            Resource["UISound_2"].play()
            chooseControler.challenge_mode_select_change_callback()
            startButtonAlpha.target = 1.0 if len(chooseControler.challengeModeSelections) == 3 else 0.5
            
    clickEvent = eventManager.regClickEventFs(clickEventCallback, False)
    
    songShadowRect = const.EMPTY_RECT
    chartsShadowRect = const.EMPTY_RECT
    chartsShadowDPower = const.EMPTY_RECT
    mirrorButtonRect, autoplayButtonRect = const.EMPTY_RECT, const.EMPTY_RECT
    playButtonRect = const.EMPTY_RECT
    avatar_rect = const.EMPTY_RECT
    diffchoosebarRect = const.EMPTY_RECT
    selectButtonRect = const.EMPTY_RECT
    undoAreaRect = const.EMPTY_RECT
    
    chooseControler.disable_valueter()
    chooseState.change_diff(getUserData("internal-lastDiffIndex"))
    chooseControler.enable_valueter()
    
    def _render(rjc: bool = True):
        nonlocal songShadowRect
        nonlocal chartsShadowRect
        nonlocal chartsShadowDPower
        nonlocal mirrorButtonRect, autoplayButtonRect
        nonlocal playButtonRect
        nonlocal avatar_rect
        nonlocal diffchoosebarRect
        
        clearCanvas(wait_execute = True)
        
        drawParallax(0, 0, w, h, True)
        ctxSave(wait_execute=True)
        bgBlurRadio = (w + h) / 60
        bgScale = max((w + bgBlurRadio) / w, (h + bgBlurRadio) / h)
        root.run_js_code(f"ctx.filter = 'blur({bgBlurRadio}px)';", wait_execute=True)
        ctxTranslate(w / 2, h / 2, wait_execute=True)
        ctxScale(bgScale, bgScale, wait_execute=True)
        ctxTranslate(-w / 2 * bgScale, -h / 2 * bgScale, wait_execute=True)
        root.run_js_code(f"mainTempCanvasDrawer.draw(ctx.canvas);", wait_execute=True)
        clearCanvas(wait_execute=True)
        root.run_js_code(f"ctx.drawImage(mainTempCanvasDrawer.cv, 0, 0, {w}, {h});", wait_execute=True)
        ctxRestore(wait_execute=True)
        fillRectEx(0, 0, w, h, "rgba(0, 0, 0, 0.5)", wait_execute=True)
        
        drawFsBgdeCoration({
            "base_color": [0.018, 0.018, 0.018, 0.0901],
            "grid_brightness": 0.4,
            "glow_brightness": 0.71
        })
        
        with utils.shadowDrawer("rgba(0, 0, 0, 0.5)", (w + h) / 125):
            chartsShadowRect = (
                w * -0.009375, 0,
                w * 0.4921875, h
            )
            chartsShadowDPower = utils.getDPower(*utils.getSizeByRect(chartsShadowRect), 75)
            root.run_js_code(
                f"ctx.drawDiagonalRectangle(\
                    {",".join(map(str, chartsShadowRect))},\
                    {chartsShadowDPower},\
                    'rgba(0, 0, 0, 0.3)'\
                );",
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
        
            playButtonRect = (
                w * 0.878125, h * (861 / 1080),
                w * 2.0, h * (1012 / 1080)
            )
            root.run_js_code(
                f"ctx.drawDiagonalRectangle(\
                    {",".join(map(str, playButtonRect))},\
                    {utils.getDPower(*utils.getSizeByRect(playButtonRect), 75)},\
                    'rgba(255, 255, 255, {startButtonAlpha.value})'\
                );",
                wait_execute = True
            )
        
        avatar_rect = phicore.drawUserData(
            root, ud_popuper.p, w, h,
            Resource, avatar_img, userNameWidth,
            userNamePadding, ud_popuper.isPopup,
            getUserData("userdata-userName"),
            getUserData("userdata-rankingScore"),
            getPlayDataItem("hasChallengeMode"),
            getPlayDataItem("challengeModeRank")
        )

        diffchoosebarRect = (
            w * 0.41875, h * (779 / 1080),
            w * 0.865625, h * (857 / 1080)
        )
        root.run_js_code(
            f"ctx.drawDiagonalRectangle(\
                {",".join(map(str, diffchoosebarRect))},\
                {utils.getDPower(*utils.getSizeByRect(diffchoosebarRect), 75)},\
                'rgba(0, 0, 0, 0.3)'\
            );",
            wait_execute = True
        )
        
        drawSongItems()
        
        barShadowRect = (
            w * 0.121875, h * (12 / 1080),
            w * 0.49375, h * (123 / 1080)
        )
        root.run_js_code(
            f"ctx.drawDiagonalRectangle(\
                {",".join(map(str, barShadowRect))},\
                {utils.getDPower(*utils.getSizeByRect(barShadowRect), 75)},\
                'rgba(0, 0, 0, 0.6)'\
            );",
            wait_execute = True
        )
        
        if not isChallengeMode:
            mirrorButtonRect = (
                w * 0.40625, h * (897 / 1080),
                w * 0.4828125, h * (947 / 1080)
            )
            root.run_js_code(
                f"ctx.drawDiagonalRectangle(\
                    {",".join(map(str, mirrorButtonRect))},\
                    {utils.getDPower(*utils.getSizeByRect(mirrorButtonRect), 75)},\
                    '{"rgba(0, 0, 0, 0.4)" if not chooseState.is_mirror else "rgb(255, 255, 255)"}'\
                );",
                wait_execute = True
            )
            
            drawText(
                *utils.getCenterPointByRect(mirrorButtonRect),
                "Mirror",
                font = f"{(w + h) / 130}px pgrFont",
                textAlign = "center",
                textBaseline = "middle",
                fillStyle = "rgba(223, 223, 223, 0.75)" if not chooseState.is_mirror else "rgb(0, 0, 0, 0.8)",
                wait_execute = True
            )
            
            autoplayButtonRect = (
                w * 0.4923828125, h * (897 / 1080),
                w * 0.5689453125, h * (947 / 1080)
            )
            root.run_js_code(
                f"ctx.drawDiagonalRectangle(\
                    {",".join(map(str, autoplayButtonRect))},\
                    {utils.getDPower(*utils.getSizeByRect(autoplayButtonRect), 75)},\
                    '{"rgba(0, 0, 0, 0.4)" if not chooseState.is_autoplay else "rgb(255, 255, 255)"}'\
                );",
                wait_execute = True
            )
            
            drawText(
                *utils.getCenterPointByRect(autoplayButtonRect),
                "Autoplay",
                font = f"{(w + h) / 130}px pgrFont",
                textAlign = "center",
                textBaseline = "middle",
                fillStyle = "rgba(223, 223, 223, 0.75)" if not chooseState.is_autoplay else "rgb(0, 0, 0, 0.8)",
                wait_execute = True
            )
        
        drawImage(
            "Random",
            w * 0.375825 - RandomIconWidth / 2,
            h * (53 / 1080) - RandomIconHeight / 2,
            RandomIconWidth, RandomIconHeight,
            wait_execute = True
        )
        
        drawText(
            w * 0.375825, h * (89 / 1080),
            "随机",
            font = f"{(w + h) / 152}px pgrFontThin",
            textAlign = "center",
            textBaseline = "middle",
            fillStyle = f"rgb(255, 255, 255)",
            wait_execute = True
        )
        
        drawLine(
            w * 0.415625, h * (41 / 1080),
            w * 0.4078315, h * (92 / 1080),
            lineWidth = w / 3000,
            strokeStyle = "rgb(255, 255, 255)",
            wait_execute = True
        )
        
        drawImage(
            "setting",
            w * 0.4476315 - ChartChooseSettingIconWidth / 2,
            h * (53 / 1080) - ChartChooseSettingIconHeight / 2,
            ChartChooseSettingIconWidth, ChartChooseSettingIconHeight,
            wait_execute = True
        )
        
        drawText(
            w * 0.4476315, h * (89 / 1080),
            "设置",
            font = f"{(w + h) / 152}px pgrFontThin",
            textAlign = "center",
            textBaseline = "middle",
            fillStyle = f"rgb(255, 255, 255)",
            wait_execute = True
        )

        root.run_js_code(
            f"ctx.drawTriangleFrame(\
                {w * 0.93125}, {h * (905 / 1080)},\
                {w * 0.93125}, {h * (967 / 1080)},\
                {w * 0.959375}, {h * (936 / 1080)},\
                'rgb(0, 0, 0)', {(w + h) * 0.001}\
            );",
            wait_execute = True
        )
        
        drawText(
            w * 0.1484375, h * (34 / 1080),
            "排序方式",
            font = f"{(w + h) / 135}px pgrFontThin",
            textAlign = "left",
            textBaseline = "top",
            fillStyle = f"rgb(255, 255, 255)",
            wait_execute = True
        )
        
        root.run_js_code(
            f"ctx.drawScaleImage(\
                {root.get_img_jsvarname("sort")},\
                {w * 0.14843750}, {h * (72 / 1080)},\
                {SortIconWidth}, {SortIconHeight},\
                1, {-1 if chooseState.sort_reverse else 1}\
            );",
            wait_execute = True
        )
        
        drawText(
            w * 0.16875, h * (69 / 1080),
            const.PHI_SORTMETHOD_STRING_MAP[chooseState.sort_method],
            font = f"{(w + h) / 100}px pgrFontThin",
            textAlign = "left",
            textBaseline = "top",
            fillStyle = f"rgb(255, 255, 255)",
            wait_execute = True
        )
        
        drawButton("ButtonLeftBlack", "Arrow_Left", (0, 0))
                
        if time.time() - chooseChartRenderSt < 1.25:
            p = (time.time() - chooseChartRenderSt) / 1.25
            root.run_js_code(
                f"ctx.fillRectEx(\
                    0, 0, {w}, {h},\
                    'rgba(0, 0, 0, {(1.0 - p) ** 2})'\
                );",
                wait_execute = True
            )
        
        if tonextUI and time.time() - tonextUISt < 0.75:
            p = (time.time() - tonextUISt) / 0.75
            root.run_js_code(
                f"ctx.fillRectEx(\
                    0, 0, {w}, {h},\
                    'rgba(0, 0, 0, {1.0 - (1.0 - p) ** 2})'\
                );",
                wait_execute = True
            )
        elif tonextUI:
            clearCanvas(wait_execute = True)
            root.run_js_wait_code()
            Thread(target=nextUI, daemon=True).start()
            return True
        
        if rjc:
            root.run_js_wait_code()
    
    def _release_illu():
        illrespacker.unload(illrespacker.getnames())
    
    def _whenexit():
        chooseControler.mixer.music.fadeout(500)
        eventManager.unregEventByChooseChartControl(chooseControler)
        if not immediatelyExitRender:
            _release_illu()
    
    while _render() is None and not immediatelyExitRender:
        ...
    
    _whenexit()

def loadingTransitionRender(nextUI: typing.Callable[[], typing.Any]):
    if not getUserData("setting-enableSceneTransitionAnimation"):
        return nextUI()
        
    global dspSettingWidgets
    
    bg_path = random.choice([
        song.image
        for chapter in Chapters.items
        for song in chapter.songs
    ])
    respacker = webcv.PILResPacker(root)
    respacker.reg_img(utils.gtpresp(bg_path), "loading_transition_bg")
    respacker.load(*respacker.pack())
    
    phicore.root = root
    phicore.w, phicore.h = w, h
    tip = phi_tips.get_tip()
    tip_font_size = phicore.getFontSize(tip, w * 0.84375 * 0.9, w * 0.020833 / 1.25)
    
    tonextUI, tonextUISt = False, float("nan")
    transTime = random.uniform(1.3, 1.8)
    transitionRenderSt = time.time()
    
    while True:
        clearCanvas(wait_execute = True)
        renderT = time.time() - transitionRenderSt
        
        if renderT > 0.5:
            drawCoverFullScreenImage("loading_transition_bg", w, h, wait_execute=True)
            blackRectAlpha = 1.0 - (renderT - 0.5) / 1.125
            if blackRectAlpha <= 1.0:
                fillRectEx(0, 0, w, h, f"rgba(0, 0, 0, {blackRectAlpha})", wait_execute=True)
        
        root.run_js_code(
            f"ctx.drawGrd(\
                {[0.0, h * 0.6, 0.0, h]},\
                {[
                    [0.0, "rgba(0, 0, 0, 0.0)"],
                    [0.25, "rgba(0, 0, 0, 0.0)"],
                    [0.5, "rgba(0, 0, 0, 0.25)"],
                    [0.75, "rgba(0, 0, 0, 0.5)"],
                    [1.0, "rgba(0, 0, 0, 0.796875)"]
                ]},\
                0.0, {h * 0.6}, {w}, {h}\
            );",
            wait_execute = True
        )
        
        phicore.drawTipAndLoading(
            utils.fixorp(renderT / 0.5),
            renderT, tip, tip_font_size
        )
        
        if renderT > transTime and not tonextUI:
            tonextUI, tonextUISt = True, time.time()
                
        if renderT < 1.0:
            p = renderT / 1.0
            root.run_js_code(
                f"ctx.fillRectEx(\
                    0, 0, {w}, {h},\
                    'rgba(0, 0, 0, {(1.0 - p) ** 2})'\
                );",
                wait_execute = True
            )
        
        if tonextUI and time.time() - tonextUISt < 0.75:
            p = (time.time() - tonextUISt) / 0.75
            root.run_js_code(
                f"ctx.fillRectEx(\
                    0, 0, {w}, {h},\
                    'rgba(0, 0, 0, {1.0 - (1.0 - p) ** 2})'\
                );",
                wait_execute = True
            )
        elif tonextUI:
            clearCanvas(wait_execute = True)
            root.run_js_wait_code()
            Thread(target=nextUI, daemon=True).start()
            break
        
        root.run_js_wait_code()
    
    respacker.unload(respacker.getnames())

def challengeModeRender(challengeModeSelections: list[tuple[phigame_obj.Song, phigame_obj.SongDifficulty]], nextUI: typing.Callable[[], None]):
    pplmResults: list[utils.PhigrosPlayLogicManager] = []
    level = 0
    
    for song, diff in challengeModeSelections:
        chart_information = {
            "Name": song.name,
            "Artist": song.composer,
            "Level": f"{diff.name}  Lv.{diff.strdiffnum}",
            "Illustrator": song.iller,
            "Charter": diff.charter,
            "BackgroundDim": None
        }
        pplm, finishPlay = chartPlayerRender(
            chartAudio = utils.gtpresp(diff.chart_audio),
            chartImage = utils.gtpresp(diff.chart_image),
            chartFile = utils.gtpresp(diff.chart_file),
            startAnimation = True,
            chart_information = chart_information,
            playLoadSuccess = False,
            challengeMode = True,
            loadingAnimationStartP = 0.2,
            loadingAnimationBlackIn = True,
            showSettlementAnimation = False
        )
        
        level += int(diff.level)
        
        if not finishPlay:
            return nextUI()
        
        pplmResults.append(pplm)
        
    return challengeModeSettlementRender(pplmResults, challengeModeSelections, nextUI, level)

def challengeModeSettlementRender(
    pplmResults: list[utils.PhigrosPlayLogicManager],
    songs: list[tuple[phigame_obj.Song, phigame_obj.SongDifficulty]],
    nextUI: typing.Callable[[], None],
    level: int
):
    respacker = webcv.PILResPacker(root)
    
    for i, (s, _) in enumerate(songs):
        respacker.reg_img(utils.gtpresp(s.image), f"cmsr_song_{i}")
        
    avatar_img = Image.open(utils.gtpresp(getUserData("userdata-userAvatar")))
    respacker.reg_img(avatar_img, "user_avatar")
    respacker.load(*respacker.pack())
    
    totalScore = sum(pplm.ppps.getScore() for pplm in pplmResults)
    
    if totalScore >= 3000000:
        challengeMode_level = 5
    elif totalScore >= 2940000:
        challengeMode_level = 4
    elif totalScore >= 2850000:
        challengeMode_level = 3
    elif totalScore >= 2700000:
        challengeMode_level = 2
    elif totalScore >= 2460000:
        challengeMode_level = 1
    else:
        return nextUI()
    
    challengeMode_levelName = {5: "AP", 4: "V", 3: "S", 2: "A", 1: "B"}[challengeMode_level]
    challengeModeRank = challengeMode_level * 100 + level
    
    phicore.root = root
    songNameFontSizes = [phicore.getFontSize(song.name, w * 0.8203125 * 0.7, w * 0.021) for song, _ in songs]
    
    def songItemRender(i: int, p: float):
        pplm = pplmResults[i]
        song, diff = songs[i]
        y0 = pplmRenderRect[1] + i * (pplmRenderItemHeight + pplmRenderPady)
        y1 = y0 + pplmRenderItemHeight
        dx = (1 - p) ** 3 * w * 1.4
        songItemRect = (
            pplmrrt_getx_fromy(y1) + dx, y0,
            pplmrrt_getx_fromy(y0) + dx + pplmRenderRectSize[0] * (1 - pplmRenderRectDPower), y1
        )
        songItemSize = utils.getSizeByRect(songItemRect)
        songItemDPower = utils.getDPower(*songItemSize, 75)
        illu_name = f"cmsr_song_{i}"
        illu_rect = (
            songItemRect[0], songItemRect[1],
            songItemRect[0] + songItemSize[0] * 0.52, songItemRect[3]
        )
        illu_rect_dpower = utils.getDPower(*utils.getSizeByRect(illu_rect), 75)
        
        root.run_js_code(
            f"ctx.drawDiagonalRectangle(\
                {",".join(map(str, songItemRect))},\
                {songItemDPower}, 'rgba(0, 0, 0, 0.5)'\
            );",
            wait_execute = True
        )
        
        root.run_js_code(
            f"ctx.drawDiagonalRectangleClipImageOnlyWidth(\
                {",".join(map(str, illu_rect))},\
                {root.get_img_jsvarname(illu_name)},\
                {songItemSize[0]}, {illu_rect_dpower}, 1.0\
            );",
            wait_execute = True
        )
        
        root.run_js_code(
            f"ctx.drawDiagonalGrd(\
                {",".join(map(str, illu_rect))},\
                {illu_rect_dpower}, {[
                    [0.0, "rgba(0, 0, 0, 0.0)"],
                    [0.25, "rgba(0, 0, 0, 0.0)"],
                    [0.5, "rgba(0, 0, 0, 0.25)"],
                    [0.75, "rgba(0, 0, 0, 0.5)"],
                    [1.0, "rgba(0, 0, 0, 0.796875)"]
                ]},\
                {[
                    0.0, illu_rect[1],
                    0.0, illu_rect[3]
                ]}\
            );",
            wait_execute = True
        )
        
        drawText(
            illu_rect[0] + w * 0.0171875, illu_rect[3] - h * (41 / 1080),
            song.name,
            font = f"{songNameFontSizes[i]}px pgrFont",
            textAlign = "left",
            textBaseline = "middle",
            fillStyle = "white",
            wait_execute = True
        )
        
        difffonts = (w + h) / 105
        
        drawText(
            illu_rect[2] - w * 0.0328125,
            illu_rect[1] + h * (185 / 1080),
            f"Lv.{diff.strdiffnum}",
            font = f"{difffonts}px pgrFont",
            textAlign = "right",
            textBaseline = "bottom",
            fillStyle = "white",
            wait_execute = True
        )
        
        drawText(
            illu_rect[2] - w * 0.0328125,
            illu_rect[1] + h * (154 / 1080),
            diff.name,
            font = f"{difffonts}px pgrFont",
            textAlign = "right",
            textBaseline = "bottom",
            fillStyle = "white",
            wait_execute = True
        )
        
        drawText(
            songItemRect[2] - w * 0.034375,
            songItemRect[1] + h * (61 / 1080),
            phicore.stringifyScore(pplm.ppps.getScore()),
            font = f"{(w + h) / 40}px pgrFont",
            textAlign = "right",
            textBaseline = "middle",
            fillStyle = "white",
            wait_execute = True
        )
        
        def drawDataCount(dx: float, text: str, count: int):
            x = songItemRect[2] - dx
            
            drawText(
                x, songItemRect[1] + h * (165 / 1080),
                text,
                font = f"{(w + h) / 195}px pgrFontThin",
                textAlign = "center",
                textBaseline = "middle",
                fillStyle = "rgba(247, 247, 247, 0.8)",
                wait_execute = True
            )
            
            drawText(
                x, songItemRect[1] + h * (133 / 1080),
                f"{count}",
                font = f"{(w + h) / 80}px pgrFont",
                textAlign = "center",
                textBaseline = "middle",
                fillStyle = "white",
                wait_execute = True
            )
        
        def drawELCount(dy: float, text: str, count: int):
            y = songItemRect[1] + dy
            
            drawText(
                songItemRect[2] - w * 0.0390625,
                y,
                f"{count}",
                font = f"{(w + h) / 125}px pgrFont",
                textAlign = "right",
                textBaseline = "middle",
                fillStyle = "white",
                wait_execute = True
            )
            
            drawText(
                songItemRect[2] - w * 0.1203125,
                y,
                text,
                font = f"{(w + h) / 130}px pgrFontThin",
                textAlign = "left",
                textBaseline = "middle",
                fillStyle = "rgba(247, 247, 247, 0.8)",
                wait_execute = True
            )
        
        drawDataCount(w * 0.34375, "Perfect", pplm.ppps.getPerfectCount())
        drawDataCount(w * 0.2703125, "Good", pplm.ppps.getGoodCount())
        drawDataCount(w * 0.2171875, "Bad", pplm.ppps.getBadCount())
        drawDataCount(w * 0.165625, "Miss", pplm.ppps.getMissCount())
        
        drawELCount(h * (131 / 1080), "Early", pplm.ppps.getEarlyCount())
        drawELCount(h * (159 / 1080), "Late", pplm.ppps.getLateCount())
    
    def totalRender(p: float):
        dx = (1 - p) ** 3 * w * 1.4
        totalDataRect = (
            w * 0.5359375 + dx, h * (829 / 1080),
            w * 0.9078125 + dx, h * (968 / 1080)
        )
        
        root.run_js_code(
            f"ctx.drawDiagonalRectangle(\
                {",".join(map(str, totalDataRect))},\
                {utils.getDPower(*utils.getSizeByRect(totalDataRect), 75)},\
                'rgba(0, 0, 0, 0.5)'\
            );",
            wait_execute = True
        )
        
        drawText(
            totalDataRect[0] + w * 0.04375,
            totalDataRect[1] + h * (52 / 1080),
            phicore.stringifyScore(totalScore),
            font = f"{(w + h) / 42}px pgrFont",
            textAlign = "left",
            textBaseline = "middle",
            fillStyle = "white",
            wait_execute = True
        )
    
    def drawButtons(p: float):
        dx = ButtonWidth * (1 - p) ** 1.4
        retry_size = w * const.FINISH_UI_BUTTON_SIZE / 190 * 145 * 0.3
        drawButton("ButtonLeftBlack", "Retry", (-dx, 0), (retry_size, retry_size))
        drawButton("ButtonRightBlack", "Arrow_Left", (w + dx - ButtonWidth, h - ButtonHeight))
    
    renderSt = time.time()
    tonextUI, tonextUISt = False, float("nan")
    showingCMR, showingCMRSt = False, float("nan")
    mixer.music.load("./resources/Over.mp3")
    Thread(target=lambda: (time.sleep(0.25), mixer.music.play(-1)), daemon=True).start()
    
    ud_popuper = UserDataPopuper()
    userNameConstFontSize = (w + h) / const.USERNAME_CONST_FONT
    userNamePadding = w * 0.01
    userNameWidth = root.run_js_code(f"ctx.getTextSize({repr(getUserData("userdata-userName"))}, '{userNameConstFontSize}px pgrFont')[0];") + userNamePadding * 2
    
    avatar_rect = const.EMPTY_RECT
    cross_rect = const.EMPTY_RECT
    checked_rect = const.EMPTY_RECT
    
    songItemRenderDur = 1.5
    renderTasks = [
        {"st": 0.2, "dur": songItemRenderDur, "render": lambda p: songItemRender(0, p)},
        {"st": 0.8, "dur": songItemRenderDur, "render": lambda p: songItemRender(1, p)},
        {"st": 1.4, "dur": songItemRenderDur, "render": lambda p: songItemRender(2, p)},
        {"st": 2.0, "dur": songItemRenderDur, "render": totalRender},
        {"st": 3.2, "dur": 0.7, "render": lambda p: drawAlphaImage(
            f"Level_{challengeMode_levelName}",
            w * 0.8578125 - (lw := w * 0.0875 * 1.3 * (1.0 + ((1.0 - p) ** 1.7) * 0.4)) / 2,
            h * (841 / 1080) - (lh := lw / Resource["levels"][challengeMode_levelName].width * Resource["levels"][challengeMode_levelName].height) / 2,
            lw, lh,
            1.0 - (1.0 - p) ** 2,
            wait_execute = True
        )},
        {"st": 4.0, "dur": 0.7, "render": lambda p: phicore.drawUserData(
            root, ud_popuper.p, w, h,
            Resource, avatar_img, userNameWidth,
            userNamePadding, ud_popuper.isPopup,
            getUserData("userdata-userName"),
            getUserData("userdata-rankingScore"),
            getPlayDataItem("hasChallengeMode"),
            getPlayDataItem("challengeModeRank"),
            1.0 - (1.0 - p) ** 2
        ), "tag": "userdata"},
        {"st": 4.7, "dur": 0.7, "render": drawButtons}
    ]
    
    def unregEvents():
        eventManager.unregEvent(mainClickEvent)
        
    def findRenderTaskByTag(tag: str):
        for task in renderTasks:
            if task.get("tag", None) == tag:
                return task
        
        return None
    
    def mainClickCallback(x, y):
        nonlocal nextUI, tonextUI, tonextUISt
        nonlocal showingCMR, showingCMRSt
        
        # 点击头像
        if utils.inrect(x, y, avatar_rect) and not showingCMR:
            ud_popuper.change()
        
        # 重试
        if utils.inrect(x, y, (0, 0, ButtonWidth, ButtonHeight)) and now_t > 4.8 and not showingCMR:
            unregEvents()
            nextUI_Bak = nextUI
            nextUI, tonextUI, tonextUISt = lambda: challengeModeRender(songs, nextUI_Bak), True, time.time()
        
        # 继续
        if utils.inrect(x, y, (w - ButtonWidth, h - ButtonHeight, w, h)) and now_t > 4.8 and not showingCMR:
            showingCMR, showingCMRSt = True, time.time()
            renderTasks.extend([
                {"st": now_t + 0.7, "dur": 0.7, "render": lambda p: drawAlphaImage(
                    f"cmlevel_{challengeMode_level}",
                    w / 2 - (cml_w := (w * 0.1875 * 1.1)) / 2,
                    h * (605 / 1080) - (cml_h := cml_w / Resource["challenge_mode_levels"][challengeMode_level].width * Resource["challenge_mode_levels"][challengeMode_level].height) / 2,
                    cml_w, cml_h,
                    1.0 - (1.0 - utils.fixorp(p)) ** 2,
                    wait_execute = True
                ), "cmr": True},
                {"st": now_t + 0.5, "dur": 0.7, "render": lambda p: drawText(
                    w / 2, h * (545 / 1080),
                    f"{level}",
                    font = f"{(w + h) / 20 * (1.0 + ((1.0 - p) ** 2) * 0.4)}px pgrFont",
                    textAlign = "center",
                    textBaseline = "middle",
                    fillStyle = f"rgba(255, 255, 255, {1.0 - (1.0 - utils.fixorp(p * 2)) ** 2})",
                    wait_execute = True
                ), "cmr": True},
                {"st": now_t + 1.0, "dur": 0.7, "render": lambda p: drawAlphaImage(
                    "cross",
                    height = (cross_h := (h * (71 / 1080))),
                    width = (cross_w := cross_h / Resource["cross"].height * Resource["cross"].width),
                    x = w / 2 - w * 0.10625 - cross_w / 2,
                    y = h * (836 / 1080) - cross_h / 2,
                    alpha = 1.0 - (1.0 - utils.fixorp(p)) ** 2,
                    wait_execute = True
                ), "cmr": True, "tag": "cross"},
                {"st": now_t + 1.6, "dur": 0.7, "render": lambda p: drawAlphaImage(
                    "checked",
                    height = (checked_h := (h * (71 / 1080))),
                    width = (checked_w := checked_h / Resource["checked"].height * Resource["checked"].width),
                    x = w / 2 + w * 0.10625 - checked_w / 2,
                    y = h * (836 / 1080) - checked_h / 2,
                    alpha = 1.0 - (1.0 - utils.fixorp(p)) ** 2,
                    wait_execute = True
                ), "cmr": True, "tag": "checked"},
            ])
        
        # 放弃成绩
        if utils.inrect(x, y, cross_rect):
            rt = findRenderTaskByTag("cross")
            if rt is not None and rt["st"] <= now_t:
                unregEvents()
                tonextUI, tonextUISt = True, time.time()
        
        # 保存成绩
        if utils.inrect(x, y, checked_rect):
            rt = findRenderTaskByTag("checked")
            if rt is not None and rt["st"] <= now_t:
                unregEvents()
                nextUI_Bak = nextUI
                nextUI, tonextUI, tonextUISt = lambda: (
                    setPlayDataItem("challengeModeRank", challengeModeRank),
                    setPlayDataItem("hasChallengeMode", True),
                    savePlayData(playData),
                    nextUI_Bak()
                ), True, time.time()
        
    mainClickEvent = phigame_obj.ClickEvent(
        rect = (0, 0, w, h),
        callback = mainClickCallback,
        once = False
    )
    eventManager.regClickEvent(mainClickEvent)
    
    while True:
        clearCanvas(wait_execute = True)
        drawImage("AllSongBlur", 0, 0, w, h, wait_execute=True)
        
        pplmRenderRect = (
            w * 0.075, h * (145 / 1080),
            w * 0.8953125, h * (795 / 1080)
        )
        pplmRenderRectSize = utils.getSizeByRect(pplmRenderRect)
        pplmRenderRectDPower = utils.getDPower(*pplmRenderRectSize, 75)
        pplmRenderPady = h * (33 / 1080)
        pplmRenderItemHeight = (pplmRenderRectSize[1] - pplmRenderPady * 2) / 3
        pplmrrt_getx_fromy = lambda y: pplmRenderRect[0] + (1.0 - (y - pplmRenderRect[1]) / pplmRenderRectSize[1]) * pplmRenderRectSize[0] * pplmRenderRectDPower
        
        # root.run_js_code(
        #     f"ctx.drawDiagonalRectangle(\
        #         {",".join(map(str, pplmRenderRect))},\
        #         {pplmRenderRectDPower}, 'rgba(0, 0, 0, 0.5)'\
        #     );",
        #     wait_execute = True
        # )
        
        # drawButton("ButtonRightBlack", "Arrow_Right", (w - ButtonWidth, h - ButtonHeight))
        
        cmr_seted_ga = False
        if showingCMR:
            cmr_p = utils.fixorp((time.time() - showingCMRSt) / 1.75)
            ctxSave(wait_execute=True)
            ctxSetGlobalAlpha(1.0 - utils.fixorp(cmr_p * 3.5), wait_execute=True)
            cmr_seted_ga = True
        
        now_t = time.time() - renderSt
        for task in renderTasks:
            if now_t >= task["st"] and not task.get("cmr", False):
                p = utils.fixorp((now_t - task["st"]) / task["dur"])
                res = task["render"](p)
                tag = task.get("tag", None)
                
                match tag:
                    case "userdata":
                        avatar_rect = res
        
        if cmr_seted_ga:
            ctxRestore(wait_execute=True)
            fillRectEx(0, 0, w, h, f"rgba(0, 0, 0, {utils.fixorp(cmr_p * 3.5) * 0.6})", wait_execute=True)
            
            for task in renderTasks:
                if now_t >= task["st"] and task.get("cmr", False):
                    p = utils.fixorp((now_t - task["st"]) / task["dur"])
                    res = task["render"](p)
                    tag = task.get("tag", None)
                    
                    match tag:
                        case "cross":
                            cross_rect = utils.xywh_rect2_xxyy(res)
                        
                        case "checked":
                            checked_rect = utils.xywh_rect2_xxyy(res)
        
        if time.time() - renderSt < 1.25:
            p = (time.time() - renderSt) / 1.25
            root.run_js_code(
                f"ctx.fillRectEx(\
                    0, 0, {w}, {h},\
                    'rgba(0, 0, 0, {(1.0 - p) ** 2})'\
                );",
                wait_execute = True
            )
        
        if tonextUI and time.time() - tonextUISt < 0.75:
            p = (time.time() - tonextUISt) / 0.75
            root.run_js_code(
                f"ctx.fillRectEx(\
                    0, 0, {w}, {h},\
                    'rgba(0, 0, 0, {1.0 - (1.0 - p) ** 2})'\
                );",
                wait_execute = True
            )
        elif tonextUI:
            clearCanvas(wait_execute = True)
            root.run_js_wait_code()
            mixer.music.fadeout(500)
            root.run_js_code("mask.style.backdropFilter = '';", wait_execute = True)
            Thread(target=nextUI, daemon=True).start()
            break
        
        root.run_js_wait_code()
        
    respacker.unload(respacker.getnames())
    
def importArchiveFromPhigros():
    root.run_js_code(f"alert({repr("已移除。")});")

def updateFontSizes():
    global userName_FontSize
    
    userName_Width1px = root.run_js_code(f"ctx.font='50px pgrFont'; ctx.measureText({repr(getUserData("userdata-userName"))}).width;") / 50
    userName_FontSize = w * 0.209375 / (userName_Width1px if userName_Width1px != 0.0 else 1.0)
    if userName_FontSize > w * 0.0234375:
        userName_FontSize = w * 0.0234375

def updateSettingConfig():
    userData.update({
        "setting-chartOffset": PlaySettingWidgets["OffsetSlider"].value,
        "setting-noteScale": PlaySettingWidgets["NoteScaleSlider"].value,
        "setting-backgroundDim": PlaySettingWidgets["BackgroundDimSlider"].value,
        "setting-enableClickSound": PlaySettingWidgets["ClickSoundCheckbox"].checked,
        "setting-musicVolume": PlaySettingWidgets["MusicVolumeSlider"].value,
        "setting-uiVolume": PlaySettingWidgets["UISoundVolumeSlider"].value,
        "setting-clickSoundVolume": PlaySettingWidgets["ClickSoundVolumeSlider"].value,
        "setting-enableMorebetsAuxiliary": PlaySettingWidgets["MorebetsAuxiliaryCheckbox"].checked,
        "setting-enableFCAPIndicator": PlaySettingWidgets["FCAPIndicatorCheckbox"].checked,
        "setting-enableLowQuality": PlaySettingWidgets["LowQualityCheckbox"].checked,
        "setting-enableSceneTransitionAnimation": PlaySettingWidgets["SceneTransitionAnimationCheckbox"].checked,
        "setting-enableTrigrid": PlaySettingWidgets["TrigridCheckbox"].checked,
    })
    
    Resource["CalibrationHit"].set_volume(getUserData("setting-clickSoundVolume"))

def updateDSPConfig():
    userData.update({
        "internal-dspBufferExponential": dspSettingWidgets["ValueSlider"].value
    })

def updateSettingWidgets():
    PlaySettingWidgets["OffsetLabel"].right_text = f"{int(getUserData("setting-chartOffset"))}ms"
    PlaySettingWidgets["OffsetTip"].right_text = "*请调节至第三拍的声音与按键音恰好重合的状态" if getUserData("setting-enableClickSound") else "*请调节至第三拍的声音与按键爆开几乎同时的状态"

def updateDSPWidgets():
    dspSettingWidgets["ValueLabel"].right_text = f"{2 ** getUserData("internal-dspBufferExponential")}"

def updateConfig():
    rcfg = userData.copy()
    
    try: updateSettingConfig()
    except KeyError: pass
    try: updateDSPConfig()
    except KeyError: pass
    
    try: updateSettingWidgets()
    except KeyError: pass
    try: updateDSPWidgets()
    except KeyError: pass
    
    if userData != rcfg:
        saveUserData(userData)
    
    if rcfg["setting-enableLowQuality"] != getUserData("setting-enableLowQuality"):
        applyConfig()

def applyConfig():
    if getUserData("setting-enableLowQuality"):
        root.run_js_code(f"lowquality_scale = {1.0 / webdpr * getUserData("internal-lowQualityScale")};")
        root.run_js_code(f"lowquality_imjscvscale_x = {getUserData("internal-lowQualityScale-JSLayer")};")
        root.run_js_code(f"ctx.imageSmoothingEnabled = false;")
    else:
        root.run_js_code(f"lowquality_scale = {1.0 / webdpr};")
        root.run_js_code(f"lowquality_imjscvscale_x = 1.0;")
        root.run_js_code(f"ctx.imageSmoothingEnabled = true;")
    root.run_js_code(f"resizeCanvas({rw}, {rh});") # update canvas

root = webcv.WebCanvas(
    width = 1, height = 1,
    x = -webcv.screen_width, y = -webcv.screen_height,
    title = "phispler - Phigros Simulator",
    debug = "--debug" in sys.argv,
    resizable = "--resizeable" in sys.argv,
    frameless = "--frameless" in sys.argv,
    renderdemand = "--renderdemand" in sys.argv,
    renderasync = "--renderasync" in sys.argv
)
utils.shadowDrawer.root = root

def init():
    global webdpr
    global dw_legacy, dh_legacy
    global rw, rh
    global w, h
    global Resource, eventManager
    global presentationArrow
    
    presentationArrow = "--presentation-arrow" in sys.argv
    
    if webcv.disengage_webview:
        socket_webviewbridge.hook(root)
    
    w, h, webdpr, dw_legacy, dh_legacy = root.init_window_size_and_position(0.6)
    root.run_js_code(f"lowquality_scale = {1.0 / webdpr};")
    
    if presentationArrow:
        root.wait_jspromise("ctx.loadArrowImage();")
        root.run_js_code("document.body.style.cursor = 'none';")

    rw, rh = w, h
    if "--usu169" in sys.argv:
        ratio = w / h
        if ratio > 16 / 9:
            w = int(h * 16 / 9)
        else:
            h = int(w / 16 * 9)
        root.run_js_code("usu169 = true;")
    root.run_js_code(f"resizeCanvas({rw}, {rh});")

    loadChapters()
    Resource = loadResource()
    eventManager = phigame_obj.EventManager()
    bindEvents()
    updateFontSizes()
    applyConfig()
    Thread(target=showStartAnimation, daemon=True).start()
        
    root.wait_for_close()
    exitfunc(0)

Thread(target=root.init, args=(init, ), daemon=True).start()
root.start()
