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
from modterm.components.scrollable_list import SelectWindow
from modterm.components.definitions import HOLDING, INPUT, COIL, DISCRETE
from modterm.components.hepers import get_text_input, CancelInput, text_input_to_int, text_input_to_float
from modterm.components.modbus_handler import ModbusHandler
from modterm.components.config_handler import load_unit_sweep_config, save_unit_sweep_config
from modterm.components.menu_base import MenuBase


class UnitSweepMenu(MenuBase):
    def __init__(self, screen, normal_text, highlighted_text, modbus_config):
        super().__init__(screen,
                         normal_text,
                         highlighted_text,
                         menu_labels={2: "F2 - Command: ",
                                      3: "F3 - Start register: ",
                                      4: "F4 - Number of registers to read: ",
                                      5: "F5 - Start unit ID: ",
                                      6: "F6 - Last unit ID: ",
                                      7: "F7 - Timeout: ",
                                      8: "Start reading, ESC to interrupt the process"},
                         config_values={2: "command",
                                        3: "start_register",
                                        4: "number_of_registers",
                                        5: "start_unit",
                                        6: "last_unit",
                                        7: "timeout",
                                        8: ""},
                         interfaces={2: self.switch_command,
                                     3: self.get_start_register,
                                     4: self.get_number_of_registers,
                                     5: self.get_start_unit_id,
                                     6: self.get_last_unit_id,
                                     7: self.get_timeout},
                         menu_name="Sweep unit IDs")

        self.modbus_handler = ModbusHandler(self.add_status_text)
        self.configuration = load_unit_sweep_config()
        self.modbus_config = modbus_config

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
                                            str(self.configuration.start_register) if not clear else "")
        except CancelInput:
            return
        start_register = text_input_to_int(start_register)
        if start_register is not None:
            if not 0 <= start_register < 65535:
                start_register = None
        if start_register is None:
            self.dialog.window.addstr(3, 23, "Invalid start register number")
            self.dialog.window.refresh()
            curses.napms(1000)
        else:
            self.configuration.start_register = start_register

    def get_number_of_registers(self, clear=False):
        try:
            number_of_regs = get_text_input(self.dialog.window, 20, 4, 36,
                                            str(self.configuration.number_of_registers) if not clear else "")
        except CancelInput:
            return
        number_of_regs = text_input_to_int(number_of_regs)
        if number_of_regs is not None:
            if not 0 <= number_of_regs < 65535:
                number_of_regs = None
        if number_of_regs is None:
            self.dialog.window.addstr(4, 36, "Invalid number of registers")
            self.dialog.window.refresh()
            curses.napms(1000)
        else:
            self.configuration.number_of_registers = number_of_regs

    def get_start_unit_id(self, clear=False):
        try:
            start_unit_id = get_text_input(self.dialog.window, 5, 5, 22,
                                           str(self.configuration.start_unit) if not clear else "")
        except CancelInput:
            return
        start_unit_id = text_input_to_int(start_unit_id)
        if start_unit_id is not None:
            if not 0 < int(start_unit_id) < 256:
                start_unit_id = None
        if start_unit_id is not None:
            if self.configuration.last_unit <= start_unit_id:
                self.dialog.window.addstr(5, 22, "Must be lower than the last unit ID!")
                self.dialog.window.refresh()
                curses.napms(1000)
                return
            self.configuration.start_unit = start_unit_id
            return
        self.dialog.window.addstr(5, 22, "Invalid unit ID")
        self.dialog.window.refresh()
        curses.napms(1000)

    def get_last_unit_id(self, clear=False):
        try:
            last_unit_id = get_text_input(self.dialog.window, 5, 6, 21,
                                          str(self.configuration.last_unit) if not clear else "")
        except CancelInput:
            return
        last_unit_id = text_input_to_int(last_unit_id)
        if last_unit_id is not None:
            if not 0 < int(last_unit_id) < 256:
                last_unit_id = None
        if last_unit_id is not None:
            if int(last_unit_id) <= self.configuration.start_unit:
                self.dialog.window.addstr(6, 21, "Must be greater than the start unit ID!")
                self.dialog.window.refresh()
                curses.napms(1000)
                return
            self.configuration.last_unit = last_unit_id
            return
        self.dialog.window.addstr(6, 21, "Invalid unit ID")
        self.dialog.window.refresh()
        curses.napms(1000)

    def get_timeout(self, clear=False):
        try:
            timeout = get_text_input(self.dialog.window, 5, 7, 16,
                                     str(self.configuration.timeout) if not clear else "")
        except CancelInput:
            return
        timeout = text_input_to_float(timeout)
        if timeout is not None:
            if 60 < float(timeout):
                self.dialog.window.addstr(7, 16, "I don't think you want to wait for that long")
                self.dialog.window.refresh()
                curses.napms(1000)
                return
            self.configuration.timeout = timeout
            return
        self.dialog.window.addstr(7, 16, "Invalid timeout value!")
        self.dialog.window.refresh()
        curses.napms(1000)

    def action(self):
        save_unit_sweep_config(self.configuration)
        return self.modbus_handler.unit_sweep(self.screen, self.modbus_config, self.configuration)
