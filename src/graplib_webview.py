from __future__ import annotations

import typing

import webcv

root: webcv.WebCanvas

transparent = "rgba(0, 0, 0, 0)"
number = int|float
ctx: str = "ctx"
order: typing.Optional[int] = None

def setCtx(n: str):
    global ctx
    ctx = n

def getCtx() -> str:
    return ctx

def setOrder(n: typing.Optional[int]):
    global order
    order = n
    
def getOrder():
    return order

def ctxSave(wait_execute: bool = False):
    root.run_js_code(f"{ctx}.save();", wait_execute, order)

def ctxRestore(wait_execute: bool = False):
    root.run_js_code(f"{ctx}.restore();", wait_execute, order)

def ctxTranslate(x: number, y: number, wait_execute: bool = False):
    root.run_js_code(f"{ctx}.translate({x}, {y});", wait_execute, order)

def ctxScale(x: number, y: number, wait_execute: bool = False):
    root.run_js_code(f"{ctx}.scale({x}, {y});", wait_execute, order)

def ctxRect(
    x: number, y: number,
    width: number, height: number,
    wait_execute: bool = False
):
    root.run_js_code(f"{ctx}.rect({x}, {y}, {width}, {height});", wait_execute, order)

def ctxBeginPath(wait_execute: bool = False):
    root.run_js_code(f"{ctx}.beginPath();", wait_execute, order)

def ctxClip(rule: str = "nonzero", wait_execute: bool = False):
    root.run_js_code(f"{ctx}.clip('{rule}');", wait_execute, order)

def ctxSetTransform(a: number, b: number, c: number, d: number, e: number, f: number, wait_execute: bool = False):
    root.run_js_code(f"{ctx}.setTransform({a}, {b}, {c}, {d}, {e}, {f});", wait_execute, order)

def ctxResetTransform(wait_execute: bool = False):
    root.run_js_code(f"{ctx}.resetTransform();", wait_execute, order)

def ctxSetGlobalAlpha(alpha: number, wait_execute: bool = False):
    root.run_js_code(f"{ctx}.globalAlpha = {alpha};", wait_execute, order)

def ctxMutGlobalAlpha(alpha: number, wait_execute: bool = False):
    root.run_js_code(f"{ctx}.globalAlpha *= {alpha};", wait_execute, order)

def ctxSetFilter(filter: str, wait_execute: bool = False):
    root.run_js_code(f"{ctx}.filter = '{filter}';", wait_execute, order)

def clearCanvas(wait_execute: bool = False):
    root.run_js_code(f"{ctx}.clear();", wait_execute, order)
    
def drawLine(
    x0: number, y0: number,
    x1: number, y1: number,
    lineWidth: number = 1,
    strokeStyle: str = transparent,
    wait_execute: bool = False
):
    code = []
    code.append(f"{ctx}.save();")
    code.append(f"{ctx}.lineWidth = {lineWidth};")
    code.append(f"{ctx}.strokeStyle = '{strokeStyle}';")
    code.append(f"{ctx}.beginPath();")
    code.append(f"{ctx}.moveTo({x0}, {y0});")
    code.append(f"{ctx}.lineTo({x1}, {y1});")
    code.append(f"{ctx}.stroke();")
    code.append(f"{ctx}.restore();")
    root.run_js_code("".join(code), wait_execute, order)

def drawText(
    x: number, y: number,
    text: str, font: typing.Optional[str] = None,
    textAlign: typing.Literal["start", "end", "left", "right", "center"] = "left",
    textBaseline: typing.Literal["top", "hanging", "middle", "alphabetic", "ideographic", "bottom"] = "middle",
    fillStyle: str = transparent,
    strokeStyle: str = transparent,
    method: typing.Literal["fill", "stroke"] = "fill",
    maxwidth: typing.Optional[number] = None,
    wait_execute: bool = False
):
    text = repr(text)
    code = []
    code.append(f"{ctx}.save();")
    code.append(f"{ctx}.font = '{font}';") if font is not None else None
    code.append(f"{ctx}.textAlign = '{textAlign}';")
    code.append(f"{ctx}.textBaseline = '{textBaseline}';")
    code.append(f"{ctx}.fillStyle = '{fillStyle}';") if method == "fill" else None
    code.append(f"{ctx}.strokeStyle = '{strokeStyle}';") if method == "stroke" else None
    code.append(f"{ctx}.{method}Text({text}, {x}, {y}, {maxwidth if maxwidth is not None else "undefined"});")
    code.append(f"{ctx}.restore();")
    root.run_js_code("".join(code), wait_execute, order)

def doPolygon(
    points: typing.Iterable[tuple[number, number]],
    wait_execute: bool = False
):
    code = []
    code.append(f"{ctx}.moveTo({points[0][0]}, {points[0][1]});")
    code.extend(f"{ctx}.lineTo({x}, {y});" for x, y in points[1:])
    root.run_js_code("".join(code), wait_execute, order)

def drawPolygon(
    points: typing.Iterable[tuple[number, number]],
    fillStyle: str = transparent,
    strokeStyle: str = transparent,
    lineWidth: number = 1,
    method: typing.Literal["fill", "stroke"] = "fill",
    wait_execute: bool = False
):
    code = []
    code.append(f"{ctx}.save();")
    code.append(f"{ctx}.fillStyle = '{fillStyle}';") if method == "fill" else None
    code.append(f"{ctx}.strokeStyle = '{strokeStyle}';") if method == "stroke" else None
    code.append(f"{ctx}.lineWidth = {lineWidth};")
    code.append(f"{ctx}.beginPath();")
    root.run_js_code("".join(code), wait_execute, order)
    
    doPolygon(points, wait_execute)
    
    code = []
    code.append(f"{ctx}.fill();") if method == "fill" else None
    code.append(f"{ctx}.stroke();") if method == "stroke" else None
    code.append(f"{ctx}.restore();")
    root.run_js_code("".join(code), wait_execute, order)

def drawImage(
    imname: str,
    x: number, y: number,
    width: number, height: number,
    wait_execute: bool = False
):
    jvn = root.get_img_jsvarname(imname)
    root.run_js_code(f"{ctx}.drawImage({jvn}, {x}, {y}, {width}, {height});", wait_execute, order)

def drawCoverFullScreenImage(
    imname: str,
    w: number, h: number,
    x: number = 0, y: number = 0,
    wait_execute: bool = False
):
    # fullscreen?
    
    jvn = root.get_img_jsvarname(imname)
    root.run_js_code(f"{ctx}.drawCoverFullScreenImage({jvn}, {w}, {h}, {x}, {y});", wait_execute, order)

def drawAlphaImage(
    imname: str,
    x: number, y: number,
    width: number, height: number,
    alpha: number,
    wait_execute: bool = False
):
    jvn = root.get_img_jsvarname(imname)
    root.run_js_code(f"{ctx}.drawAlphaImage({jvn}, {x}, {y}, {width}, {height}, {alpha});", wait_execute, order)
    return x, y, width, height

def drawMirrorImage(
    imname: str,
    x: number, y: number,
    width: number, height: number,
    alpha: number,
    wait_execute: bool = False
):
    jvn = root.get_img_jsvarname(imname)
    root.run_js_code(f"{ctx}.drawMirrorImage({jvn}, {x}, {y}, {width}, {height}, {alpha});", wait_execute, order)

def drawMirrorRotateImage(
    imname: str,
    x: number, y: number,
    width: number, height: number,
    deg: number, alpha: number,
    wait_execute: bool = False
):
    jvn = root.get_img_jsvarname(imname)
    root.run_js_code(f"{ctx}.drawMirrorRotateImage({jvn}, {x}, {y}, {width}, {height}, {deg}, {alpha});", wait_execute, order)

def drawRotateImage(
    imname: str,
    x: number, y: number,
    width: number, height: number,
    deg: number, alpha: number,
    wait_execute: bool = False
):
    jvn = root.get_img_jsvarname(imname)
    root.run_js_code(f"{ctx}.drawRotateImage({jvn}, {x}, {y}, {width}, {height}, {deg}, {alpha});", wait_execute, order)

def addRoundRectData(
    x: number, y: number,
    w: number, h: number,
    r: number,
    wait_execute: bool = False
):
    root.run_js_code(f"{ctx}.addRoundRectData({x}, {y}, {w}, {h}, {r});", wait_execute, order)

def drawRoundDatas(color: str, wait_execute: bool = False):
    root.run_js_code(f"{ctx}.drawRoundDatas('{color}');", wait_execute, order)

def outOfTransformDrawCoverFullscreenChartBackgroundImage(imname: str, wait_execute: bool = False):
    jvn = root.get_img_jsvarname(imname)
    root.run_js_code(f"{ctx}.outOfTransformDrawCoverFullscreenChartBackgroundImage({jvn});", wait_execute, order)
    
def fillRectEx(
    x: number, y: number,
    w: number, h: number,
    color: str,
    wait_execute: bool = False
):
    root.run_js_code(f"{ctx}.fillRectEx({x}, {y}, {w}, {h}, '{color}');", wait_execute, order)

def strokeRectEx(
    x: number, y: number,
    w: number, h: number,
    color: str,
    lineWidth: number = 1,
    wait_execute: bool = False
):
    root.run_js_code(f"{ctx}.strokeRectEx({x}, {y}, {w}, {h}, '{color}', {lineWidth});", wait_execute, order)

def drawCircle(
    center: tuple[number, number],
    width: number,
    r: number,
    fillStyle: str,
    wait_execute: bool = False
):
    code = []
    code.append(f"{ctx}.save();")
    code.append(f"{ctx}.strokeStyle = '{fillStyle}';")
    code.append(f"{ctx}.beginPath();")
    code.append(f"{ctx}.lineWidth = {width};")
    code.append(f"{ctx}.arc({center[0]}, {center[1]}, {r}, 0, 2 * Math.PI);")
    code.append(f"{ctx}.stroke();")
    code.append(f"{ctx}.restore();")
    root.run_js_code("".join(code), wait_execute, order)

class ColorMultiplyFilter:
    def __init__(self, color: tuple[number, number, number], jsorder: int = None):
        self.color = color
        self.jsorder = jsorder
    
    def __enter__(self):
        if self.color == (255, 255, 255):
            return
        
        root.run_js_code(
            f"setColorMatrix{tuple(map(lambda x: x / 255, self.color))}; {ctx}.filter = 'url(#textureLineColorFilter)';",
            wait_execute=True, order=self.jsorder
        )
    
    def __exit__(self, *_):
        if self.color == (255, 255, 255):
            return
        
        root.run_js_code(
            "ctx.filter = 'none';",
            wait_execute=True, order=self.jsorder
        )
