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
from modterm.components.window_base import WindowBase


def display_help(screen, help_text_rows):
    help_window = WindowBase(screen, len(help_text_rows) + 5, 80, title=f"Help - {help_text_rows[0]}", added_border=True)
    help_window.draw_window()
    idx = 0
    for idx, row in enumerate(help_text_rows[1:], start=2):
        help_window.window.addstr(idx, 2, row)
    help_window.window.addstr(idx+1, 2, "")
    help_window.window.addstr(idx+2, 2, "Press ESC to dismiss help")
    help_window.window.refresh()
    x = screen.getch()
    while x != 27:
        x = screen.getch()
