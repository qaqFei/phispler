import err_processer as _
import init_logging as _
import fix_workpath as _
import import_argvs as _
import check_edgechromium as _
import check_bin as _

import json
import sys
import time
import logging
import typing
from threading import Thread
from os import popen
from os.path import exists
from ntpath import basename

import requests
from PIL import Image, ImageFilter
from pydub import AudioSegment

import webcv
import dxsound
import const
import utils
import dialog
import info_loader
import ppr_help
import file_loader
import phira_respack
import phicore
import tempdir
import socket_webviewbridge
import wcv2matlike
import needrelease
import phichart
from dxsmixer import mixer
from exitfunc import exitfunc
from graplib_webview import *

import load_extended as _

if len(sys.argv) == 1:
    print(ppr_help.HELP_ZH)
    raise SystemExit

tempdir.clearTempDir()
temp_dir = tempdir.createTempDir()

enable_clicksound = "--noclicksound" not in sys.argv
debug = "--debug" in sys.argv
loop = "--loop" in sys.argv
render_range_more = "--render-range-more" in sys.argv
render_range_more_scale = 2.0 if "--render-range-more-scale" not in sys.argv else eval(sys.argv[sys.argv.index("--render-range-more-scale") + 1])
noautoplay = "--noautoplay" in sys.argv
rtacc = "--rtacc" in sys.argv
lowquality = "--lowquality" in sys.argv
lowquality_scale = float(sys.argv[sys.argv.index("--lowquality-scale") + 1]) ** 0.5 if "--lowquality-scale" in sys.argv else 2.0 ** 0.5
showfps = "--showfps" in sys.argv
speed = float(sys.argv[sys.argv.index("--speed") + 1]) if "--speed" in sys.argv else 1.0
clickeffect_randomblock_roundn = eval(sys.argv[sys.argv.index("--clickeffect-randomblock-roundn") + 1]) if "--clickeffect-randomblock-roundn" in sys.argv else 0.0
noplaychart = "--noplaychart" in sys.argv
clicksound_volume = float(sys.argv[sys.argv.index("--clicksound-volume") + 1]) if "--clicksound-volume" in sys.argv else 1.0
musicsound_volume = float(sys.argv[sys.argv.index("--musicsound-volume") + 1]) if "--musicsound-volume" in sys.argv else 1.0
lowquality_imjscvscale_x = float(sys.argv[sys.argv.index("--lowquality-imjscvscale-x") + 1]) if "--lowquality-imjscvscale-x" in sys.argv else 1.0
lowquality_imjs_maxsize = float(sys.argv[sys.argv.index("--lowquality-imjs-maxsize") + 1]) if "--lowquality-imjs-maxsize" in sys.argv else 256
wl_more_chinese = "--wl-more-chinese" in sys.argv
skip_time = float(sys.argv[sys.argv.index("--skip-time") + 1]) if "--skip-time" in sys.argv else 0.0
enable_jscanvas_bitmap = "--enable-jscanvas-bitmap" in sys.argv
respath = sys.argv[sys.argv.index("--res") + 1] if "--res" in sys.argv else "./resources/resource_packs/default"
usu169 = "--usu169" in sys.argv
render_video = "--render-video" in sys.argv
render_video_fps = float(sys.argv[sys.argv.index("--render-video-fps") + 1]) if "--render-video-fps" in sys.argv else 60.0
render_video_fourcc = sys.argv[sys.argv.index("--render-video-fourcc") + 1] if "--render-video-fourcc" in sys.argv else "mp4v"
renderdemand = "--renderdemand" in sys.argv
renderasync = "--renderasync" in sys.argv
render_video_buffer_size = 45 if "--render-video-buffer-size" not in sys.argv else int(sys.argv[sys.argv.index("--render-video-buffer-size") + 1])

if render_video and noautoplay:
    noautoplay = False
    logging.warning("if use --render-video, you cannot use --noautoplay")

if render_video and showfps:
    showfps = False
    logging.warning("if use --render-video, you cannot use --showfps")

if render_video and renderasync:
    renderasync = False
    logging.warning("if use --render-video, you cannot use --renderasync")

if render_video and renderdemand:
    renderdemand = False
    logging.warning("if use --render-video, you cannot use --renderdemand")

if "--mirror" in sys.argv:
    phicore.enableMirror = True
    
if "--disable-watermark" in sys.argv:
    phicore.enableWatermark = False

combotips = ("AUTOPLAY" if not noautoplay else "COMBO") if "--combotips" not in sys.argv else sys.argv[sys.argv.index("--combotips") + 1]
mixer.init()

if "--phira-chart" in sys.argv:
    logging.info("Downloading phira chart...")
    pctid = sys.argv[sys.argv.index("--phira-chart") + 1]
    apiresult = requests.get(f"https://phira.5wyxi.com/chart/{pctid}").json()
    if "error" in apiresult:
        logging.error(f"phira api: {apiresult["error"]}")
        raise SystemExit
    
    sys.argv.insert(1, f"{temp_dir}/phira-temp-chart.zip" if "--phira-chart-save" not in sys.argv else sys.argv[sys.argv.index("--phira-chart-save") + 1])
    with open(sys.argv[1], "wb") as f:
        with requests.get(apiresult["file"], stream=True) as reqs:
            for content in reqs.iter_content(chunk_size=1024):
                f.write(content)
    logging.info("Downloaded phira chart.")

logging.info("Unpack Chart...")
popen(f"7z x \"{sys.argv[1]}\" -o\"{temp_dir}\" -y").read()

logging.info("Loading All Files of Chart...")
files_dict = {
    "charts": [],
    "images": [],
    "audio": [],
}
chartimages = {}
cfrfp_procer: typing.Callable[[str], str] = lambda x: x.replace(f"{temp_dir}/", "")

for item in utils.getAllFiles(temp_dir):
    if item.endswith("info.txt") or item.endswith("info.csv") or item.endswith("info.yml") or item.endswith("extra.json") or item.endswith(".glsl"):
        continue
    
    item_rawname = cfrfp_procer(item)
    loadres = file_loader.loadfile(item)
    
    match loadres.filetype:
        case file_loader.FILE_TYPE.CHART:
            files_dict["charts"].append([item, loadres.data])
            
        case file_loader.FILE_TYPE.IMAGE:
            files_dict["images"].append([item, loadres.data])
            
        case file_loader.FILE_TYPE.SONG:
            files_dict["audio"].append(item)
        
        case file_loader.FILE_TYPE.UNKNOW:
            logging.warning(f"Unknow resource type. path = {item_rawname}") # errors: ")
            # for e in loadres.errs: logging.warning(f"\t{repr(e)}")
                    
if not files_dict["charts"]:
    logging.fatal("No Chart File Found")
    raise SystemExit

if not files_dict["audio"]:
    logging.fatal("No Audio File Found")
    raise SystemExit

if not files_dict["images"]:
    logging.warning("No Image File Found")
    files_dict["images"].append(["default", Image.new("RGB", (16, 9), "black")])

chart_fp: str
chart_json: dict
cimg_fp: str
chart_image: Image.Image
audio_fp: str

chart_index = file_loader.choosefile(
    fns = map(lambda x: x[0], files_dict["charts"]),
    prompt = "请选择谱面文件: ", rawprocer = cfrfp_procer
)
chart_fp, chart_json = files_dict["charts"][chart_index]

if exists(f"{temp_dir}/extra.json"):
    try:
        logging.info("found extra.json, loading...")
        extra = phichart.loadExtra(json.load(open(f"{temp_dir}/extra.json", "r", encoding="utf-8")))
        logging.info("loading extra.json successfully")
    except SystemExit as e:
        logging.error("loading extra.json failed")
        
if "extra" not in globals():
    extra = phichart.loadExtra({})
    
chart_obj = phichart.load(chart_json)
def loadChartObject(first: bool = False):
    global chart_obj
    chart_obj = phichart.load(chart_json)
    
    if "--load-bpc" in sys.argv:
        chart_obj = phichart.CommonChart.loaddump(open(sys.argv[sys.argv.index("--load-bpc") + 1], "rb").read())
    
    if chart_obj.is_rpe():
        chart_obj.options.rpeVersion = (
            sys.argv[sys.argv.index("--rpeversion") + 1]
            if "--rpeversion" in sys.argv
            else chart_obj.options.rpeVersion
        )
        
    chart_obj.extra = extra
    chart_obj.init_extra()
        
    if not first:
        updateCoreConfig()

loadChartObject(True)

cimg_index = file_loader.choosefile(
    fns = map(lambda x: x[0], files_dict["images"]),
    prompt = "请选择背景图片: ", rawprocer = cfrfp_procer,
    default = chart_obj.options.res_ext_background if chart_obj.is_rpe() else None
)
cimg_fp, chart_image = files_dict["images"][cimg_index]
chart_image = chart_image.convert("RGB")

audio_index = file_loader.choosefile(
    fns = files_dict["audio"],
    prompt = "请选择音频文件: ", rawprocer = cfrfp_procer,
    default = chart_obj.options.res_ext_song if chart_obj.is_rpe() else None
)
audio_fp = files_dict["audio"][audio_index]

raw_audio_fp = audio_fp
if speed != 1.0:
    logging.info(f"Processing audio, rate = {speed}")
    seg: AudioSegment = AudioSegment.from_file(audio_fp)
    seg = seg._spawn(seg.raw_data, overrides = {
        "frame_rate": int(seg.frame_rate * speed)
    }).set_frame_rate(seg.frame_rate)
    audio_fp = f"{temp_dir}/ppr_temp_audio_{time.time()}.wav"
    seg.export(audio_fp, format="wav")
    
phi_rpack = phira_respack.PhiraResourcePack(respath)
phi_rpack.setToGlobal()
phi_rpack.printInfo()
    
if "--prespwan-clicksound" in sys.argv:
    logging.warning("prespwan click sound cannot spwan costom click sound.")
    
    import audio_utils
    
    seg: AudioSegment = AudioSegment.from_file(audio_fp)
    cs_mixer = audio_utils.AudioMixer(seg)
    cs_segs = phi_rpack.createResourceDict()["Note_Click_Audio_Pydub"]
    
    for line in chart_obj.lines:
        for note in line.notes:
            if not note.isFake:
                t = (note.time + chart_obj.offset) / speed
                cs_mixer.mix(cs_segs[note.type], t)
    
    audio_fp = f"{temp_dir}/ppr_temp_audio_{time.time()}.wav"
    cs_mixer.get().export(audio_fp, format="wav")
    
    enable_clicksound = False

mixer.music.load(audio_fp)
raw_audio_length = mixer.music.get_length()

if "--soundapi-downgrade" in sys.argv and not render_video:
    seg: AudioSegment = AudioSegment.from_file(audio_fp)
    speed *= seg.duration_seconds / raw_audio_length
    
all_inforamtion = {}
logging.info("Loading Chart Information...")

ChartInfoLoader = info_loader.InfoLoader([f"{temp_dir}/info.csv", f"{temp_dir}/info.txt", f"{temp_dir}/info.yml"])
chart_information = ChartInfoLoader.get(basename(chart_fp), basename(raw_audio_fp), basename(cimg_fp))

if chart_obj.is_rpe() and chart_information is ChartInfoLoader.default_info:
    chart_information["Name"] = chart_obj.options.meta_ext_name
    chart_information["Artist"] = chart_obj.options.meta_ext_composer
    chart_information["Level"] = chart_obj.options.meta_ext_level
    chart_information["Charter"] = chart_obj.options.meta_ext_charter

logging.info("Loading Chart Information Successfully")
logging.info("Chart Info: ")
for k,v in chart_information.items():
    logging.info(f"           {k}: {v}")

def loadResource():
    global globalNoteWidth
    global note_max_width, note_max_height
    global note_max_size_half
    global WaitLoading, LoadSuccess
    global chart_res
    global cksmanager
    
    logging.info("Loading Resource...")
    WaitLoading = mixer.Sound("./resources/WaitLoading.mp3")
    LoadSuccess = mixer.Sound("./resources/LoadSuccess.wav")
    Thread(target=WaitLoading_FadeIn, daemon = True).start()
    LoadSuccess.set_volume(0.75)
    WaitLoading.play(-1)
    noteWidth_raw = w * const.NOTE_DEFAULTSIZE
    globalNoteWidth = noteWidth_raw * (eval(sys.argv[sys.argv.index("--scale-note") + 1]) if "--scale-note" in sys.argv else 1.0)
    
    Resource = {
        "levels":{
            "AP": Image.open("./resources/levels/AP.png"),
            "FC": Image.open("./resources/levels/FC.png"),
            "V": Image.open("./resources/levels/V.png"),
            "S": Image.open("./resources/levels/S.png"),
            "A": Image.open("./resources/levels/A.png"),
            "B": Image.open("./resources/levels/B.png"),
            "C": Image.open("./resources/levels/C.png"),
            "F": Image.open("./resources/levels/F.png")
        },
        "challenge_mode_levels": [
            Image.open(f"./resources/challenge_mode_levels/{i}.png")
            for i in range(6)
        ],
        "le_warn": Image.open("./resources/le_warn.png"),
        "Retry": Image.open("./resources/Retry.png"),
        "Arrow_Right": Image.open("./resources/Arrow_Right.png"),
        "Over": mixer.Sound("./resources/Over.mp3"),
        "Pause": mixer.Sound("./resources/Pause.wav"),
        "PauseImg": Image.open("./resources/Pause.png"),
        "ButtonLeftBlack": Image.open("./resources/Button_Left_Black.png"),
        "ButtonRightBlack": None
    }
    
    Resource.update(phi_rpack.createResourceDict())
    
    respacker = webcv.PILResPacker(root)
    
    background_image_blur = chart_image.filter(ImageFilter.GaussianBlur(sum(chart_image.size) / 50))
    respacker.reg_img(background_image_blur, "background_blur")
    
    Resource["ButtonRightBlack"] = Resource["ButtonLeftBlack"].transpose(Image.FLIP_LEFT_RIGHT).transpose(Image.FLIP_TOP_BOTTOM)
    
    for k, v in Resource["Notes"].items():
        respacker.reg_img(Resource["Notes"][k], f"Note_{k}")
    
    for i in range(phira_respack.globalPack.effectFrameCount):
        respacker.reg_img(Resource["Note_Click_Effect"]["Perfect"][i], f"Note_Click_Effect_Perfect_{i + 1}")
        respacker.reg_img(Resource["Note_Click_Effect"]["Good"][i], f"Note_Click_Effect_Good_{i + 1}")
        
    for k,v in Resource["levels"].items():
        respacker.reg_img(v, f"Level_{k}")
    
    for i, v in enumerate(Resource["challenge_mode_levels"]):
        respacker.reg_img(v, f"cmlevel_{i}")
        
    respacker.reg_img(Resource["le_warn"], "le_warn")
    respacker.reg_img(chart_image, "chart_image")
    respacker.reg_img(Resource["Retry"], "Retry")
    respacker.reg_img(Resource["Arrow_Right"], "Arrow_Right")
    respacker.reg_img(Resource["PauseImg"], "PauseImg")
    respacker.reg_img(Resource["ButtonLeftBlack"], "ButtonLeftBlack")
    respacker.reg_img(Resource["ButtonRightBlack"], "ButtonRightBlack")
    
    chart_res = {}
    
    if chart_obj.is_rpe():
        imfns: list[str] = list(map(lambda x: x[0], files_dict["images"]))
        imobjs: list[Image.Image] = list(map(lambda x: x[1], files_dict["images"]))
        
        for line in chart_obj.lines:
            if not line.isTextureLine: continue
            if not line.isGifLine:
                paths = [
                    f"{temp_dir}/{line.texture}",
                    f"{temp_dir}/{line.texture}.png",
                    f"{temp_dir}/{line.texture}.jpg",
                    f"{temp_dir}/{line.texture}.jpeg"
                ]
                
                for p in paths:
                    if utils.fileinlist(p, imfns):
                        texture_index = utils.findfileinlist(p, imfns)
                        texture: Image.Image = imobjs[texture_index]
                        chart_res[line.texture] = (texture.convert("RGBA"), texture.size)
                        logging.info(f"Loaded line texture {line.texture}")
                        break
                else:
                    logging.warning(f"Cannot find texture {line.texture}")
                    texture = Image.new("RGBA", (4, 4), (0, 0, 0, 0))
                    chart_res[line.texture] = (texture, texture.size)
                    
                respacker.reg_img(chart_res[line.texture][0], f"lineTexture_{line.index}")
            else:
                h264data, size = utils.video2h264(f"{temp_dir}/{line.texture}")
                chart_res[line.texture] = (None, size)
                name = f"lineTexture_{line.index}"
                root.reg_res(h264data, f"{name}.mp4")
                root.wait_jspromise(f"loadvideo(\"{root.get_resource_path(f"{name}.mp4")}\", '{name}_img');")

        for video in extra.videos:
            root.reg_res(video.h264data, f"{video.unqique_id}.mp4")
            root.wait_jspromise(f"loadvideo(\"{root.get_resource_path(f"{video.unqique_id}.mp4")}\", '{video.unqique_id}_img');")
        
        for k, v in chart_res.items():
            chart_res[k] = (None, v[1])
        
    root.reg_res(open("./resources/font.ttf", "rb").read(), "pgrFont.ttf")
    root.reg_res(open("./resources/font-thin.ttf", "rb").read(), "pgrFontThin.ttf")
    respacker.load(*respacker.pack())
    
    root.wait_jspromise(f"loadFont('pgrFont', \"{root.get_resource_path("pgrFont.ttf")}\");")
    root.wait_jspromise(f"loadFont('pgrFontThin', \"{root.get_resource_path("pgrFontThin.ttf")}\");")
    root.unreg_res("pgrFont.ttf")
    root.unreg_res("pgrFontThin.ttf")
    
    # root.file_server.shutdown()
    note_max_width = max(globalNoteWidth * i for i in phira_respack.globalPack.dub_fixscale.values())
    note_max_height = max((
        note_max_width / Resource["Notes"]["Tap"].width * Resource["Notes"]["Tap"].height,
        note_max_width / Resource["Notes"]["Tap_dub"].width * Resource["Notes"]["Tap_dub"].height,
        note_max_width / Resource["Notes"]["Drag"].width * Resource["Notes"]["Drag"].height,
        note_max_width / Resource["Notes"]["Drag_dub"].width * Resource["Notes"]["Drag_dub"].height,
        note_max_width / Resource["Notes"]["Flick"].width * Resource["Notes"]["Flick"].height,
        note_max_width / Resource["Notes"]["Flick_dub"].width * Resource["Notes"]["Flick_dub"].height,
        note_max_width / Resource["Notes"]["Hold_Head"].width * Resource["Notes"]["Hold_Head"].height,
        note_max_width / Resource["Notes"]["Hold_Head_dub"].width * Resource["Notes"]["Hold_Head_dub"].height,
        note_max_width / Resource["Notes"]["Hold_End"].width * Resource["Notes"]["Hold_End"].height
    ))
    note_max_size_half = ((note_max_width ** 2 + note_max_height ** 2) ** 0.5) / 2
                
    shaders = {
        "chromatic": open("./shaders/chromatic.glsl", "r", encoding="utf-8").read(),
        "circleBlur": open("./shaders/circle_blur.glsl", "r", encoding="utf-8").read(),
        "fisheye": open("./shaders/fisheye.glsl", "r", encoding="utf-8").read(),
        "glitch": open("./shaders/glitch.glsl", "r", encoding="utf-8").read(),
        "grayscale": open("./shaders/grayscale.glsl", "r", encoding="utf-8").read(),
        "noise": open("./shaders/noise.glsl", "r", encoding="utf-8").read(),
        "pixel": open("./shaders/pixel.glsl", "r", encoding="utf-8").read(),
        "radialBlur": open("./shaders/radial_blur.glsl", "r", encoding="utf-8").read(),
        "shockwave": open("./shaders/shockwave.glsl", "r", encoding="utf-8").read(),
        "vignette": open("./shaders/vignette.glsl", "r", encoding="utf-8").read()
    }
    
    for line in chart_obj.lines:
        for note in line.notes:
            if note.hitsound_reskey not in Resource["Note_Click_Audio"]:
                try:
                    Resource["Note_Click_Audio"][note.hitsound_reskey] = dxsound.directSound(f"{temp_dir}/{note.hitsound}")
                    logging.info(f"Loaded note hitsound {note.hitsound}")
                except Exception as e:
                    logging.warning(f"Cannot load note hitsound {note.hitsound} for note due to {e}")
    
    if chart_obj.extra is not None:
        for effect in chart_obj.extra.effects:
            if effect.shader not in shaders.keys():
                try:
                    shaders[effect.shader] = utils.fixShader(open(f"{temp_dir}/{effect.shader}", "r", encoding="utf-8").read())
                    const.EXTRA_DEFAULTS[effect.shader] = utils.getShaderDefault(shaders[effect.shader])
                except Exception as e:
                    logging.warning(f"Cannot load shader {effect.shader} due to {e}")
        
        shadernames = list(set(effect.shader for effect in chart_obj.extra.effects))
        
        for name, glsl in shaders.items():
            if name not in shadernames: continue
            root.load_glsl(name, glsl)
    
    cksmanager = phicore.ClickSoundManager(Resource["Note_Click_Audio"])
    logging.info("Load Resource Successfully")
    return Resource

def WaitLoading_FadeIn():
    for i in range(100):
        WaitLoading.set_volume((i + 1) / 100)
        time.sleep(2 / 100)

def showStart():
    WaitLoading.fadeout(450)
    
    if not phicore.noanimation:
        def dle_warn(a: float):
            drawAlphaImage("le_warn", 0, 0, w, h, a, wait_execute=True)
        
        animationst = time.time()
        while time.time() - animationst < 1.0:
            clearCanvas(wait_execute=True)
            p = (time.time() - animationst) / 1.0
            dle_warn(1.0 - (1.0 - utils.fixorp(p)) ** 4)
            root.run_js_wait_code()
        
        time.sleep(0.35)
        
        animationst = time.time()
        while time.time() - animationst < 1.0:
            clearCanvas(wait_execute=True)
            phicore.drawBg()
            p = (time.time() - animationst) / 1.0
            dle_warn((utils.fixorp(p) - 1.0) ** 4)
            root.run_js_wait_code()
        
        time.sleep(0.25)
        clearCanvas(wait_execute=True)
        phicore.drawBg()
        root.run_js_wait_code()
        
    Thread(target=playerStart, daemon=True).start()

def checkOffset(now_t: float):
    global show_start_time
    
    dt = utils.checkOffset(now_t, raw_audio_length, mixer)
    if dt != 0.0:
        show_start_time += dt
        updateCoreConfig()

def playerStart():
    global show_start_time, cksmanager
    
    Resource["Over"].stop()
    
    LoadSuccess.play()
    phicore.loadingAnimation()
    phicore.lineOpenAnimation()

    show_start_time = time.time() - skip_time
    updateCoreConfig()
    now_t = 0
    
    if not render_video:
        mixer.music.play()
        mixer.music.set_pos(skip_time)
        while not mixer.music.get_busy(): pass
        
        if noautoplay:
            pplm_proxy = phichart.PPLMProxy_CommonChart(chart_obj)
            
            pppsm = utils.PhigrosPlayManager(chart_obj.note_num)
            pplm = utils.PhigrosPlayLogicManager(
                pplm_proxy, pppsm,
                enable_clicksound, lambda nt: Resource["Note_Click_Audio"][nt].play(),
                globalNoteWidth * const.MPBJUDGE_RANGE_X,
                w, h
            )
            
            convertTime2Chart = lambda t: (t - show_start_time) * speed - chart_obj.offset
            root.jsapi.set_attr("PhigrosPlay_KeyDown", lambda key: pplm.pc_click(convertTime2Chart(time.time()), key))
            root.jsapi.set_attr("PhigrosPlay_KeyUp", lambda key: pplm.pc_release(convertTime2Chart(time.time()), key))
            root.jsapi.set_attr("PhigrosPlay_TouchStart", lambda x, y, i: pplm.mob_touchstart(convertTime2Chart(time.time()), x / w, y / h, i))
            root.jsapi.set_attr("PhigrosPlay_TouchMove", lambda x, y, i: pplm.mob_touchmove(convertTime2Chart(time.time()), x / w, y / h, i))
            root.jsapi.set_attr("PhigrosPlay_TouchEnd", lambda i: pplm.mob_touchend(i))
            pplm.bind_events(root)
        else:
            pplm = None
            
        play_restart_flag = False
        pause_flag = False
        pause_st = float("nan")
        
        def _f(): nonlocal play_restart_flag; play_restart_flag = True
        
        @utils.runByThread
        def space():
            global show_start_time
            nonlocal pause_flag, pause_st
            
            if not pause_flag:
                pause_flag = True
                mixer.music.pause()
                Resource["Pause"].play()
                pause_st = time.time()
            else:
                mixer.music.unpause()
                show_start_time += time.time() - pause_st
                pause_flag = False
        
        choosing_dump = False
        @utils.runByThread
        def dumpChart():
            nonlocal choosing_dump
            if noautoplay or choosing_dump: return
            
            choosing_dump = True
            fn = dialog.savefile(fn="dump.bpc")
            choosing_dump = False
            if fn is None: return
            
            with open(fn, "wb") as f:
                f.write(chart_obj.dump())
                
        root.jsapi.set_attr("Noautoplay_Restart", _f)
        root.jsapi.set_attr("SpaceClicked", space)
        root.jsapi.set_attr("DumpChart", dumpChart)
        root.run_js_code("_Noautoplay_Restart = (e) => {if (e.altKey && e.ctrlKey && e.repeat && e.key.toLowerCase() == 'r') pywebview.api.call_attr('Noautoplay_Restart');};") # && e.repeat 为了判定长按
        root.run_js_code("_SpaceClicked = (e) => {if (e.key == ' ' && !e.repeat) pywebview.api.call_attr('SpaceClicked');};")
        root.run_js_code("_DumpChart = (e) => {if (e.altKey && e.ctrlKey && !e.repeat && e.key.toLowerCase() == 'd') pywebview.api.call_attr('DumpChart');};")
        root.run_js_code("window.addEventListener('keydown', _Noautoplay_Restart);")
        root.run_js_code("window.addEventListener('keydown', _SpaceClicked);")
        root.run_js_code("window.addEventListener('keydown', _DumpChart);")
        
        while True:
            while pause_flag: time.sleep(1 / 30)
            
            now_t = time.time() - show_start_time
            checkOffset(now_t)
            extasks = phicore.renderChart_Common(now_t, pplm=pplm)
            
            break_flag = phicore.processExTask(extasks)
            
            if break_flag:
                break
            
            if play_restart_flag:
                break
        
        if noautoplay:
            pplm.unbind_events(root)
        
        root.run_js_code("window.removeEventListener('keydown', _Noautoplay_Restart);")
        root.run_js_code("window.removeEventListener('keydown', _SpaceClicked);")
        
        if play_restart_flag:
            mixer.music.fadeout(250)
            loadChartObject()
            Thread(target=playerStart, daemon=True).start()
            return
        
    elif render_video: # eq else
        video_fp = sys.argv[sys.argv.index("--render-video-savefp") + 1] if "--render-video-savefp" in sys.argv else dialog.savefile(fn="render_video.mp4")
        
        if video_fp is None:
            root.destroy()
            return
        
        import cv2
        writer = cv2.VideoWriter(
            video_fp,
            cv2.VideoWriter.fourcc(*render_video_fourcc),
            render_video_fps,
            (w, h),
            True
        )
        needrelease.add(writer.release)
        
        def writeFrame(frames: list[bytes]):
            for data in frames:
                matlike = utils.bytes2matlike(data, w, h)
                writer.write(matlike)
        
        wcv2matlike.callback = writeFrame
        httpd, port = wcv2matlike.createServer()
        
        root.run_js_code(f"initUploadFrame({render_video_buffer_size}, 'http://127.0.0.1:{port}/');")
        
        now_t = 0.0
        while now_t < raw_audio_length + chart_obj.offset:
            extasks = phicore.renderChart_Common(now_t, None)
                
            root.wait_jspromise("uploadFrame();")
            now_t += 1 / render_video_fps
        
        root.wait_jspromise("upload_all_frames(true);")
        
        httpd.shutdown()
        writer.release()
        needrelease.remove(writer.release)
                
        if "--render-video-autoexit" in sys.argv:
            root.destroy()
            return
        
    else:
        assert False, "never"
    
    mixer.music.set_volume(1.0)
    phicore.initSettlementAnimation(pplm if noautoplay else None)
    
    def Chart_Finish_Animation():
        animation_1_time = 0.75
        a1_combo = pplm.ppps.getCombo() if noautoplay else None
        
        animation_1_start_time = time.time()
        while True:
            p = (time.time() - animation_1_start_time) / animation_1_time
            if p > 1.0: break
            phicore.lineCloseAimationFrame(p, a1_combo)
        
        time.sleep(0.25)
        Resource["Over"].play(-1)
    
        animation_2_time = 3.5
        animation_2_start_time = time.time()
        a2_loop_clicked = False
        a2_continue_clicked = False
        a2_break = False
        
        def whileCheck():
            nonlocal a2_break
            while True:
                if a2_loop_clicked or (loop and (time.time() - animation_2_start_time) > 0.25):
                    def _f():
                        loadChartObject()
                        playerStart()
                    Thread(target=_f, daemon=True).start()
                    break
                
                if a2_continue_clicked:
                    root.destroy()
                    break
                    
                time.sleep(1 / 240)
            
            root.run_js_code("window.removeEventListener('click', _loopClick);")
            root.run_js_code("window.removeEventListener('click', _continueClick);")
            a2_break = True
        
        Thread(target=whileCheck, daemon=True).start()
        
        def loopClick(clientX, clientY):
            nonlocal a2_loop_clicked
            if clientX <= w * const.FINISH_UI_BUTTON_SIZE and clientY <= w * const.FINISH_UI_BUTTON_SIZE / 190 * 145:
                a2_loop_clicked = True
        
        def continueClick(clientX, clientY):
            nonlocal a2_continue_clicked
            if clientX >= w - w * const.FINISH_UI_BUTTON_SIZE and clientY >= h - w * const.FINISH_UI_BUTTON_SIZE / 190 * 145:
                a2_continue_clicked = True
        
        root.jsapi.set_attr("loopClick", loopClick)
        root.jsapi.set_attr("continueClick", continueClick)
        root.run_js_code("_loopClick = (e) => {pywebview.api.call_attr('loopClick', e.clientX, e.clientY);}")
        root.run_js_code("_continueClick = (e) => {pywebview.api.call_attr('continueClick', e.clientX, e.clientY);}")
        root.run_js_code("window.addEventListener('click-np', _loopClick);")
        root.run_js_code("window.addEventListener('click-np', _continueClick);")
        
        while not a2_break:
            p = (time.time() - animation_2_start_time) / animation_2_time
            if p > 1.0: break
            phicore.settlementAnimationFrame(p)
        
        while not a2_break:
            phicore.settlementAnimationFrame(1.0)
    
    mixer.music.fadeout(250)
    Chart_Finish_Animation()

def updateCoreConfig():
    global PhiCoreConfigObject
    
    PhiCoreConfigObject = phicore.PhiCoreConfig(
        SETTER = lambda vn, vv: globals().update({vn: vv}),
        root = root, w = w, h = h,
        chart_information = chart_information,
        chart_obj = chart_obj,
        Resource = Resource,
        globalNoteWidth = globalNoteWidth,
        note_max_size_half = note_max_size_half,
        raw_audio_length = raw_audio_length,
        clickeffect_randomblock_roundn = clickeffect_randomblock_roundn,
        chart_res = chart_res,
        cksmanager = cksmanager,
        enable_clicksound = enable_clicksound, rtacc = rtacc,
        noautoplay = noautoplay, showfps = showfps,
        speed = speed, render_range_more = render_range_more,
        render_range_more_scale = render_range_more_scale,
        debug = debug, combotips = combotips, noplaychart = noplaychart,
        clicksound_volume = clicksound_volume,
        musicsound_volume = musicsound_volume
    )
    phicore.CoreConfigure(PhiCoreConfigObject)

logging.info("Loading Window...")
root = webcv.WebCanvas(
    width = 1, height = 1,
    x = -webcv.screen_width, y = -webcv.screen_height,
    title = "phispler - Simulator",
    debug = "--debug" in sys.argv,
    resizable = False,
    frameless = "--frameless" in sys.argv,
    renderdemand = renderdemand, renderasync = renderasync,
    jslog = "--enable-jslog" in sys.argv,
    jslog_path = sys.argv[sys.argv.index("--jslog-path")] if "--jslog-path" in sys.argv else "./ppr-jslog-nofmt.js"
)

def init():
    global webdpr
    global lowquality, lowquality_scale
    global w, h
    global Resource
    
    if webcv.disengage_webview:
        socket_webviewbridge.hook(root)

    w, h, webdpr, _, _ = root.init_window_size_and_position(0.6)
    
    webdpr = root.run_js_code("window.devicePixelRatio;")
    if webdpr != 1.0:
        lowquality = True
        lowquality_scale *= 1.0 / webdpr # ...?

    if lowquality:
        root.run_js_code(f"lowquality_scale = {lowquality_scale};")

    root.run_js_code(f"lowquality_imjscvscale_x = {lowquality_imjscvscale_x};")
    root.run_js_code(f"lowquality_imjs_maxsize = {lowquality_imjs_maxsize};")
    root.run_js_code(f"enable_jscanvas_bitmap = {enable_jscanvas_bitmap};")
    root.run_js_code(f"RPEVersion = {chart_obj.options.rpeVersion};")
    
    rw, rh = w, h
    if usu169:
        ratio = w / h
        if ratio > 16 / 9:
            w = int(h * 16 / 9)
        else:
            h = int(w / 16 * 9)
        root.run_js_code("usu169 = true;")
    root.run_js_code(f"resizeCanvas({rw}, {rh}, {{willReadFrequently: {render_video}}});")
        
    Resource = loadResource()

    if wl_more_chinese:
        root.run_js_code("setWlMoreChinese();")

    updateCoreConfig()

    Thread(target=showStart, daemon=True).start()
    root.wait_for_close()
    atexit_run()

def atexit_run():
    tempdir.clearTempDir()
    needrelease.run()
    exitfunc(0)

Thread(target=root.init, args=(init, ), daemon=True).start()
root.start()
atexit_run()
