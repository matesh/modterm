"""
ModTerm - Modbus analyser for the terminal

Copyright (C) 2023  Máté Szabó

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""

import curses
import textwrap
from curses.textpad import Textbox


class CancelInput(Exception):
    pass


def validate_text_edit_keys(keystroke):
    if keystroke == 127:
        return curses.KEY_BACKSPACE
    if keystroke == 27:
        raise CancelInput
    return keystroke


def get_text_input(window, width, y, x, default):
    number_entry = window.derwin(1, width, y, x)
    number_entry.clear()
    number_entry.addstr(str(default))
    tb = Textbox(number_entry, insert_mode=True)
    curses.curs_set(1)
    window.refresh()
    try:
        tb.edit(validate_text_edit_keys)
    except CancelInput:
        curses.curs_set(0)
        raise
    content = tb.gather().strip()
    curses.curs_set(0)
    return content


def validate_ip(s: str) -> bool:
    a = s.split('.')
    if len(a) != 4:
        return False
    for x in a:
        if not x.isdigit():
            return False
        i = int(x)
        if i < 0 or i > 255:
            return False
    return True


def wrap_text(text, width):
    return textwrap.fill(text, width)


def text_input_to_int(text):
    try:
        if text.startswith('0x'):
            return int(text, 16)
        return int(text, 10)
    except Exception:
        return None


def text_input_to_float(text):
    try:
        return float(text)
    except Exception:
        return None
