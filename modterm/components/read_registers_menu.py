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
from modterm.components.definitions import HOLDING, INPUT, COIL, DISCRETE
from modterm.components.hepers import get_text_input, CancelInput, text_input_to_int
from modterm.components.scrollable_list import SelectWindow
from modterm.components.modbus_handler import ModbusHandler
from modterm.components.config_handler import load_read_config, save_read_config
from modterm.components.menu_base import MenuBase


class ReadRegistersMenu(MenuBase):
    def __init__(self, screen, normal_text, highlighted_text, modbus_config):
        super().__init__(screen,
                         normal_text,
                         highlighted_text,
                         menu_labels={2: "F2 - Command: ",
                                      3: "F3 - Start register: ",
                                      4: "F4 - Number of registers to read: ",
                                      5: "F5 - Modbus unit ID: ",
                                      6: "F6 - Block size: ",
                                      7: "Start reading, ESC to interrupt the process "},
                         config_values={2: "command",
                                        3: "start",
                                        4: "number",
                                        5: "unit",
                                        6: "block_size",
                                        7: ""},
                         interfaces={2: self.switch_command,
                                     3: self.get_start_register,
                                     4: self.get_number_of_registers,
                                     5: self.get_unit_id,
                                     6: self.get_block_size},
                         menu_name="Read registers")

        self.modbus_handler = ModbusHandler(self.add_status_text)
        self.modbus_config = modbus_config
        self.configuration = load_read_config()

    def switch_command(self, clear=False):
        command_list = [INPUT, HOLDING, COIL, DISCRETE]
        width = len(max(command_list, key=len)) + 4
        selector = SelectWindow(self.screen, len(command_list) + 2, width, self.dialog.window.getbegyx()[0] + 3,
                                self.dialog.window.getbegyx()[1] + 15, self.normal_text, self.highlighted_text,
                                command_list)
        if (selection := selector.get_selection()) is not None:
            self.configuration.command = selection

    def get_start_register(self, clear=False):
        try:
            start_register = get_text_input(self.dialog.window, 20, 3, 23,
                                            str(self.configuration.start) if not clear else "")
        except CancelInput:
            return
        start_register = text_input_to_int(start_register)
        if start_register is not None:
            if not 0 <= start_register < 65535:
                start_register = None
        if start_register is None:
            self.dialog.window.addstr(3, 23, "Invalid register number")
            self.dialog.window.refresh()
            curses.napms(1000)
        else:
            self.configuration.start = start_register

    def get_number_of_registers(self, clear=False):
        try:
            number_of_regs = get_text_input(self.dialog.window, 20, 4, 36,
                                            str(self.configuration.number) if not clear else "")
        except CancelInput:
            return
        number_of_regs = text_input_to_int(number_of_regs)
        if number_of_regs is not None:
            if not 0 <= number_of_regs < 65535:
                number_of_regs = None
        if number_of_regs is None:
            self.dialog.window.addstr(4, 36, "Invalid")
            self.dialog.window.refresh()
            curses.napms(1000)
        else:
            self.configuration.number = number_of_regs

    def get_unit_id(self, clear=False):
        try:
            unit_id = get_text_input(self.dialog.window, 5, 5, 23,
                                     str(self.configuration.unit) if not clear else "")
        except CancelInput:
            return
        unit_id = text_input_to_int(unit_id)
        if unit_id is not None:
            if not 0 <= unit_id <= 255:
                unit_id = None
        if unit_id is None:
            self.dialog.window.addstr(5, 23, "Invalid unit ID")
            self.dialog.window.refresh()
            curses.napms(1000)
        else:
            self.configuration.unit = unit_id

    def get_block_size(self, clear=False):
        try:
            block_size = get_text_input(self.dialog.window, 4, 6, 19,
                                        str(self.configuration.block_size) if not clear else "")
        except CancelInput:
            return
        block_size = text_input_to_int(block_size)
        if block_size is not None:
            if not 1 <= block_size <= 125:
                block_size = None
        if block_size is None:
            self.dialog.window.addstr(6, 23, "Block size must be between 1 and 125")
            self.dialog.window.refresh()
            curses.napms(1000)
        else:
            self.configuration.block_size = block_size

    def action(self):
        save_read_config(self.configuration)
        return self.modbus_handler.get_data_rows(self.screen, self.modbus_config, self.configuration)
