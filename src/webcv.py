from __future__ import annotations

import fix_workpath as _
import imageload_hook as _
import init_logging as _

import threading
import typing
import http.server
import io
import time
import socket
import sys
import logging
import platform
from os.path import abspath
from random import randint
from urllib.parse import urlparse

disengage_webview = "--disengage-webview" in sys.argv

if not disengage_webview: import webview
from PIL import Image

import graplib_webview
import utils

if not disengage_webview:
    from ctypes import windll
    screen_width = windll.user32.GetSystemMetrics(0)
    screen_height = windll.user32.GetSystemMetrics(1)
else:
    screen_width, screen_height = -1, -1

current_thread = threading.current_thread
host = socket.gethostbyname(socket.gethostname()) if "--nolocalhost" in sys.argv else "127.0.0.1"
logging.info(f"server host: {host}")

framerate_counter = '''\
(() => {

_frame_count = 0;
_frame_lastreftime = performance.now();
_framerate_ckeck_limit = 25;
framerate = -1;

_frame_counter = () => {
    _frame_count++;
    
    if (_frame_count >= _framerate_ckeck_limit) {
        const uset = performance.now() - _frame_lastreftime;
        framerate = uset != 0.0 ? _frame_count / (uset / 1000) : Infinity;
        _frame_count = 0;
        _frame_lastreftime = performance.now();
        
        if (framerate != Infinity) {
            _framerate_ckeck_limit = framerate * 0.25;
        }
    }
    
    requestAnimationFrame(_frame_counter);
}

requestAnimationFrame(_frame_counter);

})();
'''

def _parseRangeHeader(data: bytes, rg: typing.Optional[str], setrep_header: typing.Callable[[str, str], typing.Any]):
    if rg is None: return data
    start, end = rg.split("=")[1].split("-")
    start = int(start)
    end = int(end) if end else len(data) - 1
    start = min(max(start, 0), len(data) - 1)
    end = min(end, len(data) - 1)
    setrep_header("Content-Range", f"bytes {start}-{end}/{len(data)}")
    setrep_header("Content-Length", str(end - start + 1))
    return data[start:end+1]

def _img2bytes(im: Image.Image):
    try:
        from numpy import array as nparr
        from cv2 import imencode, cvtColor, COLOR_RGBA2BGRA
        return imencode(".png", cvtColor(nparr(im), COLOR_RGBA2BGRA))[1].tobytes()
    except (ImportError, ModuleNotFoundError):
        bio = io.BytesIO()
        im.save(bio, "png")
        return bio.getvalue()

type respacker_imtype = Image.Image|bytes|str|typing.Callable[[], respacker_imtype]

def _packerimg2bytes(im: respacker_imtype):
    if isinstance(im, Image.Image):
        if hasattr(im, "byteData"):
            return im.byteData
        else:
            return _img2bytes(im)
    elif isinstance(im, bytes):
        return im
    elif isinstance(im, str):
        return _packerimg2bytes(Image.open(im))
    elif isinstance(im, typing.Callable):
        return _packerimg2bytes(im())

class WebCanvas_FileServerHandler(http.server.BaseHTTPRequestHandler):
    _canvas: WebCanvas
    
    def do_GET(self):
        parsed = urlparse(self.path)
        
        if parsed.path[1:] in self._canvas._regims:
            im: Image.Image = self._canvas._regims[parsed.path[1:]]
            data = _packerimg2bytes(im)
            ctype = "image/png"
                
        elif parsed.path[1:] in self._canvas._regres or parsed.path[1:] in self._canvas._regres_cb:
            data = self._canvas._regres[parsed.path[1:]] if parsed.path[1:] in self._canvas._regres else self._canvas._regres_cb[parsed.path[1:]]()
            
            if parsed.path.endswith(".png"): ctype = "image/png"
            elif parsed.path.endswith(".js"): ctype = "application/javascript"
            elif parsed.path.endswith(".html"): ctype = "text/html"
            elif parsed.path.endswith(".css"): ctype = "text/css"
            elif parsed.path.endswith(".json"): ctype = "application/json"
            elif parsed.path.endswith(".ttf"): ctype = "font/ttf"
            elif parsed.path.endswith(".woff"): ctype = "font/woff"
            elif parsed.path.endswith(".woff2"): ctype = "font/woff2"
            elif parsed.path.endswith(".eot"): ctype = "font/eot"
            elif parsed.path.endswith(".svg"): ctype = "image/svg+xml"
            elif parsed.path.endswith(".ttc"): ctype = "font/ttc"
            elif parsed.path.endswith(".otf"): ctype = "font/otf"
            elif parsed.path.endswith(".xml"): ctype = "application/xml"
            elif parsed.path.endswith(".txt"): ctype = "text/plain"
            elif parsed.path.endswith(".ico"): ctype = "image/x-icon"
            elif parsed.path.endswith(".webp"): ctype = "image/webp"
            elif parsed.path.endswith(".mp4"): ctype = "video/mp4"
            elif parsed.path.endswith(".webm"): ctype = "video/webm"
            elif parsed.path.endswith(".ogg"): ctype = "video/ogg"
            elif parsed.path.endswith(".mp3"): ctype = "audio/mpeg"
            elif parsed.path.endswith(".wav"): ctype = "audio/wav"
            elif parsed.path.endswith(".flac"): ctype = "audio/flac"
            elif parsed.path.endswith(".aac"): ctype = "audio/aac"
            elif parsed.path.endswith(".avi"): ctype = "video/x-msvideo"
            elif parsed.path.endswith(".mov"): ctype = "video/quicktime"
            elif parsed.path.endswith(".mkv"): ctype = "video/x-matroska"
            else: ctype = "application/octet-stream"
        
        else:
            data = b"404 Not Found"
            ctype = "text/plain"
        
        rangeHeader = self.headers.get("Range")
        code = 206 if rangeHeader else 200
        self.send_response(code)
        self.send_header("Content-type", ctype)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "*")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")
        data = _parseRangeHeader(data, rangeHeader, self.send_header)
        self.end_headers()

        self.wfile.write(data)
    
    def log_request(self, *args, **kwargs) -> None: ...

class JsApi:
    def __init__(self) -> None:
        self.things: dict[str, typing.Any] = {}
    
    def get_thing(self, name: str):
        return self.things[name]
    
    def set_thing(self, name: str, value: typing.Any):
        self.things[name] = value
    
    def get_attr(self,name: str):
        return getattr(self, name)
    
    def set_attr(self, name: str, value: typing.Any):
        setattr(self, name, value)
    
    def call_attr(self, name: str, *args, **kwargs):
        try: func = getattr(self, name)
        except AttributeError:
            return logging.warning(f"JsApi: No such attribute '{name}'")
        return func(*args, **kwargs)
    
    @staticmethod
    def _socket_bridge_error(code: str, err: dict):
        raise Exception(f"SocketBridge: {err}")

class PILResPacker:
    def __init__(self, cv: WebCanvas):
        self.cv = cv
        self.imgs: list[tuple[str, respacker_imtype]] = []
        self._imgopted: dict[str, threading.Event] = {}
    
    def reg_img(self, img: respacker_imtype, name: str):
        self.imgs.append((name, img))
        
    def pack(self):
        datas = []
        dataindexs = []
        datacount = 0
        cache = {}
        for name, img in self.imgs:
            if id(img) in cache:
                data = cache[id(img)]
            else:
                data = _packerimg2bytes(img)
                cache[id(img)] = data
                
            datas.append(data)
            dataindexs.append([name, [datacount, len(data)]])
            datacount += len(data)
            
        return b"".join(datas), dataindexs

    def load(self, data: bytes, indexs: list[list[str, list[int, int]]]):
        rid = f"pilrespacker_{randint(0, 2 << 31)}"
        self.cv.reg_res(data, rid)
        imnames = self.cv.wait_jspromise(f"loadrespackage('{self.cv.get_resource_path(rid)}', {indexs});")
        self.cv.wait_loadimgs(self.cv.get_imgcomplete_jseval(imnames))
        self.cv.unreg_res(rid)
        self.cv.run_js_code(f"[{",".join(map(self.cv.get_img_jsvarname, imnames))}].forEach(im => URL.revokeObjectURL(im.src));")
        
        def optimize():
            codes = []
            codes.append(f"cachecv = document.createElement('canvas');")
            codes.append(f"cachecv.width = cachecv.height = 1;")
            codes.append(f"cachectx = cachecv.getContext('2d');")
            for im in imnames:
                codes.append(f"cachectx.drawImage({self.cv.get_img_jsvarname(im)}, 0, 0);")
            codes.append(f"delete cachecv; delete cachectx;")
            self.cv.run_js_code("".join(codes))
            
            for im in imnames:
                self._imgopted[im].set()
            
        self._imgopted.update({im: threading.Event() for im in imnames})
        threading.Thread(target=optimize, daemon=True).start()
    
    def getnames(self):
        return [name for name, _ in self.imgs]

    def unload(self, names: list[str]):
        codes = []
        
        for name in names:
            self._imgopted[name].wait()
            self._imgopted.pop(name)
            jvn = self.cv.get_img_jsvarname(name)
            codes.append(f"deleteLowQualityImage({jvn}); delete {jvn};")
            
        self.cv.run_js_code("".join(codes))

class LazyPILResPacker:
    def __init__(self, cv: WebCanvas):
        self.cv = cv
        self.imgs: dict[str, list[respacker_imtype]] = {}
        self._imgcache: dict[str, bytes] = {}
        self._loadcbs: dict[str, typing.Callable[[], bytes]] = {}
    
    def reg_img(self, img: respacker_imtype, name: str):
        if name not in self.imgs:
            self.imgs[name] = []
            
        self.imgs[name].append(img)
    
    def pack(self):
        return ()
    
    def _create_loadcb(self, name: str, index: int):
        def loadcb():
            key = (name, index)
            if key in self._imgcache:
                return self._imgcache[key]
            
            data = _packerimg2bytes(self.imgs[name][index])
            self._imgcache[key] = data
            return data
        
        return loadcb
    
    def load(self):
        imnames = self.getnames()
        loadcbs: dict[tuple[str, int], typing.Callable[[], bytes]] = {
            (name, index): self._create_loadcb(name, index)
            for name in imnames
            for index in range(len(self.imgs[name]))
        }
        codes = []
        
        for (name, index), cb in loadcbs.items():
            self.cv.reg_rescb(cb, f"lazy-{name}-{index}")
            jvn = self.cv.get_img_jsvarname(name)
            
            if index == 0:
                codes.append(f"{jvn} = new Image();")
                codes.append(f"{jvn}.setAttribute('crossOrigin', 'anonymous');")
            
            if index == len(self.imgs[name]) - 1:
                srcs = [self.cv.get_resource_path(f"lazy-{name}-{i}") for i in range(len(self.imgs[name]))]
                codes.append(f"{jvn}.enable_lazy_load({srcs});")
        
        self.cv.run_js_code("".join(codes))
        
        self._loadcbs.update(loadcbs)
    
    def getnames(self):
        return [name for name, _ in self.imgs.items()]
    
    def unload(self, names: list[str]):
        codes = []
        
        for name in names:
            for index in range(len(self.imgs[name])):
                self.cv.unreg_rescb(f"lazy-{name}-{index}")
                self._loadcbs.pop((name, index))
                
            jvn = self.cv.get_img_jsvarname(name)
            codes.append(f"deleteLowQualityImage({jvn}); delete {jvn};")
            
        self.cv.run_js_code("".join(codes))

if "--force-lazy-respacker" in sys.argv:
    PILResPacker = LazyPILResPacker

# def ban_threadtest_current_thread():
#     obj = current_thread()
#     obj.name = "MainThread"
#     return obj

# webview.threading.current_thread = ban_threadtest_current_thread

class WebCanvas:
    def __init__(
        self,
        width: int, height: int,
        x: int, y: int,
        debug: bool = False,
        title: str = "WebCanvas",
        resizable: bool = True,
        frameless: bool = False,
        html_path: str = "./web_canvas.html",
        renderdemand: bool = False,
        renderasync: bool = False,
        hidden: bool = False,
        jslog: bool = False,
        jslog_path: str = "./web_canvas.jslog.txt"
    ):
        self.jsapi = JsApi()
        self._destroyed = threading.Event()
        self._regims: dict[str, Image.Image] = {}
        self._regres: dict[str, bytes] = {}
        self._regres_cb: dict[str, typing.Callable[[], bytes]] = {}
        self._is_loadimg: dict[str, bool] = {}
        self._jscodes: list[str] = []
        self._framerate: int|float = -1
        self._jscode_orders: dict[int, list[tuple[str, bool]]] = {}
        
        self._rdevent = threading.Event()
        self._raevent = threading.Event()
        self.renderdemand = renderdemand
        self.renderasync = renderasync
        
        self.rwjc_waiter = threading.Event()
        self.rwjc_waiter.set()
        
        self.jslog = jslog
        self.jslog_path = jslog_path
        self.jslog_f = open(jslog_path, "w", encoding="utf-8") if self.jslog else None
        
        self.web = webview.create_window(
            title = title,
            url = abspath(html_path),
            resizable = resizable,
            js_api = self.jsapi,
            frameless = frameless,
            hidden = hidden
        ) if not disengage_webview else None
        self.evaljs = lambda x, *args, **kwargs: (self.web.evaluate_js(x) if not disengage_webview else None)
        self.init = lambda func: (self._init(width, height, x, y), func())
        self.start = lambda: webview.start(debug=debug) if not disengage_webview else time.sleep(60 * 60 * 24 * 7 * 4 * 12 * 80)
    
    def _init(self, width: int, height: int, x: int, y: int):
        if not disengage_webview:
            self.web.resize(width, height)
            self.web.move(x, y)
            self.web.events.closed += self._destroyed.set
            
            title = self.web.title
            temp_title = self.web.title + " " * randint(0, 4096)
            self.web.set_title(temp_title)
            
            self.web_hwnd = 0
            while not self.web_hwnd:
                self.web_hwnd = windll.user32.FindWindowW(None, temp_title)
                time.sleep(0.01)
            self.web.set_title(title)
        else:
            self.web_hwnd = -1
        
        self.fileserver_port = utils.getNewPort()
        WebCanvas_FileServerHandler._canvas = self
        self.file_server = http.server.HTTPServer(("", self.fileserver_port), WebCanvas_FileServerHandler)
        threading.Thread(target=self.file_server.serve_forever, daemon=True).start()
        
        self.jsapi.set_attr("_rdcallback", self._rdevent.set)
        self._raevent.set()
        
        graplib_webview.root = self
    
    def title(self, title: str) -> str: self.web.set_title(title) if not disengage_webview else None
    def winfo_hwnd(self) -> int: return self.web_hwnd
    def winfo_legacywindowwidth(self) -> int: return self.run_js_code("window.innerWidth;")
    def winfo_legacywindowheight(self) -> int: return self.run_js_code("window.innerHeight;")

    def destroy(self): self.web.destroy() if not disengage_webview else None
    def resize(self, width: int, height: int): self.web.resize(width, height) if not disengage_webview else None
    def move(self, x: int, y:int): self.web.move(x, y) if not disengage_webview else None
    def fullscreen(self): self.web.toggle_fullscreen() if not disengage_webview else None
    
    def run_js_code(self, code: str, wait_execute: bool = False, order: typing.Optional[int] = None, needresult: bool = True):
        if self.jslog and not code.endswith(";"): code += ";"
        
        if order is None:
            return self._jscodes.append(code) if wait_execute else self.evaljs(code, needresult)
        
        if order not in self._jscode_orders:
            self._jscode_orders[order] = []
        self._jscode_orders[order].append((code, wait_execute))
    
    def delete_img(self, imname: str):
        return self.run_js_code(f"delete window.{self.get_img_jsvarname(imname)};")
    
    def _rjwc(self, codes: list[str]):
        self.rwjc_waiter.wait()
        
        try:
            framerate: int|float = self.run_js_code(f"{codes}.forEach(r2eval);\nframerate;")
        except Exception as e:
            logging.error(f"has error in javascript code.")
            time.sleep(60 * 60 * 24 * 7 * 4 * 12 * 80)
        
        if self.renderdemand:
            self._rdevent.wait()
            self._rdevent.clear()
        
        self._framerate = framerate
        
        if self.renderasync:
            self._raevent.set()
    
    def run_jscode_orders(self):
        if self._jscode_orders:
            for _, i in sorted(self._jscode_orders.items(), key=lambda x: x[0]):
                for c, w in i: 
                    if w: self._jscodes.append(c)
                    else: self.run_js_code(c)
            self._jscode_orders.clear()
        
    def run_js_wait_code(self):
        if self._jscode_orders: self.run_jscode_orders() # not to create a new pyframe
        self.run_js_code("requestAnimationFrame(() => pywebview.api.call_attr('_rdcallback'));", wait_execute=True)
        self.run_js_code("if (!('_frame_counter' in window)) {&FRAMERATE_CODE&};".replace("&FRAMERATE_CODE&", framerate_counter), wait_execute=True)
        self.run_js_code("ctx.onframeok();", wait_execute=True)
        
        codes = self._jscodes.copy()
        self._jscodes.clear()
        
        if self.jslog:
            self.jslog_f.write("\n// JSCODE - FRAME - START //\n")
            self.jslog_f.writelines(codes)
            self.jslog_f.write("\n// JSCODE - FRAME - END //\n")
        
        if not self.renderasync:
            return self._rjwc(codes)
        else:
            self._raevent.wait()
            self._raevent.clear()
            threading.Thread(target=self._rjwc, args=(codes, ), daemon=True).start()
    
    def get_framerate(self) -> int|float: return self._framerate
    
    def get_img_jsvarname(self, imname: str):
        return f"{imname}_img"
    
    def reg_img(self, im: Image.Image, name: str) -> None:
        self._regims[name] = im
        self._is_loadimg[name] = False
    
    def reg_res(self, res_data: bytes, name: str) -> None:
        self._regres[name] = res_data
    
    def unreg_res(self, name: str) -> None:
        self._regres.pop(name)
    
    def reg_rescb(self, cb: typing.Callable[[], bytes], name: str) -> None:
        self._regres_cb[name] = cb
    
    def unreg_rescb(self, name: str) -> None:
        self._regres_cb.pop(name)
    
    def get_imgcomplete_jseval(self, ns: list[str]) -> str:
        return f"[{",".join([f"{self.get_img_jsvarname(item)}.complete" for item in ns])}]"
    
    def wait_loadimgs(self, complete_code: str) -> None:
        while not all(self.run_js_code(complete_code)):
            time.sleep(0.01)
        
    def reg_event(self, name: str, callback: typing.Callable) -> None:
        if disengage_webview: return
        setattr(self.web.events, name, getattr(self.web.events, name) + callback)
    
    def wait_for_close(self) -> None:
        while not self._destroyed.wait(0.1):
            pass
        
        if self.jslog:
            self.jslog_f.write(f"\n\n// Webview closed.\n")
            self.jslog_f.flush()
            self.jslog_f.close()
    
    def get_resource_path(self, name: str) -> str:
        return f"http://{host}:{self.fileserver_port}/{name}"

    def wait_jspromise(self, code: str) -> None:
        eid = f"wait_jspromise_{randint(0, 2 << 31)}"
        ete = threading.Event()
        ecbname = f"{eid}_callback"
        result = None
        
        def _callback(jsresult):
            nonlocal result
            result = jsresult
            ete.set()
            
        self.jsapi.set_attr(ecbname, _callback)
        self.run_js_code(f"eval({repr(code)}).then((result) => pywebview.api.call_attr('{ecbname}', result));")
        ete.wait()
        delattr(self.jsapi, ecbname)
        return result
    
    def init_window_size_and_position(
        self,
        scrsize: float,
        outscr_maxsize: float = 0.75
    ):
        webdpr = self.run_js_code("window.devicePixelRatio;")
        
        if disengage_webview:
            w, h = self.run_js_code("window.innerWidth;"), self.run_js_code("window.innerHeight;")
            
            dw_legacy, dh_legacy = 0, 0
        else:
            if "--window-host" in sys.argv and platform.system() == "Windows":
                from ctypes import windll
                windll.user32.SetParent(self.winfo_hwnd(), eval(sys.argv[sys.argv.index("--window-host") + 1]))
            
            if "--fullscreen" in sys.argv:
                w, h = screen_width, screen_height
                self.fullscreen()
            
                dw_legacy, dh_legacy = 0, 0
            else:
                if "--size" in sys.argv:
                    w, h = int(sys.argv[sys.argv.index("--size") + 1]), int(sys.argv[sys.argv.index("--size") + 2])
                else:
                    w, h = int(screen_width * scrsize), int(screen_height * scrsize)

                winw, winh = (
                    w if w <= screen_width else int(screen_width * outscr_maxsize),
                    h if h <= screen_height else int(screen_height * outscr_maxsize)
                )
                
                self.resize(winw, winh)
                
                w_legacy, h_legacy = self.winfo_legacywindowwidth(), self.winfo_legacywindowheight()
                dw_legacy, dh_legacy = winw - w_legacy, winh - h_legacy
                dw_legacy *= webdpr; dh_legacy *= webdpr
                dw_legacy = int(dw_legacy); dh_legacy = int(dh_legacy)
                self.resize(winw + dw_legacy, winh + dh_legacy)
                self.move(
                    int((screen_width - (winw + dw_legacy) / webdpr) / 2),
                    int((screen_height - (winh + dh_legacy) / webdpr) / 2)
                )
        
        w *= webdpr; h *= webdpr
        
        return w, h, webdpr, dw_legacy, dh_legacy
    
    def load_glsl(self, name: str, code: str):
        self.run_js_code(f"mainShaderLoader.load({repr(name)}, {repr(code)});")
        if (glerr := self.run_js_code("GLERR;")) is not None:
            logging.warning(f"Cannot compile shader {name} due to {glerr}")
        else:
            logging.info(f"Loaded shader {name}")
        
    def do_shader(self, name: str, values: dict, ctxname: str = "ctx"):
        self.run_js_code(
            f"mainShaderLoader.renderToCanvas({ctxname}, {repr(name)}, {repr(values)})",
            wait_execute = True
        )
    