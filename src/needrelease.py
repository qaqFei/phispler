import typing
import logging

needs: list[typing.Callable[[], typing.Any]] = []

def add(func: typing.Callable[[], typing.Any]) -> None:
    needs.append(func)

def remove(func: typing.Callable[[], typing.Any]) -> None:
    try: needs.remove(func)
    except ValueError: pass

def run() -> None:
    try:
        for func in needs.copy():
            remove(func)
            func()
    except Exception as e:
        logging.error(f"Error while running needrelease: {repr(e)}")
