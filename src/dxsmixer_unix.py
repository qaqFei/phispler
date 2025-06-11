def toDowngradeAPI():
    import typing
    from os import environ; environ["PYGAME_HIDE_SUPPORT_PROMPT"] = ""
    from threading import Lock
    
    from pygame import mixer as _mixer
    
    _mixer.init(channels = 32)
    mixer = _mixer
    
    length = -1
    _load = mixer.music.load
    _get_pos = mixer.music.get_pos
    
    def _loadhook(fn: str, needlength: bool = True):
        nonlocal length
        
        length = _mixer.Sound(fn).get_length() if needlength else -1.0
        _load(fn)
        
    mixer.music.load = _loadhook
    mixer.music.get_length = lambda: length
    mixer.music.get_pos = lambda: _get_pos() / 1000
    
    apis = {
        "unload": mixer.music.unload,
        "load": mixer.music.load,
        "get_length": mixer.music.get_length,
        "set_pos": mixer.music.set_pos,
        "get_pos": mixer.music.get_pos,
        "play": mixer.music.play,
        "stop": mixer.music.stop,
        "pause": mixer.music.pause,
        "unpause": mixer.music.unpause,
        "set_volume": mixer.music.set_volume,
        "get_volume": mixer.music.get_volume,
        "set_endevent": mixer.music.set_endevent,
        "get_endevent": mixer.music.get_endevent,
        "get_busy": mixer.music.get_busy,
        "fadeout": mixer.music.fadeout
    }
    
    # Segmentation fault: 你好
    mixer_lock = Lock()
    
    def apilock(fn: typing.Callable):
        def wrapper(*args, **kwargs):
            with mixer_lock:
                return fn(*args, **kwargs)
        return wrapper

    for name, fn in apis.items():
        setattr(mixer.music, name, apilock(fn))
    
    return mixer

type musicCls = object
mixer = toDowngradeAPI()
