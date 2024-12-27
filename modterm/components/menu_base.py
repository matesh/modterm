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

from typing import Optional
import curses
from functools import partial
from textwrap import wrap
from abc import abstractmethod
from modterm.components.window_base import WindowBase
from modterm.components.definitions import TableContents
from modterm.components.help import display_help


class MenuBase:
    def __init__(self, screen, normal_text, highlighted_text, menu_labels, config_values, interfaces, menu_name):
        self.menu_labels = menu_labels
        self.menu_name = menu_name
        self.config_values = config_values
        self.interfaces = interfaces
        self.dialog = None
        self.is_valid = None
        self.max_status_index = None
        self.screen = screen
        self.screen_size = self.screen.getmaxyx()
        self.reset_window()
        self.normal_text = normal_text
        self.highlighted_text = highlighted_text
        self.start_status_index = max(self.menu_labels.keys()) + 2
        self.status_index = self.start_status_index
        self.failed_action = False

        self.position = max(self.menu_labels.keys())

        self.keymap = {
            curses.KEY_UP: partial(self.jump_to, offset=-1),
            curses.KEY_DOWN: partial(self.jump_to, offset=1),
            curses.KEY_HOME: partial(self.jump_to, position=min(self.menu_labels.keys())),
            curses.KEY_PPAGE: partial(self.jump_to, position=min(self.menu_labels.keys())),
            curses.KEY_END: partial(self.jump_to, position=max(self.menu_labels.keys())),
            curses.KEY_NPAGE: partial(self.jump_to, position=max(self.menu_labels.keys())),
            curses.KEY_F2: partial(self.jump_to, position=2, execute=True),
            curses.KEY_F3: partial(self.jump_to, position=3, execute=True),
            curses.KEY_F4: partial(self.jump_to, position=4, execute=True),
            curses.KEY_F5: partial(self.jump_to, position=5, execute=True),
            curses.KEY_F6: partial(self.jump_to, position=6, execute=True),
            curses.KEY_F7: partial(self.jump_to, position=7, execute=True),
            curses.KEY_F8: partial(self.jump_to, position=8, execute=True),
            curses.KEY_F9: partial(self.jump_to, position=9, execute=True),
            curses.KEY_F1: self.help}

        self.help_text_rows = [
            f"{menu_name}"]
        self.help_text_rows.extend(wrap(f"Using the common navigation or indicated F keys, navigate to the "
                                        "desired option. Press enter to edit a setting value or start the "
                                        "operation. Press del or backspace on a setting to clear and edit it "
                                        "Upon all transactions being successful, you will be returned to the "
                                        "main screen. Upon any unsuccessful operation, you will be offered to "
                                        "retry or return to the main screen. Numeric inputs understand hexadecimal"
                                        "as well, start the hex number with the 0x prefix", 76))

    def reset_window(self):
        width = 100 if 102 < self.screen.getmaxyx()[1] else self.screen.getmaxyx()[1] - 2
        height = 30 if 32 < self.screen.getmaxyx()[0] else self.screen.getmaxyx()[0] - 2
        self.dialog = WindowBase(self.screen, height, width, title=self.menu_name, min_width=40, min_height=15, added_border=True)
        self.is_valid = self.dialog.is_valid
        if not self.is_valid:
            return
        self.max_status_index = height - 2

    def jump_to(self, position=None, offset=None, execute=False):
        if position is None and offset is None:
            return
        if offset is None:
            if position not in self.menu_labels:
                return
            if position == max(self.menu_labels.keys()) and execute:
                return
            self.position = position
            if execute:
                self.draw()
                self.interfaces[self.position]()
            return
        else:
            if self.position + offset not in self.menu_labels.keys():
                return
            self.position = self.position + offset

    def help(self):
        display_help(self.screen, self.help_text_rows)

    def draw(self, no_highlight=False):
        self.dialog.draw_window()
        for position, label in self.menu_labels.items():
            value_prop = str(self.config_values[position])
            value = str(getattr(self.configuration, value_prop)) if len(value_prop) > 0 else ""
            if len(value) == 0 and self.position == position:
                self.dialog.window.addstr(position, 2, label, self.normal_text if no_highlight else self.highlighted_text)
            else:
                self.dialog.window.addstr(position, 2, label, self.normal_text)

            if self.position == position and position != max(self.menu_labels.keys()):
                self.dialog.window.addstr(position, 2 + len(label), value,
                                          self.normal_text if no_highlight else self.highlighted_text)
            else:
                self.dialog.window.addstr(position, 2 + len(label), value, self.normal_text)
        self.dialog.window.refresh()

    def add_status_text(self, text, failed=False, highlighted=False):
        if failed:
            self.failed_action = True
        text_lines = wrap(text, self.dialog.width - 4)
        if len(text_lines) == 0:
            text_lines = [""]
        if self.status_index + len(text_lines) > self.dialog.height - 2:
            self.dialog.window.clear()
            self.draw(True)
            self.status_index = self.start_status_index
        for idx, line in enumerate(text_lines):
            if idx == 0:
                self.dialog.window.addstr(self.status_index, 2, line, self.normal_text if not highlighted else self.highlighted_text)
            else:
                self.dialog.window.addstr(self.status_index, 2, "    " + line, self.normal_text if not highlighted else self.highlighted_text)
            self.status_index += 1
            self.dialog.window.refresh()

    def get_result(self) -> Optional[TableContents]:
        self.draw()
        x = self.screen.getch()
        while x != 27:
            if x in self.keymap:
                self.keymap[x]()
            elif x == ord('\n'):
                if self.position != max(self.menu_labels.keys()):
                    self.interfaces[self.position]()
                else:
                    self.draw(True)
                    to_return = self.action()
                    curses.flushinp()
                    self.screen.nodelay(False)
                    if self.failed_action:
                        self.add_status_text("")
                        self.add_status_text("Press any key to close this panel or ENTER to try again", highlighted=True)
                        x = self.screen.getch()
                        if x != ord('\n'):
                            self.dialog.window.refresh()
                            self.screen.nodelay(False)
                            return to_return
                        self.status_index = self.start_status_index
                        self.failed_action = False
                    else:
                        curses.napms(1000)
                        curses.flushinp()
                        self.dialog.window.refresh()
                        self.screen.nodelay(False)
                        return to_return
            elif x == 127 or x == curses.KEY_BACKSPACE:
                self.interfaces[self.position](clear=True)
            elif x == curses.KEY_RESIZE and curses.is_term_resized(self.screen_size[0], self.screen_size[1]):
                curses.resizeterm(self.screen.getmaxyx()[0],
                                  self.screen.getmaxyx()[1])
                self.screen_size = self.screen.getmaxyx()
                self.reset_window()
            self.draw()
            x = self.screen.getch()
        return None

    @abstractmethod
    def action(self):
        ...
