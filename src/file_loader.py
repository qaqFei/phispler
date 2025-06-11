import json
import logging
import typing
from dataclasses import dataclass

from PIL import Image

import utils
from dxsmixer import mixer

class FILE_TYPE:
    CHART: int = 1
    SONG: int = 2
    IMAGE: int = 3
    UNKNOW: int = 4

@dataclass
class LoadResult:
    filetype: typing.Literal[1, 2, 3, 4]
    data: typing.Any
    errs: typing.Optional[list[Exception]]

class FileLoadError(Exception): ...

def loadfile(fp: str):
    errs: list[Exception] = []
    
    try:
        return LoadResult(FILE_TYPE.IMAGE, Image.open(fp), None)
    except Exception as e:
        errs.append(e)
        
    try:
        mixer.music.load(fp)
        return LoadResult(FILE_TYPE.SONG, None, None)
    except Exception as e:
        errs.append(e)
    
    try:
        with open(fp, "r", encoding="utf-8") as f:
            raw = f.read()
            
            try: return LoadResult(FILE_TYPE.CHART, json.loads(raw), None)
            except Exception as e:
                errs.append(e)
            
                if isinstance(e, json.decoder.JSONDecodeError):
                    pec2rpeResult, p2r_errs = utils.pec2rpe(raw)
                    
                    for e in p2r_errs:
                        logging.warning(f"pec2rpe: {repr(e)}")
                    
                    for line in pec2rpeResult["judgeLineList"]:
                        for i, e in enumerate(line["eventLayers"][0]["speedEvents"]):
                            if i != len(line["eventLayers"][0]["speedEvents"]) - 1:
                                e["endTime"] = line["eventLayers"][0]["speedEvents"][i + 1]["startTime"]
                            else:
                                e["endTime"] = [e["startTime"][0] + 31250000, 0, 1]
                    
                    return LoadResult(FILE_TYPE.CHART, pec2rpeResult, None)
            
            raise FileLoadError("Unknown file type, load to text success, but decode to json failed.")
    except Exception as e:
        errs.append(e)
    
    return LoadResult(FILE_TYPE.UNKNOW, None, errs)

def choosefile(fns: typing.Iterable[str], prompt: str, failmsg: str = "请输入有效的数字", rawprocer: typing.Callable[[str], str] = lambda x: x, default: typing.Optional[str] = None) -> int:
    fns = list(fns)
    procerd = list(map(rawprocer, fns))
    
    if len(fns) == 1: return 0
    if default in procerd: return procerd.index(default)
    
    for i, fn in enumerate(procerd):
        print(f"{i + 1}. {fn}")

    while True:
        try:
            result = int(input(prompt)) - 1
            if not (0 <= result <= len(fns) - 1):
                raise ValueError
        except ValueError:
            print(f"{failmsg}\n")
        
        break
    
    return result
