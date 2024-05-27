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


help_text_rows = [
    "",
    "Quit application: F10",
    "Top menu items: F keys as indicated",
    "",
    "Register operations",
    "r - Read registers",
    "w - Write registers",
    "s - Sweep modbus units with register reads",
    "e - Export register data"
    # "i - Sweep IP addresses with register reads",
]

def display_help(screen):
    help_window = WindowBase(screen, 20, 80, title="Help")
    help_window.draw_window()
    for idx, row in enumerate(help_text_rows, start=1):
        help_window.window.addstr(idx, 2, row)
    help_window.window.refresh()
    x = screen.getch()
    while x != 27:
        x = screen.getch()
