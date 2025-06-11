import fix_workpath as _

import ctypes
import tkinter
import tkinter.ttk
from tkinter.filedialog import askopenfilename, askdirectory
from tkinter.messagebox import showerror
from os import popen
from os.path import exists, isfile, isdir
from sys import executable

from const import PPR_CMDARGS

if exists("./main.py") and isfile("./main.py"):
    target_path = f"\"phispler\" \"{executable}\" ./main.py"
elif exists("./main.exe") and isfile("./main.exe"):
    target_path = "./main.exe"
else:
    print("Can't find main.py or main.exe.")
    raise SystemExit

def hook_dropfiles_first(hwnd, callback):
    globals()[f"hook_dropfiles_dropfunc_prototype_{hwnd}"] = ctypes.WINFUNCTYPE(*(ctypes.c_uint64,) * 5)(lambda hwnd,msg,wp,lp: [callback([ctypes.windll.shell32.DragQueryFileW(ctypes.c_uint64(wp),0,szFile := ctypes.create_unicode_buffer(260),ctypes.sizeof(szFile)),szFile.value][1]) if msg == 0x233 else None,ctypes.windll.user32.CallWindowProcW(*map(ctypes.c_uint64,(lptr,hwnd,msg,wp,lp)))][1]);ctypes.windll.shell32.DragAcceptFiles(hwnd,True);lptr = ctypes.windll.user32.GetWindowLongPtrA(hwnd,-4);ctypes.windll.user32.SetWindowLongPtrA(hwnd,-4,globals()[f"hook_dropfiles_dropfunc_prototype_{hwnd}"])

def openfile_callback(widget: tkinter.Entry):
    fp = askopenfilename(parent=root, title="选择文件")
    if fp == "":
        return
    
    if not (exists(fp) and isfile(fp)):
        showerror(title="错误", message="选择的文件不存在或不为文件")
    
    widget.delete(0, "end")
    widget.insert(0, fp)

def opendir_callback(widget: tkinter.Entry):
    dp = askdirectory(parent=root, title="选择文件夹")
    if dp == "":
        return

    if not exists(dp):
        showerror(title="错误", message="选择的文件夹不存在")

    widget.delete(0, "end")
    widget.insert(0, dp)

def launch():
    launch_args = []
    nowarp_args = []
    chartfp = file_input_entry.get()
    
    if exists(chartfp):
        launch_args.append(chartfp)
    else:
        showerror(title="错误", message="谱面文件不存在或不为文件")
        return
    
    for var, arg in zip(arg_widgets, PPR_CMDARGS["args"]):
        if var.get():
            launch_args.append(f"--{arg[1]}")

    for entry, kwarg in zip(kwarg_widgets, PPR_CMDARGS["kwargs"]):
        userinput = entry.get()
        isnoawrp = False
        if not userinput: continue
        match kwarg[3]:
            case "int":
                try: userinput = int(float(userinput))
                except ValueError:
                    showerror(title="错误", message=f"参数 {kwarg[1]} 的值应为整数")
                    return
            
            case "float":
                try: userinput = float(userinput)
                except ValueError:
                    showerror(title="错误", message=f"参数 {kwarg[1]} 的值应为浮点数")
                    return

            case "string":
                pass
            
            case "string-nowarp":
                isnoawrp = True
            
            case "path":
                if not (exists(userinput) or isfile(userinput)):
                    showerror(title="错误", message=f"参数 {kwarg[1]} 的值应为存在的文件")
                    return
            
            case "path-dir":
                if not (exists(userinput) or isdir(userinput)):
                    showerror(title="错误", message=f"参数 {kwarg[1]} 的值应为存在的文件夹")
                    return
            
            case "choice":
                if userinput not in kwarg[4]:
                    showerror(title="错误", message=f"参数 {kwarg[1]} 的值应为以下之一: {kwarg[4]}")
                    return
                
        if userinput != kwarg[2]:
            if isnoawrp:
                nowarp_args.append(f"--{kwarg[1]}")
                nowarp_args.append(f"{userinput}")
            else:
                launch_args.append(f"--{kwarg[1]}")
                launch_args.append(f"{userinput}")
    
    command = "start " + target_path + " " + " ".join(map(lambda x: f"\"{x}\"", launch_args)) + " " + " ".join(nowarp_args)
    print(command)
    popen(command)
    
root = tkinter.Tk()
root.withdraw()
root.title("phispler Launcher")
root.iconbitmap("icon.ico")
root.resizable(False, False)
screen_width, screen_height = root.winfo_screenwidth(), root.winfo_screenheight()
file_input_label = tkinter.Label(root, text="谱面文件: ")
file_input_label.grid(row=0, column=0, columnspan=100, padx=12, sticky="w")
file_input_entry = tkinter.ttk.Entry(root, width=int(screen_width / 35))
file_input_entry.grid(row=0, column=101, columnspan=100, sticky="w")
file_input_filedialog_button = tkinter.ttk.Button(root, text="选择", command=lambda: openfile_callback(file_input_entry))
file_input_filedialog_button.grid(row=0, column=202, sticky="w")

arg_widgets = []
kwarg_widgets = []

arg_canvas = tkinter.Canvas(root)
arg_sbary = tkinter.ttk.Scrollbar(root, orient="vertical", command=arg_canvas.yview)
arg_sbarx = tkinter.ttk.Scrollbar(root, orient="horizontal", command=arg_canvas.xview)
arg_canvas.configure(yscrollcommand=arg_sbary.set)
arg_canvas.configure(xscrollcommand=arg_sbarx.set)

arg_frame = tkinter.Frame(arg_canvas)
arg_canvas.create_window((0, 0), window=arg_frame, anchor="nw")

for index, data in enumerate(PPR_CMDARGS["args"]):
    var = tkinter.BooleanVar()
    var.set(False)
    checkbut = tkinter.ttk.Checkbutton(arg_frame, text=data[0], variable=var)
    checkbut.grid(row=index, column=0, sticky="w")
    arg_widgets.append(var)

arg_frame.update_idletasks()
arg_canvas.configure(scrollregion=arg_canvas.bbox("all"))

arg_canvas.grid(row=1, column=0, columnspan=3000, sticky="nw")
arg_sbary.grid(row=1, column=3001, sticky="ns")
arg_sbarx.grid(row=2, column=0, columnspan=1000, sticky="ew")
arg_canvas.bind("<MouseWheel>", lambda e: arg_canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
arg_canvas.bind("<Shift-MouseWheel>", lambda e: arg_canvas.xview_scroll(int(-1*(e.delta/120)), "units"))

kwarg_canvas = tkinter.Canvas(root, width=root.winfo_width())
kwarg_sbary = tkinter.ttk.Scrollbar(root, orient="vertical", command=kwarg_canvas.yview)
kwarg_sbarx = tkinter.ttk.Scrollbar(root, orient="horizontal", command=kwarg_canvas.xview)
kwarg_canvas.configure(yscrollcommand=kwarg_sbary.set)
kwarg_canvas.configure(xscrollcommand=kwarg_sbarx.set)

kwarg_frame = tkinter.Frame(kwarg_canvas)
kwarg_canvas.create_window((0, 0), window=kwarg_frame, anchor="nw")

for i, data in enumerate(PPR_CMDARGS["kwargs"]):
    label = tkinter.Label(kwarg_frame, text=f"{data[0]} ({data[3]}): ")
    label.grid(row=i, column=0, sticky="w")
    match data[3]:
        case "int" | "float" | "string" | "string-nowarp":
            entry = tkinter.Entry(kwarg_frame)
            entry.grid(row=i, column=1, sticky="w")
            kwarg_widgets.append(entry)
            if data[2] is not None:
                entry.insert(0, str(data[2]))
        case "path":
            entry = tkinter.Entry(kwarg_frame)
            entry.grid(row=i, column=1, sticky="w")
            button = tkinter.ttk.Button(kwarg_frame, text="浏览", command=lambda entry=entry: openfile_callback(entry))
            button.grid(row=i, column=2, sticky="w")
            kwarg_widgets.append(entry)
        case "path-dir":
            entry = tkinter.Entry(kwarg_frame)
            entry.grid(row=i, column=1, sticky="w")
            button = tkinter.ttk.Button(kwarg_frame, text="浏览", command=lambda entry=entry: opendir_callback(entry))
            button.grid(row=i, column=2, sticky="w")
            kwarg_widgets.append(entry)
        case "choice":
            entry = tkinter.ttk.Combobox(kwarg_frame, values=data[4])
            entry.grid(row=i, column=1, sticky="w")
            kwarg_widgets.append(entry)
            entry.current(0)

kwarg_frame.update_idletasks()
kwarg_canvas.configure(scrollregion=kwarg_canvas.bbox("all"))

kwarg_canvas.grid(row=3, column=2, columnspan=3000, sticky="nw")
kwarg_sbary.grid(row=3, column=3001, sticky="ns")
kwarg_sbarx.grid(row=4, column=2, columnspan=1000, sticky="ew")
kwarg_canvas.bind("<MouseWheel>", lambda e: kwarg_canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
kwarg_canvas.bind("<Shift-MouseWheel>", lambda e: kwarg_canvas.xview_scroll(int(-1*(e.delta/120)), "units"))

launchButton = tkinter.ttk.Button(root, text="启动", command=launch)
launchButton.grid(row=5, column=0, columnspan=5000, padx=12, pady=5, sticky="w")

root.deiconify()
root.update()
arg_frame["width"] = root.winfo_width()
kwarg_frame["width"] = root.winfo_width()
arg_canvas["width"] = root.winfo_width()
kwarg_canvas["width"] = root.winfo_width()
hook_dropfiles_first(root.winfo_id(), lambda file:([file_input_entry.delete(0, "end"),file_input_entry.insert(0, file)] if isfile(file) else None))
root.mainloop()
