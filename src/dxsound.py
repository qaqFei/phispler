import platform

if platform.system() == "Windows":
    from dxsound_win import *
else:
    from dxsound_unix import *
