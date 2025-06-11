import platform

if platform.system() == "Windows":
    import fix_workpath as _
    import init_logging as _
    
    import tkinter.messagebox
    import logging
    from os import system

    import webview.platforms.winforms

    if webview.platforms.winforms.renderer != "edgechromium":
        logging.info("Edge WebView2 Runtime is not installed")
        tkinter.messagebox.showerror("错误", "请使用EdgeChromium渲染器\n关闭此对话框后将启动安装程序")
        system(".\\ecwv_installer.exe /silent /install")
        if webview.platforms.winforms._is_chromium():
            webview.platforms.winforms.renderer = "edgechromium"
        else:
            tkinter.messagebox.showwarning("警告", "EdgeChromium渲染器安装失败或取消")
