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


class WindowBase:
    def __init__(self, screen, height, width, y=None, x=None, title="", footer=""):
        self.width = width
        self.screen = screen
        self.height = height
        self.window = curses.newwin(self.height,
                                    self.width, 
                                    (screen.getmaxyx()[0] - self.height) // 2 if y is None else y,
                                    (screen.getmaxyx()[1] - self.width) // 2 if x is None else x)
        self.title = title
        self.footer = footer
        
    def draw_window(self):
        self.window.erase()
        self.window.border(0)
        self.window.box()
        if self.title != "":
            self.window.addstr(0, (self.window.getmaxyx()[1] - len(self.title)) // 2, f" {self.title} ")
        if self.footer != "":
            self.window.addstr(self.height-2, (self.window.getmaxyx()[1] - len(self.footer)) // 2, self.footer)
        self.window.refresh()
