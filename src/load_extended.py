import importlib.util
import platform
from sys import argv

if "--extended" in argv:
    ZH_T = "警告!!!"
    ZH_M = "你正在加载注入扩展功能,\n请确保你知道你在做什么和对注入的文件有足够的信任!\n如果你不确定, 请不要加载这个扩展!\n你确定要加载这个扩展吗?"
    
    EN_T = "Warning!!!"
    EN_M = "You are about to load the injection extension,\nplease make sure you know what you are doing and trust the file you are injecting!\nIf you are not sure, please do not load this extension!\nAre you sure you want to load this extension?"
    
    if platform.system() == "Windows":
        from ctypes import windll
        language = windll.kernel32.GetSystemDefaultUILanguage()
    else:
        language = 0x804

    T = ZH_T if language == 0x804 else EN_T
    M = ZH_M if language == 0x804 else EN_M
    
    if platform.system() == "Windows":
        from tkinter.messagebox import askokcancel
        result = askokcancel(title = T, message = M, default = "cancel", icon = "warning")
    else:
        result = "y" in input(f"{T}\n{M} (y/n): ").lower()
    
    if result:
        spec = importlib.util.spec_from_file_location("ppr-extended", argv[argv.index("--extended") + 1])
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
