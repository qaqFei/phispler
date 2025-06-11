import typing
import platform

REPO_URL = "https://github.com/qaqFei/phispler"

class NOTE_TYPE:
    TAP = 1
    DRAG = 2
    HOLD = 3
    FLICK = 4

class NOTE_JUDGE_RANGE:
    PERFECT = 0.08
    GOOD = 0.16
    BAD = 0.18
    MISS = 0.2

class NOTE_JUDGE_RANGE_CHALL:
    PERFECT = 0.04
    GOOD = 0.075
    BAD = 0.18
    MISS = 0.2

class NOTE_STATE:
    PERFECT = 1
    GOOD = 2
    BAD = 3
    MISS = 4

class PHIGROS_SETTING_STATE:
    PLAY = 1
    ACCOUNT_AND_COUNT = 2
    OTHER = 3

class OTHER_SETTING_LB_STRINGS:
    TWITTER = "@Phigros PGS"
    BILIBILI = "@Phigros官方"
    QQ = "鸽游网络@Phigros"
    GITHUB = "github@qaqFei"

class PHIGROS_LINKS:
    TWITTER = "https://twitter.com/Phigros_PGS"
    BILIBILI = "https://space.bilibili.com/414149787"
    QQ = "https://pd.qq.com/s/433r43ehu"
    GITHUB = REPO_URL
    PRIVACYPOLIC = "https://www.pigeongames.cn/news/2"

class PHI_SORTMETHOD:
    DEFAULT = 1
    SONG_NAME = 2
    DIFFICULTY = 3
    SCORE = 4

class CHART_RENDER_ORDERS:
    LINE = 0
    
    HOLD = 1
    FLICK = 2
    DRAG = 2
    TAP = 2
    
    DEBUG = 3

class LINEWIDTH:
    PHI = 0.0075
    RPE = 1 / 180

class SPEC_VALS:
    RES_NOLOADED = object()
    
TYPE_STRING_MAP = {
    NOTE_TYPE.TAP: "Tap",
    NOTE_TYPE.DRAG: "Drag",
    NOTE_TYPE.HOLD: "Hold",
    NOTE_TYPE.FLICK: "Flick"
}

NOTE_RORDER_MAP = {
    NOTE_TYPE.TAP: CHART_RENDER_ORDERS.TAP,
    NOTE_TYPE.DRAG: CHART_RENDER_ORDERS.DRAG,
    NOTE_TYPE.HOLD: CHART_RENDER_ORDERS.HOLD,
    NOTE_TYPE.FLICK: CHART_RENDER_ORDERS.FLICK
}

PHI_SORTMETHOD_STRING_MAP = {
    PHI_SORTMETHOD.DEFAULT: "默认",
    PHI_SORTMETHOD.SONG_NAME: "曲名",
    PHI_SORTMETHOD.DIFFICULTY: "难度",
    PHI_SORTMETHOD.SCORE: "成绩"
}

LEVEL_COLOR_MAP = {
    0: (16, 178, 47),
    1: (0, 117, 187),
    2: (207, 19, 19),
    3: (56, 56, 56)
}

LEVEL_CHOOSE_XMAP = {
    i: [(812 + (
        0, 150, 114, 99.5
    )[i] * j) / 1920 for j in range(i + 1)]
    for i in range(4)
}

LEVEL_CHOOSE_BLOCK_WIDTH = 0.0546875

LEVEL_BAR_END_XMAP = {
    i: (981 + sum(90 - j * 10 for j in range(i))) / 1920
    for i in range(4)
}

PGR_LEVEL_INTMAP = {
    "AP": 0, "FC": -1,
    "V": -2, "S": -3,
    "A": -4, "B": -5, "C": -6,
    "F": -7, "never_play": -8
}

DIFF_STRING_MAP = {
    0: "EZ", 1: "HD",
    2: "IN", 3: "AT"
}

MAX_LEVEL_NUM = 4

PPR_CMDARGS = {
    "args": [
        ("调试", "debug"),
        ("全屏", "fullscreen"),
        ("自动循环", "loop"),
        ("禁用点击音效", "noclicksound"),
        ("扩展渲染范围", "render-range-more"),
        ("窗口无边框", "frameless"),
        ("禁用自动游玩", "noautoplay"),
        ("启用实时准度", "rtacc"),
        ("低画质模式", "lowquality"),
        ("显示帧率", "showfps"),
        ("不播放谱面, 立即结算", "noplaychart"),
        ("替换文本为中文 (wl)", "wl-more-chinese"),
        ("使用 raf 限制帧率", "renderdemand"),
        ("异步渲染", "renderasync"),
        ("保留渲染的 JavaScript 代码", "enable-jslog"),
        ("启用 BitmapImage", "enable-jscanvas-bitmap"),
        ("降级音频API", "soundapi-downgrade"),
        ("不清理临时文件", "nocleartemp"),
        ("脱离 WebView", "disengage-webview"),
        ("禁用 localhost 作为内置服务器地址", "nolocalhost"),
        ("使用 16:9 的比例", "usu169"),
        ("渲染视频", "render-video"),
        ("渲染视频后自动退出", "render-video-autoexit"),
        ("不检查二进制文件", "nocheck-bin"),
        ("谱面镜像", "mirror"),
        ("禁用水印", "disable-watermark"),
        ("预生成打击音效", "prespwan-clicksound"),
        ("在 main 中不应用动画 (快速预览)", "noanimation"),
        ("应用演示模式鼠标", "presentation-arrow"),
        ("强制懒加载资源", "force-lazy-respacker")
    ],
    "kwargs": [
        ("连击提示文本", "combotips", "AUTOPLAY", "string"),
        ("打击特效随机块数量", "random-block-num", 4, "int"),
        ("设置音符缩放", "scale-note", 1.0, "float"),
        ("设置窗口大小 (如: \"1920 1080\")", "size", None, "string-nowarp"),
        ("设置渲染范围更多的缩放", "render-range-more-scale", 2.0, "float"),
        ("设置窗口宿主 (hwnd)", "window-host", None, "int"),
        ("设置低画质渲染缩放", "lowquality-scale", 2.0, "float"),
        ("设置资源路径", "res", None, "path-dir"),
        ("设置谱面速度", "speed", 1.0, "float"),
        ("设置打击特效方块的圆角系数", "clickeffect-randomblock-roundn", 0.0, "float"),
        ("设置打击音效音量", "clicksound-volume", 1.0, "float"),
        ("设置音乐音量", "musicsound-volume", 1.0, "float"),
        ("设置低画质渲染缩放 (js调用层)", "lowquality-imjscvscale-x", 1.0, "float"),
        ("使用 phira 谱面 (id)", "phira-chart", None, "int"),
        ("保存 phira 谱面路径", "phira-chart-save", None, "path"),
        ("播放时跳过的时间", "skip-time", 0.0, "float"),
        ("设置 渲染JavaScript 代码输出路径", "jslog-path", None, "path"),
        ("设置低画质渲染最大尺寸 (js调用层)", "lowquality-imjs-maxsize", 256, "int"),
        ("设置 rpe 谱面纹理缩放方法", "rpe-texture-scalemethod", "by-width", "choice", ["by-width", "by-height"]),
        ("扩展", "extended", None, "path"),
        ("设置渲染视频的帧率", "render-video-fps", 60.0, "float"),
        ("设置生成视频编码", "render-video-fourcc", "mp4v", "string"),
        ("设置渲染视频的保存路径", "render-video-savefp", None, "path"),
        ("手动指定 rpe 谱面版本", "rpeversion", None, "int"),
        ("渲染视频缓存帧大小", "render-video-buffer-size", 45, "int"),
        ("加载 bpc 二进制谱面", "load-bpc", None, "path"),
    ]
}
        
INF = float("inf")
NAN = float("nan")
JUDGELINE_PERFECT_COLOR = "#feffa9"
RENDER_RANGE_MORE_FRAME_LINE_COLOR = "rgba(0, 94, 255, 0.65)"
PHIGROS_VERSION = "NULL"
DEVICE = platform.platform()
OTHERSERTTING_RIGHTDOWN_TEXT = "@2024-2025 qaqFei. All right Reserverd."
FINISH_UI_BUTTON_SIZE = 0.10625
JOINQQGUILDPROMO_DIAGONALRECTANGLEPOWER = 127 / 975
CHAPTER_DIAGONALRECTANGLEDEG = -75
RPE_WIDTH = 1350
RPE_HEIGHT = 900
PGR_UW = 0.05625
PGR_UH = 0.6
FLOAT_LESSZERO_MAGIC = -1 / 1024
CSOUND_MANAGER_THREADNUM = 1
INFBEAT = 1e9
ALL_LETTER = "qwertyuiopasdfghjklzxcvbnm"
BASE_PORT = 16384
MAX_PORT = 65535
PGR_INF = 999999.0
MIRROR_ICON_LEFT = 1 / 5.72
EMPTY_RECT = (-1.0, -1.0, -1.0, -1.0)
USERNAME_CONST_FONT = 70
MPBJUDGE_RANGE_X = 1.35
NOTE_DEFAULTSIZE = 0.1234375
ClickEffectType = list[tuple[
    float,
    tuple[tuple[float, ...]],
    tuple[
        typing.Callable[[int, int], tuple[float, float]],
        float
    ]
]]
BadEffectType = list[tuple[float, float, tuple[float, float]]]
# MissEffectType = list[tuple[float, typing.Any]]

DSP_SETTING_TIP = """\
如果你在游戏中遇到游戏中的音乐无法正常播放的情况，请适当的更改这个设置。\n
在游戏中，更小的 Buffer 可以带来更低的音频延时，但同时会导致某些设备出现音频撕裂、音频嘈杂且缓慢，音频卡顿等问题。\n
如果你遇到了上述问题，请将这个值调整至可以让音频正常播放的最小值。可以通过播放下方的示例音频来测试音频能否正常播放。\n
由于技术性原因，此页面可能无法生效。
"""

PHI_OPENSOURCELICENSE = """\
MIT License

Copyright (c) 2024 qaq_fei

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

PHI_ABOUTUSTEXT = """\
Original Director / 原作
    
Soullies（Liu Wen） 
“
作为《Phigros》的作者，我将在此——

感谢 Pigeon Games 的所有成员，是大家无私的精诚合作造就了《Phigros》这一奇迹。

感谢所有给予过 Pigeon Games 帮助的组织与公司，我们非常荣幸能够得到你们的关心和支持。

感谢一直以来支持着《Phigros》的所有玩家，你们的每一次关注，每一个赞许，以及每一条意见，都深刻地影响了这份企划。

更重要的是，感谢此时此刻正在看着这块屏幕的——

你。

As the author of Phigros, I would like to—

Appreciate all the members of PigeonGames. It is our selflessness, sincerity, and cooperation that  has created this miracle.

Appreciate all the organizations and companies that helped PigeonGames. We are very honored to receive your attention and support.

Appreciate all the players who always have been supporting Phigros. Your attention, compliment, and advice have profoundly influenced our project.

More importantly, appreciate the person who is staring at the screen unblinkingly at the moment—

YOU.
”

Producer / 制作人
CN_115（杜锐）
“愿这款游戏也能被留在你的记忆中。”

Director / 策划
Barbarianerman（李茂昌）
“Phigros从发布之初逐步成长，在这段时间内我们得到了无数玩家的鼓励与支持，我在这里对各位表示诚挚的感谢。希望Phigros能够带给各位欢乐，并成为各位心中一份美好的象征。”

Leaders / 部门负责人

Programming / 程序组
CN_115（杜锐）
月下樱（李天勤）
“我们在Phigros中使用了一些有趣的技术，也在各种细节上做出了大胆的尝试，希望能给各位玩家带来更好的体验。同时我们也会不断优化，让Phigros变得更好！”

Chart Design / 谱师组
阿爽（周锐）
“希望大家可以喜欢我们的脑洞（划掉）！”

Illustration / 美术组
喵n葵（刘贝瑜）
“虽然是鸽游美术组，却是最不咕咕的组。一直感谢各位组员的爆肝（？）付出！我们会继续绘制精美的曲绘的！”

Visual & UI Design / 视觉 & UI 设计组
V17AMax（马煜）
“Phigros一路走来，我们各方面的制作水平一直在不断提升，这一点大家有目共睹。视觉设计组仍会尽力给大家带来更多惊喜！”

Music / 音乐组
姜米條（青杰）
“我是姜米條，是 Pigeon Games 的曲师组长，感谢大家支持 Phigros，同时也希望大家喜欢我们游戏的原创音乐。我们会在之后的更新里添加我们制作的音乐！”

Plots Design / 剧情组
DeathMark（赵芫华）
“只要有你们在，名为phigros的奇迹就是不可磨灭的，未来种种，山河表里，大浪凌空，险阻艰难，锦绣衰隆，我们一起度过。”

Advertising / 宣传组
SparkFred_17（周泓怿）
“愿鸽游给大家创造无限快乐，在未来我们一起努力、共同进步，成为每个人心中多彩的世界！”

Pigeon Animation Team / 动画组
汉堡（覃瀚钰）
“感谢各位和我们一起见证Phigros的成长（磕头），不要的显卡统统可以到我这换不锈钢脸盆。”

External Communications / 外部联络
Ctymax
“主要负责了版权商务相关大大小小的事宜，尽可能为玩家们搜罗来优质的音乐与美术作品。希望大家喜欢！”

--------------------------------
关于 phispler 项目 ({%REPO_URL%}),

phispler 使用MIT协议进行开源喵！！

鸣谢
星空孤雁 (Introduction 谱面谱师)
""" \
.replace("{%REPO_URL%}", REPO_URL)

PHIGROS_SETTING_BAR_WIDTH_MAP = {
    PHIGROS_SETTING_STATE.PLAY: 0.465625,
    PHIGROS_SETTING_STATE.ACCOUNT_AND_COUNT: 0.8265625,
    PHIGROS_SETTING_STATE.OTHER: 0.8265625
}
PHIGROS_SETTING_LABEL_WIDTH_MAP = {
    PHIGROS_SETTING_STATE.PLAY: 0.1,
    PHIGROS_SETTING_STATE.ACCOUNT_AND_COUNT: 0.146875,
    PHIGROS_SETTING_STATE.OTHER: 0.1
}
PHIGROS_SETTING_LABEL_X_MAP = {
    PHIGROS_SETTING_STATE.PLAY: 0.1609375,
    PHIGROS_SETTING_STATE.ACCOUNT_AND_COUNT: 0.25625,
    PHIGROS_SETTING_STATE.OTHER: 0.3984375
}
PHIGROS_SETTING_SHADOW_XRECT_MAP = {
    PHIGROS_SETTING_STATE.PLAY: (-0.3328125, 0.615625),
    PHIGROS_SETTING_STATE.ACCOUNT_AND_COUNT: (0.0265625, 0.975),
    PHIGROS_SETTING_STATE.OTHER: (0.0265625, 0.975),
}

EXTRA_DEFAULTS: dict[str, dict[str, float|list[float]]] = {
    "chromatic": {
        "sampleCount": 3,
        "power": 0.01
    },
    "circleBlur": {
        "size": 10.0
    },
    "fisheye": {
        "power": -0.1
    },
    "glitch": {
        "power": 0.3,
        "rate": 0.6,
        "speed": 5.0,
        "blockCount": 30.5,
        "colorRate": 0.01
    },
    "grayscale": {
        "factor": 1.0
    },
    "noise": {
        "seed": 81.0,
        "power": 0.03
    },
    "pixel": {
        "size": 10.0
    },
    "radialBlur": {
        "centerX": 0.5,
        "centerY": 0.5,
        "power": 0.01,
        "sampleCount": 3,
    },
    "shockwave": {
        "progress": 0.2,
        "centerX": 0.5,
        "centerY": 0.5,
        "width": 0.1,
        "distortion": 0.8,
        "expand": 10.0
    },
    "vignette": {
        "color": [0, 0, 0, 1],
        "extend": 0.25,
        "radius": 15.0
    }
}

PGR_PARTICLE_DATA = {
    "spwanTime": 0.015,
    "speedCurves": [
        {
            "time": 0,
            "value": 0,
            "inSlope": 2.1999998,
            "outSlope": 2.1999998,
            "inWeight": 0.33333334,
            "outWeight": 0.1764706
        },
        {
            "time": 1,
            "value": 1,
            "inSlope": 0,
            "outSlope": 0,
            "inWeight": 0.33333334,
            "outWeight": 0.33333334
        }
    ],
    "sizeCurves": [
        {
            "time": 0,
            "value": 0.49884492,
            "inSlope": 1.6398785,
            "outSlope": 1.6398785,
            "inWeight": 0.33333334,
            "outWeight": 0.1764706
        },
        {
            "time": 1,
            "value": 0.6941143,
            "inSlope": -1.0415096,
            "outSlope": -1.0415096,
            "inWeight": 0.25980395,
            "outWeight": 0.33333334
        }
    ],
    "startSize": 0.3
}

del typing, platform
