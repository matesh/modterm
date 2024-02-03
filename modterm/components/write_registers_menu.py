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
from typing import Optional
from modterm.components.window_base import WindowBase
from modterm.components.hepers import get_text_input
from modterm.components.modbus_handler import ModbusHandler
from modterm.components.config_handler import load_write_config, save_write_config
from modterm.components.scrollable_list import SelectWindow
from modterm.components.definitions import formats, TableContents


class WriteRegistersMenu:
    def __init__(self, screen, normal_text, highlighted_text):
        width = 100 if 102 < screen.getmaxyx()[1] else screen.getmaxyx()[1] - 2
        height = 30 if 32 < screen.getmaxyx()[0] else screen.getmaxyx()[0] - 2
        self.dialog = WindowBase(screen, height, width, title="Writre registers", min_width=40, min_height=15)
        self.is_valid = self.dialog.is_valid
        if not self.is_valid:
            return
        self.max_status_index = height - 2
        self.normal_text = normal_text
        self.highlighted_text = highlighted_text
        self.screen = screen
        self.status_start_index = 10
        self.status_index = self.status_start_index
        self.modbus_handler = ModbusHandler(self.add_status_text)

        self.configuration = load_write_config()

    def draw(self):
        self.dialog.draw_window()
        self.dialog.window.addstr(2, 2, f"F2 - Register address: {self.configuration.address}")
        self.dialog.window.addstr(3, 2, f"F3 - Modbus unit ID: {self.configuration.unit}")
        self.dialog.window.addstr(4, 2, f"F4 - Format: {self.configuration.format}")
        self.dialog.window.addstr(5, 2, f"F5 - Multicast enable: {self.configuration.multicast}")
        self.dialog.window.addstr(6, 2, f"F6 - Value: {self.configuration.value}")
        self.dialog.window.addstr(8, 2, f"Press ENTER to start writing")
        self.dialog.window.refresh()

    def add_status_text(self, text):
        if self.status_index == self.max_status_index:
            self.status_index = self.status_start_index
            self.dialog.window.clear()
            self.draw()
        self.dialog.window.addstr(self.status_index, 2, text)
        self.status_index += 1
        self.dialog.window.refresh()

    def get_register(self):
        start_register = get_text_input(self.dialog.window, 5, 2, 25, str(self.configuration.address))
        try:
            if not 0 <= int(start_register) < 65535:
                raise AttributeError
        except Exception:
            self.dialog.window.addstr(2, 24, "Invalid register number")
            self.dialog.window.refresh()
            curses.napms(1000)
        else:
            self.configuration.address = int(start_register)

    def get_unit_id(self):
        unit_id = get_text_input(self.dialog.window, 4, 3, 23, str(self.configuration.unit))
        try:
            if not 0 < int(unit_id) < 256:
                raise AttributeError
        except Exception:
            self.dialog.window.addstr(3, 22, "Invalid unit ID")
            self.dialog.window.refresh()
            curses.napms(1000)
        else:
            self.configuration.unit = int(unit_id)

    def get_format(self):
        selector = SelectWindow(self.screen, 8, 15, self.dialog.window.getbegyx()[0]+3, self.dialog.window.getbegyx()[1]+15, self.normal_text, self.highlighted_text, list(formats.keys()))
        if (selection := selector.get_selection()) is not None:
            self.configuration.format = selection

    def swap_multicast(self):
        if self.configuration.multicast:
            self.configuration.multicast = False
        else:
            self.configuration.multicast = True

    def get_value(self):
        value = get_text_input(self.dialog.window, 15, 6, 14, str(self.configuration.value))
        try:
            value = int(value)
        except Exception:
            try:
                value = int(value, 0)
            except Exception:
                self.dialog.window.addstr(6, 13, "Invalid value")
                self.dialog.window.refresh()
                curses.napms(1000)
                return
        self.configuration.value = value

    def write_register(self, modbus_config) -> Optional[TableContents]:
        self.draw()
        x = self.screen.getch()
        while x != 27 and x != ord("\n"):
            if x == curses.KEY_F2:
                self.get_register()
            if x == curses.KEY_F3:
                self.get_unit_id()
            if x == curses.KEY_F4:
                self.get_format()
            if x == curses.KEY_F5:
                self.swap_multicast()
            if x == curses.KEY_F6:
                self.get_value()
            self.draw()
            x = self.screen.getch()
        if x == 27:
            return None
        to_return = self.modbus_handler.write_registers(modbus_config, self.configuration, formats)
        self.add_status_text("Press any key to close this panel")
        self.dialog.window.refresh()
        x = self.screen.getch()
        save_write_config(self.configuration)
        return to_return
