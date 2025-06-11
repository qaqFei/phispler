import numpy as np
from pydub import AudioSegment

FR, SW, CH = 44100, 2, 2

def normalize(seg: AudioSegment):
    if seg.channels != CH: seg = seg.set_channels(CH)
    if seg.frame_rate != FR: seg = seg.set_frame_rate(FR)
    if seg.sample_width != SW: seg = seg.set_sample_width(SW)
    return seg

def seg2arr(seg: AudioSegment):
    return np.array(normalize(seg).get_array_of_samples()).astype(np.int32)
        
class AudioMixer:
    def __init__(self, base: AudioSegment):
        self.data = seg2arr(base)
        self.cachemap: dict[int, np.ndarray] = {}
    
    def mix(self, seg: AudioSegment, pos: float):
        if id(seg) in self.cachemap:
            arr = self.cachemap[id(seg)]
        else:
            arr = seg2arr(seg)
            self.cachemap[id(seg)] = arr
            
        start_pos = int(pos * FR * CH)
        end_pos = start_pos + len(arr)
        
        if end_pos > len(self.data):
            arr = arr[:len(self.data) - start_pos]
        
        if start_pos < 0:
            arr = arr[-start_pos:]
            start_pos = 0
        
        try:
            self.data[start_pos:end_pos] += arr
        except ValueError:
            pass
    
    def get(self):
        return AudioSegment(
            data=self.data.clip(-32768, 32767).astype(np.int16).tobytes(),
            sample_width=SW,
            frame_rate=FR,
            channels=CH
        )
