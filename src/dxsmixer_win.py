from __future__ import annotations

import typing
import time
from sys import argv

import dxsound
import utils

class musicCls:
    def __init__(self):
        self.dxs = None
        self.buffer = None
        
        self._lflag = 0
        self._volume = 1.0
        
        self._paused = False
        self._pause_pos = 0
        self._pause_volume = 0.0
    
    def _setBufferVolume(self, v: float):
        if self.buffer is None: return
        self.buffer.SetVolume(self.dxs.transform_volume(v))
     
    def _getBufferPosition(self) -> int:
        if self.buffer is None: return 0
        return self.buffer.GetCurrentPosition()[1]
    
    def _setBufferPosition(self, v: int):
        if self.buffer is None: return
        minv = 0
        maxv = self.dxs._sdesc.dwBufferBytes - 1
        self.buffer.SetCurrentPosition(min(max(minv, v), maxv))
    
    def load(self, fp: str):
        new_dxs = dxsound.directSound(fp, enable_cache=False)
        self.unload()
        self.dxs = new_dxs
        
    def unload(self):
        self.dxs = None
        self.buffer = None
        self._paused = False
        
    def play(self, isloop: typing.Literal[0, -1] = 0):
        self.lflag = 0 if isloop == 0 else 1
        
        if self.buffer is None:
            _, self.buffer = self.dxs.create(self.lflag)
            self._setBufferVolume(self._volume)
            
        else:
            self.set_pos(0.0)
            self.buffer.Play(self.lflag)
        
    def stop(self):
        self.buffer = None
        
    def pause(self):
        if self._paused: return
        self._paused = True
        
        self._pause_pos = self._getBufferPosition()
        self._pause_volume = self.get_volume()
        self._setBufferVolume(0.0)
        
    def unpause(self):
        # if not self._paused: return
        
        if not self._paused:
            self._pause_pos = self._getBufferPosition()
            
        self._paused = False
        
        self.buffer.Play(self.lflag)
        self._setBufferVolume(self._pause_volume)            
        self._setBufferPosition(self._pause_pos)
    
    @utils.runByThread
    def fadeout(self, t: int):
        if self._paused: return
        
        t /= 1000
        st = time.time()
        bufid = id(self.buffer)
        rvol = self.get_volume()
        
        while (
            time.time() - st < t
            and self.buffer is not None
            and self.get_busy()
        ):
            if id(self.buffer) != bufid:
                self.set_volume(rvol)
                return
                
            p = (time.time() - st) / t
            p = max(0.0, min(1.0, p))
            self.set_volume(1.0 - p)
            time.sleep(1 / 15)
        
        self.stop()
        self.set_volume(rvol)
    
    def set_volume(self, volume: float):
        self._volume = volume
        self._setBufferVolume(volume)
        
    def get_volume(self):
        return self._volume
    
    def get_busy(self) -> bool:
        return self.buffer is not None and (self.buffer.GetStatus() != 0 and not self._paused)
    
    def set_pos(self, pos: float):
        bufpos = int(pos * self.dxs._sdesc.lpwfxFormat.nAvgBytesPerSec)
        self._setBufferPosition(bufpos)
        self._pause_pos = bufpos
        
    def get_pos(self) -> float:
        return (self._getBufferPosition() if not self._paused else self._pause_pos) / self.dxs._sdesc.lpwfxFormat.nAvgBytesPerSec
    
    def get_length(self) -> float:
        return self.dxs._sdesc.dwBufferBytes / self.dxs._sdesc.lpwfxFormat.nAvgBytesPerSec
    
class mixerCls:
    def __init__(self):
        self.music = musicCls()
        
    def init(*args, **kwargs) -> None: ...
    
    def Sound(self, fp: str):
        music = musicCls()
        music.load(fp)
        return music

def toDowngradeAPI():
    global mixer
    import dxsmixer_unix
    mixer = dxsmixer_unix.mixer
    
mixer = mixerCls()

if "--soundapi-downgrade" in argv:
    toDowngradeAPI()
