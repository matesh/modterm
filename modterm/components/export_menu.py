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
import time
import os
from modterm.components.window_base import WindowBase
from modterm.components.hepers import get_text_input
from modterm.components.modbus_handler import ModbusHandler
from modterm.components.config_handler import load_export_config, save_export_config, get_project_dir


class ExportMenu:
    def __init__(self, screen, normal_text, highlighted_text, header, data_rows):
        width = 100 if 102 < screen.getmaxyx()[1] else screen.getmaxyx()[1] - 2
        height = 30 if 32 < screen.getmaxyx()[0] else screen.getmaxyx()[0] - 2

        self.header = header
        self.data_rows = data_rows

        self.max_width = width - 2
        self.dialog = WindowBase(screen, height, width, title="Unit sweep", min_width=40, min_height=15)
        self.is_valid = self.dialog.is_valid
        if not self.is_valid:
            return
        self.max_status_index = height - 2
        self.normal_text = normal_text
        self.highlighted_text = highlighted_text
        self.screen = screen
        self.status_index = 11
        self.modbus_handler = ModbusHandler(self.add_status_text)

        self.configuration = load_export_config()
        if self.configuration.last_dir is None:
            self.configuration.last_dir = get_project_dir()
        if self.configuration.last_file_name is None:
            self.configuration.last_file_name = str(int(time.time()))

    def draw(self):
        self.dialog.draw_window()
        self.dialog.window.addstr(2, 2, f"F2 - Export file type: "
                                  f"{'CSV' if self.configuration.last_file_type == '.csv' else 'Formatted text file'}")
        self.dialog.window.addstr(3, 2, f"F3 - Export directory: {self.configuration.last_dir}")
        self.dialog.window.addstr(4, 2, f"F4 - File name: {self.configuration.last_file_name}{self.configuration.last_file_type}")
        self.dialog.window.addstr(9, 2, f"Press ENTER to export")
        self.dialog.window.refresh()

    def add_status_text(self, text):
        if self.status_index == self.max_status_index:
            self.dialog.window.clear()
            self.draw()
            self.status_index = 11
        self.dialog.window.addstr(self.status_index, 2, text)
        self.status_index += 1
        self.dialog.window.refresh()

    def file_type(self):
        if self.configuration.last_file_type == ".csv":
            self.configuration.last_file_type = ".txt"
        else:
            self.configuration.last_file_type = ".csv"

    def directory(self):
        directory = get_text_input(self.dialog.window, self.max_width - 26, 3, 25,
                                   str(self.configuration.last_dir))
        if not os.path.isdir(directory):
            self.dialog.window.addstr(3, 25, "  Directory doesn't exist  ")
            self.dialog.window.refresh()
            curses.napms(1000)
        else:
            self.configuration.last_dir = directory

    def file_name(self):
        file_name = get_text_input(self.dialog.window, self.max_width - 20, 4, 18,
                                   str(self.configuration.last_file_name))
        self.configuration.last_file_name = file_name

    def export_dialog(self):
        self.draw()
        x = self.screen.getch()
        while x != 27 and x != ord("\n"):
            if x == curses.KEY_F2:
                self.file_type()
            if x == curses.KEY_F3:
                self.directory()
            if x == curses.KEY_F4:
                self.file_name()
            self.draw()
            x = self.screen.getch()
        if x == 27:
            return
        try:
            file = os.path.join(self.configuration.last_dir,
                                self.configuration.last_file_name + self.configuration.last_file_type)
            with open(file, 'w') as f:
                if self.configuration.last_file_type == ".csv":
                    f.write(",".join(x.strip() for x in self.header) + os.linesep)
                else:
                    f.write(" ".join(self.header) + os.linesep)
                for row in self.data_rows:
                    if self.configuration.last_file_type == ".csv":
                        f.write(",".join(x.strip() for x in row) + os.linesep)
                    else:
                        f.write(" ".join(row) + os.linesep)
        except Exception as e:
            self.add_status_text("Failed to export:")
            self.add_status_text(repr(e))
        else:
            self.add_status_text("Successful export")
        self.add_status_text(" ")
        self.add_status_text("Press any key to close this panel")
        self.dialog.window.refresh()
        x = self.screen.getch()
        save_export_config(self.configuration)
