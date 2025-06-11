import platform

if platform.system() == "Windows":
    from ctypes import windll
    exitfunc = windll.kernel32.ExitProcess
else:
    import os
    exitfunc = os._exit
