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
from curses.textpad import Textbox


def validate_text_edit_keys(keystroke):
    if keystroke == 127:
        return curses.KEY_BACKSPACE
    return keystroke


def get_text_input(window, width, y, x, default):
    number_entry = window.derwin(1, width, y, x)
    number_entry.clear()
    number_entry.addstr(str(default))
    tb = Textbox(number_entry, insert_mode=True)
    curses.curs_set(1)
    window.refresh()
    tb.edit(validate_text_edit_keys)
    content = tb.gather().strip()
    curses.curs_set(0)
    return content
