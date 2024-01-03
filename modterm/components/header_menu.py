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
from modterm.components.serial_interface_scan import get_serial_interfaces
from modterm.components.definitions import BigEndian, LittleEndian, TCP, RTU
from modterm.components.hepers import get_text_input
from modterm.components.config_handler import load_modbus_config
from modterm import __version__


COMMON_BAUDS = [600, 1200, 1800, 2400, 4800, 7200, 9600, 14400, 19200, 38400, 56000, 57600, 115200, 128000,
                        230400, 460800, 500000, 921600]


def validate_ip(s: str) -> bool:
    a = s.split('.')
    if len(a) != 4:
        return False
    for x in a:
        if not x.isdigit():
            return False
        i = int(x)
        if i < 0 or i > 255:
            return False
    return True


class HeaderMenu:
    def __init__(self, screen, normal_text: curses.color_pair, highlighted_text: curses.color_pair):
        self.window = curses.newwin(5, screen.getmaxyx()[1], 0, 0)
        self.normal_text = normal_text
        self.highlighted_text = highlighted_text
        self.screen = screen

        # load params
        self.configuration = load_modbus_config()

    def draw(self):
        self.window.erase()
        self.window.border(0)
        self.window.box()
        self.window.addstr(1, 2, f"F2 - Modbus protocol: {self.configuration.mode}", self.normal_text)
        if self.configuration.mode == TCP:
            self.window.addstr(2, 2, f"F3 - IP address: {self.configuration.ip}", self.normal_text)
            self.window.addstr(3, 2, f"F4 - TCP port: {self.configuration.port}", self.normal_text)
        else:
            interface = f"F3 - Interface: {self.configuration.interface}"
            self.window.addstr(2, 2, interface, self.normal_text)
            self.window.addstr(3, 2, f"F4 - Baud rate: {self.configuration.baud_rate}", self.normal_text)
            self.window.addstr(1, 2 + len(interface) + 2, f"F5 - Parity: {self.configuration.parity}", self.normal_text)
            self.window.addstr(2, 2 + len(interface) + 2, f"F6 - Bytesize: {self.configuration.bytesize}", self.normal_text)
            self.window.addstr(3, 2 + len(interface) + 2, f"F7 - Stopbits: {self.configuration.stopbits}", self.normal_text)
        self.window.addstr(1, self.screen.getmaxyx()[1]-31, f"F8 - Byte order: {self.configuration.byte_order}", self.normal_text)
        self.window.addstr(2, self.screen.getmaxyx()[1]-31, f"F9 - Word order: {self.configuration.word_order}", self.normal_text)
        header = f" ModTerm V{__version__} "
        self.window.addstr(0, (self.screen.getmaxyx()[1] - len(header))//2, header, self.normal_text)
        helptext = " F1 - Help "
        self.window.addstr(4, self.screen.getmaxyx()[1] - len(helptext) - 3, helptext, self.normal_text)
        self.window.refresh()

    def switch_protocol(self):
        if self.configuration.mode == RTU:
            self.configuration.mode = TCP
        else:
            self.configuration.mode = RTU

    def get_ip_address(self):
        ip_address = get_text_input(self.window, 16, 2, 19, self.configuration.ip)
        if not validate_ip(ip_address):
            self.window.addstr(2, 19, "!!Invalid IP!! ")
            self.window.refresh()
            curses.napms(1000)
        else:
            self.configuration.ip = ip_address

    def get_tcp_port(self):
        port = get_text_input(self.window, 16, 3, 17, str(self.configuration.port))
        try:
            if not 0 < int(port) < 65535:
                raise AttributeError
        except Exception:
            self.window.addstr(3, 17, "Invalid port!")
            self.window.refresh()
            curses.napms(1000)
        else:
            self.configuration.port = int(port)

    def swap_wordorder(self):
        if self.configuration.word_order == BigEndian:
            self.configuration.word_order = LittleEndian
        else:
            self.configuration.word_order = BigEndian

    def swap_byteorder(self):
        if self.configuration.byte_order == BigEndian:
            self.configuration.byte_order = LittleEndian
        else:
            self.configuration.byte_order = BigEndian

    def get_interface(self):
        interfaces = get_serial_interfaces()
        selector = SelectWindow(self.screen, 10, 40, 2, 2, self.normal_text, self.highlighted_text, interfaces, "Couldn't detect any interfaces")
        if (selection := selector.get_selection()) is not None:
            self.configuration.interface = selection

    def get_baud_rate(self):
        selector = SelectWindow(self.screen, 10, 20, 3, 2, self.normal_text, self.highlighted_text, COMMON_BAUDS)
        if (selection := selector.get_selection()) is not None:
            self.configuration.baud_rate = selection

    def swap_parity(self):
        if self.configuration.parity == "N":
            self.configuration.parity = "O"
        elif self.configuration.parity == "O":
            self.configuration.parity = "E"
        else:
            self.configuration.parity = "N"

    def swap_bytesize(self):
        if self.configuration.bytesize == 7:
            self.configuration.bytesize = 8
        else:
            self.configuration.bytesize = 7

    def swap_stopbits(self):
        if self.configuration.stopbits == 0:
            self.configuration.stopbits = 1
        else:
            self.configuration.stopbits = 0

    def check_navigate(self, keystroke):
        if keystroke == curses.KEY_F2:
            self.switch_protocol()

        if keystroke == curses.KEY_F8:
            self.swap_byteorder()
            return True

        if keystroke == curses.KEY_F9:
            self.swap_wordorder()
            return True

        if self.configuration.mode == TCP:
            if keystroke == curses.KEY_F3:
                self.get_ip_address()
            if keystroke == curses.KEY_F4:
                self.get_tcp_port()
            return

        if keystroke == curses.KEY_F3:
            self.get_interface()
        if keystroke == curses.KEY_F4:
            self.get_baud_rate()
        if keystroke == curses.KEY_F5:
            self.swap_parity()
        if keystroke == curses.KEY_F6:
            self.swap_bytesize()
        if keystroke == curses.KEY_F7:
            self.swap_stopbits()
