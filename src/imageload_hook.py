import io
import typing

from PIL import Image

_open = Image.open

def _isio(obj: typing.Any):
    return hasattr(obj, "read") and hasattr(obj, "seek")

class ImageProxy(Image.Image):
    def __init__(self, creater: typing.Callable[[], Image.Image]):
        self._creater = creater
        self._obj = None
    
    def __getattribute__(self, item):
        if item in ("_obj", "__call__", "_creater"):
            return object.__getattribute__(self, item)
        
        return getattr(self(), item)
    
    def __setattr__(self, key, value):
        if key in ("_obj", "__call__", "_creater"):
            return object.__setattr__(self, key, value)

        return setattr(self(), key, value)
    
    def __call__(self):
        if self._obj is None:
            self._obj = self._creater()
        
        return self._obj

def inner_open_hook(*args, **kwargs):
    args = list(args)
    
    if _isio(args[0]):
        byteData = args[0].read()
        args[0] = io.BytesIO(byteData)
        
    elif isinstance(args[0], str):
        with open(args[0], "rb") as f:
            byteData = f.read()
            args[0] = io.BytesIO(byteData)
            
    elif isinstance(args[0], bytes):
        byteData = args[0]
        args[0] = io.BytesIO(byteData)
    
    else:
        raise TypeError(f"Unsupported type for image loading: {type(args[0])}")

    im = _open(*args, **kwargs)
    im.byteData = byteData
    return im

def open_hook(*args, **kwargs):
    return ImageProxy(lambda: inner_open_hook(*args, **kwargs))

# open_hook 调用时如果不是图片文件不会报错。。
Image.open = inner_open_hook
