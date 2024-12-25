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
from modterm.components.hepers import get_text_input, CancelInput, text_input_to_int, text_input_to_float, \
                                      validate_ip
from modterm.components.modbus_handler import ModbusHandler
from modterm.components.config_handler import load_ip_sweep_config, save_ip_sweep_config
from modterm.components.menu_base import MenuBase


class IpSweepMenu(MenuBase):
    def __init__(self, screen, normal_text, highlighted_text, modbus_config):
        super().__init__(screen,
                         normal_text,
                         highlighted_text,
                         menu_labels={2: "F2  - Command: ",
                                      3: "F3  - Start register: ",
                                      4: "F4  - Number of registers to read: ",
                                      5: "F5  - Unit ID: ",
                                      6: "F6  - Subnet (first 3 octets): ",
                                      7: "F7  - TCP port: ",
                                      8: "F8  - Start address: ",
                                      9: "F9  - End address: ",
                                      10: "F10 - Timeout: ",
                                      11: "Start reading, ESC to interrupt the process"},
                         config_values={2: "command",
                                        3: "start_register",
                                        4: "number_of_registers",
                                        5: "unit_id",
                                        6: "subnet",
                                        7: "port",
                                        8: "start_address",
                                        9: "end_address",
                                        10: "timeout",
                                        11: ""},
                         interfaces={2: self.switch_command,
                                     3: self.get_start_register,
                                     4: self.get_number_of_registers,
                                     5: self.get_unit_id,
                                     6: self.get_subnet,
                                     7: self.get_port,
                                     8: self.get_start_address,
                                     9: self.get_end_address,
                                     10: self.get_timeout},
                         menu_name="Sweep IP addresses")

        self.modbus_handler = ModbusHandler(self.add_status_text)
        self.configuration = load_ip_sweep_config()
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
            start_register = get_text_input(self.dialog.window, 20, 3, len(self.menu_labels[3]) + 2,
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
            number_of_regs = get_text_input(self.dialog.window, 20, 4, len(self.menu_labels[4]) + 2,
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

    def get_unit_id(self, clear=False):
        try:
            unit_id = get_text_input(self.dialog.window, 5, 5, len(self.menu_labels[5]) + 2,
                                     str(self.configuration.unit_id) if not clear else "")
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

    def get_subnet(self, clear=False):
        try:
            subnet = get_text_input(self.dialog.window, 16, 6, len(self.menu_labels[6]) + 2,
                                    str(self.configuration.subnet) if not clear else "")
        except CancelInput:
            self.dialog.window.addstr(6, 23, "Cancelled")
            return
        if not validate_ip(subnet + ".0"):
            self.dialog.window.addstr(6, 23, "Invalid subnet! Must be the first 3 octets")
            self.dialog.window.refresh()
            curses.napms(1500)
        else:
            self.configuration.subnet = subnet

    def get_port(self, clear=False):
        try:
            port = get_text_input(self.dialog.window, 20, 7, len(self.menu_labels[7]) + 2,
                                  str(self.configuration.port) if not clear else "")
        except CancelInput:
            return
        port = text_input_to_int(port)
        if port is not None:
            if not 0 <= port < 65535:
                port = None
        if port is None:
            self.dialog.window.addstr(7, 23, "Invalid port number!")
            self.dialog.window.refresh()
            curses.napms(1000)
        else:
            self.configuration.port = port

    def get_start_address(self, clear=False):
        try:
            start_ip = get_text_input(self.dialog.window, 5, 8, len(self.menu_labels[8]) + 2,
                                           str(self.configuration.start_address) if not clear else "")
        except CancelInput:
            return
        start_ip = text_input_to_int(start_ip)
        if start_ip is not None:
            if not 0 < int(start_ip) < 256:
                start_ip = None
        if start_ip is not None:
            if self.configuration.end_address <= start_ip:
                self.dialog.window.addstr(8, 22, "Must be lower than the end address!")
                self.dialog.window.refresh()
                curses.napms(1000)
                return
            self.configuration.start_address = start_ip
            return
        self.dialog.window.addstr(8, 22, "Invalid address")
        self.dialog.window.refresh()
        curses.napms(1000)

    def get_end_address(self, clear=False):
        try:
            end_ip = get_text_input(self.dialog.window, 5, 9, len(self.menu_labels[9]) + 2,
                                          str(self.configuration.end_address) if not clear else "")
        except CancelInput:
            return
        end_ip = text_input_to_int(end_ip)
        if end_ip is not None:
            if not 0 < int(end_ip) < 256:
                end_ip = None
        if end_ip is not None:
            if end_ip <= self.configuration.start_address:
                self.dialog.window.addstr(9, 21, "Must be greater than the start address!")
                self.dialog.window.refresh()
                curses.napms(1000)
                return
            self.configuration.end_address = end_ip
            return
        self.dialog.window.addstr(9, 21, "Invalid address")
        self.dialog.window.refresh()
        curses.napms(1000)

    def get_timeout(self, clear=False):
        try:
            timeout = get_text_input(self.dialog.window, 5, 10, len(self.menu_labels[10]) + 2,
                                     str(self.configuration.timeout) if not clear else "")
        except CancelInput:
            return
        timeout = text_input_to_float(timeout)
        if timeout is not None:
            if 60 < float(timeout):
                self.dialog.window.addstr(10, 16, "I don't think you want to wait for that long")
                self.dialog.window.refresh()
                curses.napms(1000)
                return
            self.configuration.timeout = timeout
            return
        self.dialog.window.addstr(10, 16, "Invalid timeout value!")
        self.dialog.window.refresh()
        curses.napms(1000)

    def action(self):
        save_ip_sweep_config(self.configuration)
        return self.modbus_handler.ip_sweep(self.screen, self.modbus_config, self.configuration)
