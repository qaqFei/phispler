import time
import io

from pygame import mixer

mixer.init(channels = 32)

class directSound:
    def __init__(self, data: bytes|str, enable_cache: bool = True):
        if isinstance(data, str):
            with open(data, "rb") as f:
                data = f.read()
                
        self.sounds: list[tuple[mixer.Sound, float]] = [[mixer.Sound(io.BytesIO(data)), float("nan")] for _ in range(16)]
        self.length = self.sounds[0][0].get_length()
        
        for sound in self.sounds:
            sound[1] = time.time() - self.length
    
    def set_volume(self, v: float):
        for sound, _ in self.sounds:
            sound.set_volume(v)
    
    def play(self, wait: bool = False):
        vaild_sound = None
        
        for i, (sound, last_played) in enumerate(self.sounds):
            if time.time() - last_played > self.length:
                vaild_sound = sound
                self.sounds[i][1] = time.time()
                break
        
        if vaild_sound is None:
            vaild_sound = self.sounds[0][0]
            vaild_sound.stop()
            self.sounds[0][1] = time.time()
        
        vaild_sound.play()
