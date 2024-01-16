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
    def __init__(self, screen, height, width, y=None, x=None, title="", footer="", min_height=None, min_width=None):
        max_height = screen.getmaxyx()[0]
        max_width = screen.getmaxyx()[1]
        width = width if width < max_width else max_width - 2
        height = height if height < max_height else max_height - 2
        if (min_height is not None and width < min_width) or (min_height is not None and height < min_height):
            self.is_valid = False
            window = curses.newwin(max_height,
                                   max_width,
                                   0,
                                   0)
            window.erase()
            window.border(0)
            window.box()
            try:
                window.addstr(1, 2, "Terminal window is too small to draw interface")
                window.refresh()
            except Exception as e:
                pass
            curses.napms(1500)
            return
        self.is_valid = True
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
        if self.title != "" and len(self.title) < self.width:
            self.window.addstr(0, (self.window.getmaxyx()[1] - len(self.title)) // 2, f" {self.title} ")
        if self.footer != "" and len(self.footer) < self.width:
            self.window.addstr(self.height-2, (self.window.getmaxyx()[1] - len(self.footer)) // 2, self.footer)
        self.window.refresh()
