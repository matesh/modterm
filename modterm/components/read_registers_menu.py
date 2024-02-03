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
from modterm.components.window_base import WindowBase
from modterm.components.definitions import HOLDING, INPUT, TableContents
from modterm.components.hepers import get_text_input
from modterm.components.modbus_handler import ModbusHandler
from modterm.components.config_handler import load_read_config, save_read_config


class ReadRegistersMenu:
    def __init__(self, screen, normal_text, highlighted_text):
        width = 100 if 102 < screen.getmaxyx()[1] else screen.getmaxyx()[1] - 2
        height = 30 if 32 < screen.getmaxyx()[0] else screen.getmaxyx()[0] - 2
        self.dialog = WindowBase(screen, height, width, title="Read registers", min_width=40, min_height=15)
        self.is_valid = self.dialog.is_valid
        if not self.is_valid:
            return
        self.max_status_index = height - 2
        self.normal_text = normal_text
        self.highlighted_text = highlighted_text
        self.screen = screen
        self.start_status_index = 10
        self.status_index = self.start_status_index
        self.modbus_handler = ModbusHandler(self.add_status_text)

        self.configuration = load_read_config()

    def draw(self):
        self.dialog.draw_window()
        self.dialog.window.addstr(2, 2, f"F2 - Command: {self.configuration.command}")
        self.dialog.window.addstr(3, 2, f"F3 - Start register: {self.configuration.start}")
        self.dialog.window.addstr(4, 2, f"F4 - Number of registers to read: {self.configuration.number}")
        self.dialog.window.addstr(5, 2, f"F5 - Modbus unit ID: {self.configuration.unit}")
        self.dialog.window.addstr(6, 2, f"F6 - Block size: {self.configuration.block_size}")
        self.dialog.window.addstr(8, 2, f"Press ENTER to start reading, ESC to interrupt the process")
        self.dialog.window.refresh()

    def add_status_text(self, text):
        if self.status_index == self.max_status_index:
            self.dialog.window.clear()
            self.draw()
            self.status_index = self.start_status_index
        self.dialog.window.addstr(self.status_index, 2, text)
        self.status_index += 1
        self.dialog.window.refresh()

    def switch_command(self):
        if self.configuration.command == HOLDING:
            self.configuration.command = INPUT
        # elif self.configuration["command"] == INPUT:
        #     self.configuration["command"] = COIL
        else:
            self.configuration.command = HOLDING

    def get_start_register(self):
        start_register = get_text_input(self.dialog.window, 20, 3, 23, str(self.configuration.start))
        try:
            if not 0 <= int(start_register) < 65535:
                raise AttributeError
        except Exception:
            self.dialog.window.addstr(3, 23, "Invalid register number")
            self.dialog.window.refresh()
            curses.napms(1000)
        else:
            self.configuration.start = int(start_register)

    def get_number_of_registers(self):
        number_of_regs = get_text_input(self.dialog.window, 20, 4, 36, str(self.configuration.number))
        try:
            if not 0 < int(number_of_regs) < 10000:
                raise AttributeError
        except Exception:
            self.dialog.window.addstr(4, 36, "Invalid")
            self.dialog.window.refresh()
            curses.napms(1000)
        else:
            self.configuration.number = int(number_of_regs)

    def get_unit_id(self):
        unit_id = get_text_input(self.dialog.window, 5, 5, 23, str(self.configuration.unit))
        try:
            if not 0 < int(unit_id) < 256:
                raise AttributeError
        except Exception:
            self.dialog.window.addstr(5, 23, "Invalid unit ID")
            self.dialog.window.refresh()
            curses.napms(1000)
        else:
            self.configuration.unit = int(unit_id)

    def get_block_size(self):
        unit_id = get_text_input(self.dialog.window, 4, 6, 19, str(self.configuration.block_size))
        try:
            if not (1 <= int(unit_id) <= 125):
                raise AttributeError
        except Exception:
            self.dialog.window.addstr(5, 23, "Block size must be between 1 and 125")
            self.dialog.window.refresh()
            curses.napms(1000)
        else:
            self.configuration.block_size = int(unit_id)

    def read_registers(self, modbus_config) -> Optional[TableContents]:
        self.draw()
        x = self.screen.getch()
        while x != 27 and x != ord("\n"):
            if x == curses.KEY_F2:
                self.switch_command()
            if x == curses.KEY_F3:
                self.get_start_register()
            if x == curses.KEY_F4:
                self.get_number_of_registers()
            if x == curses.KEY_F5:
                self.get_unit_id()
            if x == curses.KEY_F6:
                self.get_block_size()
            self.draw()
            x = self.screen.getch()
        if x == 27:
            return None
        to_return = self.modbus_handler.get_data_rows(self.screen, modbus_config, self.configuration)
        if to_return is None:
            self.add_status_text("Failed to process registers, check the log for details.")
        self.add_status_text("Press any key to close this panel")
        self.dialog.window.refresh()
        self.screen.nodelay(False)
        x = self.screen.getch()
        save_read_config(self.configuration)
        return to_return
