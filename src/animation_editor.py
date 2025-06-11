import fix_workpath as _

import sys
import typing
import base64
from tkinter.filedialog import askopenfilename, asksaveasfilename, askdirectory
from os.path import abspath, isfile, join as joinpath

import webview

loaded_resources: typing.Optional[dict] = None

class Jsapi:
    def render_click(self, cfg: dict):
        if not isfile(cfg["render_script"]):
            return {"code": 1, "msg": "Render script not found"}
        
        return {
            "code": 0, "msg": "all ready",
            "render_script": open(cfg["render_script"], "r").read()
        }
    
    def add_resources_click(self):
        file = askopenfilename(filetypes=[("Image Files", ["*.png", "*.jpg", "*.jpeg"]), ("All Files", "*.*")])
        if not file:
            return {"code": 2, "msg": "File not selected"}
        
        if not isfile(file):
            return {"code": 1, "msg": "File not found"}

        return {"code": 0, "msg": "all ready", "path": file}
    
    def load_resources_click(self, resources: dict):
        global loaded_resources
        
        if loaded_resources is not None:
            for i in loaded_resources:
                window.evaluate_js(f"delete {i["name"]};")
            
        for i in resources:
            window.evaluate_js(f"load_resource('{i["name"]}', 'data:image/png;base64,{base64.b64encode(open(i["path"], "rb").read()).decode()}');")
        
        loaded_resources = resources
    
    def export_click(self, cfg: dict):
        if cfg["render_method"] == "one_frame":
            file = asksaveasfilename(filetypes=[("Image Files", ["*.png", "*.jpg", "*.jpeg"]), ("All Files", "*.*")])
            if not file: return
            window.evaluate_js("render_noce();")
            with open(file, "wb") as f:
                f.write(getCanvasImage())
        else:
            directory = askdirectory()
            if not directory: return
            name_eval = window.evaluate_js("prompt('input name of file eval (frame num i: int):\\nlike this: f\"{i}.png\"');")
            if not name_eval:
                name_eval = "f\"{i}.png\""
            i = 0
            while True:
                t = i / cfg["multi_frame_fps"]
                if t > cfg["multi_frame_dur"]: break
                
                window.evaluate_js(f"render_noce({t / cfg["multi_frame_dur"]});")
                i += 1
                name = eval(name_eval)
                with open(joinpath(directory, name), "wb") as f:
                    f.write(getCanvasImage())
            
def getCanvasImage():
    dataurl: str = window.evaluate_js("getCanvasImage();")
    return base64.b64decode(dataurl.replace("data:image/png;base64,", "", 1))

def started_callback():
    if "--script" in sys.argv:
        window.evaluate_js(f"$(\"#render_script\").value = {repr(sys.argv[sys.argv.index("--script") + 1])}")

window = webview.create_window(
    title = "Animation Editor",
    url = abspath("./animation_editor.html"),
    js_api = Jsapi()
)

webview.start(started_callback, debug="--debug" in sys.argv)
