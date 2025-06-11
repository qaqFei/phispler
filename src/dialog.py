import platform
import typing

if platform.system() == "Windows":
    import win32ui

    def _base_dialog(
        bFileOpen: bool,
        Filter: str = "",
        fn: str = ""
    ) -> str:
        dlg = win32ui.CreateFileDialog(
            bFileOpen,
            None,
            fn,
            0,
            Filter
        )
        dlg.DoModal()
        result = dlg.GetPathName()
        return result if result != fn else None
else:
    def _base_dialog(
        bFileOpen: bool,
        Filter: str = "",
        fn: str = ""
    ) -> str:
        return input(f"Enter file path (isopen: {bFileOpen}, filter: {Filter}, fn: {fn}): ")

def openfile(**kwargs) -> typing.Optional[str]:
    return _base_dialog(True, **kwargs)

def savefile(**kwargs) -> typing.Optional[str]:
    return _base_dialog(False, **kwargs)
