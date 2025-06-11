from ctypes import util as _ctypes_util

_registered: dict[str, str] = {}

_raw_find_library = _ctypes_util.find_library
def find_library(name: str):
    if (ret := _registered.get(name)) is not None:
        return ret
    
    return _raw_find_library(name)

_ctypes_util.find_library = find_library

def register(name: str, path: str):
    _registered[name] = path

def unregister(name: str):
    _registered.pop(name, None)
