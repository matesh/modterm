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
from modterm.components.hepers import get_text_input, CancelInput, text_input_to_int, text_input_to_float
from modterm.components.modbus_handler import ModbusHandler
from modterm.components.config_handler import load_write_config, save_write_config, load_read_config
from modterm.components.scrollable_list import SelectWindow
from modterm.components.definitions import formats, HOLDING_WRITE, COIL_WRITE, COIL, HOLDING
from modterm.components.menu_base import MenuBase


class WriteRegistersMenu(MenuBase):
    def __init__(self, screen, normal_text, highlighted_text, modbus_config, start_register=None):
        super().__init__(screen,
                         normal_text,
                         highlighted_text,
                         menu_labels={2: "F2 - Command: ",
                                      3: "F3 - Register address: ",
                                      4: "F4 - Modbus unit ID: ",
                                      5: "F5 - Format: ",
                                      6: "F6 - Multicast enable: ",
                                      7: "F7 - Value: ",
                                      8: "Write! "},
                         config_values={2: "command",
                                        3: "address",
                                        4: "unit",
                                        5: "format",
                                        6: "multicast",
                                        7: "value",
                                        8: ""},
                         interfaces={2: self.switch_command,
                                     3: self.get_register,
                                     4: self.get_unit_id,
                                     5: self.get_format,
                                     6: self.swap_multicast,
                                     7: self.get_value},
                         menu_name="Write registers")

        self.configuration = load_write_config()
        if start_register is not None:
            self.configuration.address = start_register
        self.read_config = load_read_config()
        self.modbus_config = modbus_config
        self.modbus_handler = ModbusHandler(self.add_status_text)
        self.format_lock = False
        if start_register is not None:
            if self.read_config.command == COIL:
                self.configuration.command = COIL_WRITE
                self.format_lock = True
                self.configuration.format = "BIT"
            if self.read_config.command == HOLDING:
                self.configuration.command = HOLDING_WRITE

    def switch_command(self, clear=False):
        command_list = [HOLDING_WRITE, COIL_WRITE]
        width = len(max(command_list, key=len)) + 4
        selector = SelectWindow(self.screen, len(command_list) + 2, width, self.dialog.window.getbegyx()[0] + 3,
                                self.dialog.window.getbegyx()[1] + 15, self.normal_text, self.highlighted_text,
                                command_list)
        if (selection := selector.get_selection()) is not None:
            self.configuration.command = selection
            if self.configuration.command == COIL_WRITE:
                self.format_lock = True
            else:
                self.format_lock = False

    def get_register(self, clear=False):
        try:
            start_register = get_text_input(self.dialog.window, 8, 3, 25,
                                            str(self.configuration.address) if not clear else "")
        except CancelInput:
            return
        start_register = text_input_to_int(start_register)
        if start_register is not None:
            if not 0 <= start_register <= 65535:
                start_register = None
        if start_register is None:
            self.dialog.window.addstr(3, 24, "Invalid register number!")
            self.dialog.window.refresh()
            curses.napms(1000)
        self.configuration.address = start_register

    def get_unit_id(self, clear=False):
        try:
            unit_id = get_text_input(self.dialog.window, 5, 4, 23,
                                     str(self.configuration.unit) if not clear else "")
        except CancelInput:
            return
        value = text_input_to_int(unit_id)
        if value is not None:
            if not 0 < int(unit_id) < 256:
                value = None
        if value is None:
            self.dialog.window.addstr(5, 22, "Invalid unit ID")
            self.dialog.window.refresh()
            curses.napms(1000)
        self.configuration.unit = unit_id

    def get_format(self, clear=False):
        if self.format_lock:
            return
        selector = SelectWindow(self.screen, 8, 15, self.dialog.window.getbegyx()[0]+3, self.dialog.window.getbegyx()[1]+15, self.normal_text, self.highlighted_text, list(formats.keys()))
        if (selection := selector.get_selection()) is not None:
            self.configuration.format = selection

    def swap_multicast(self, clear=False):
        if self.configuration.multicast:
            self.configuration.multicast = False
        else:
            self.configuration.multicast = True

    def get_value(self, clear=False):
        try:
            value = get_text_input(self.dialog.window, 15, 7, 14,
                                   str(self.configuration.value) if not clear else "")
        except CancelInput:
            return
        if "FLOAT" not in self.configuration.format:
            value = text_input_to_int(value)
        else:
            value = text_input_to_float(value)
        if value is None:
            self.dialog.window.addstr(7, 13, "Invalid value")
            self.dialog.window.refresh()
            curses.napms(1000)
            return
        self.configuration.value = value

    def action(self):
        save_write_config(self.configuration)
        return self.modbus_handler.write_registers(self.modbus_config, self.configuration, formats)
