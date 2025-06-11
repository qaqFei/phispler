import sys
import threading

def excepthook(etype, value, tb):
    # will be fast to load this module
    import traceback
    import time
    import os.path
    import platform
    
    import needrelease
    from exitfunc import exitfunc
    
    try:
        needrelease.run()
        
        if isinstance(etype, KeyboardInterrupt) or KeyboardInterrupt in etype.mro():
            print("^C")
            exitfunc(0)
        
        errortext = "".join(traceback.format_exception(etype, value, tb))
        errorfile = f"error_{time.time()}.txt"
        
        with open(errorfile, "w", encoding="utf-8") as f:
            f.write(errortext)
        print(errortext, end="")
        
        if platform.system() == "Windows":
            from ctypes import windll
            windll.user32.MessageBoxW(
                0, f"很抱歉, phispler 发生了错误\n已生成错误文件到: {os.path.abspath(errorfile)}\n请将错误文件发送给开发者以获得帮助\nhttps://github.com/qaqFei/phispler\n\n\n{errortext}",
                "phispler 发生错误", 0x00000010 | 0x00010000
            )
            
        exitfunc(0)
    except (Exception, KeyboardInterrupt) as e:
        print(e)
        exitfunc(0)

sys.excepthook = excepthook
threading.excepthook = lambda x: excepthook(x.exc_type, x.exc_value, x.exc_traceback)
