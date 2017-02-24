from tkinter.messagebox import showwarning, showerror
import traceback
from typing import *


def __show_dialog(callback: Callable[[str, str], None],
                  msg: str,
                  title: str):
    callback(title, msg)


def error(msg: Union[str, Exception], title='Error'):
    if isinstance(msg, Exception):
        msg = traceback.format_exc()
    __show_dialog(showerror, msg, title)


def warning(msg: str, title='Warning'):
    __show_dialog(showwarning, msg, title)
