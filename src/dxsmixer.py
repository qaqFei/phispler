import platform

if platform.system() == "Windows":
    from dxsmixer_win import *
else:
    from dxsmixer_unix import *
