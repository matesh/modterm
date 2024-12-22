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
from modterm.components.hepers import get_text_input
from modterm.components.scrollable_list import SelectWindow
from modterm.components.config_handler import load_export_config, save_export_config, get_project_dir
from modterm.components.menu_base import MenuBase


class ExportMenu(MenuBase):
    def __init__(self, screen, normal_text, highlighted_text, header, data_rows):
        super().__init__(screen,
                         normal_text,
                         highlighted_text,
                         menu_labels={2: "F2 - Export file type: ",
                                      3: "F3 - Export directory: ",
                                      4: "F4 - File name: ",
                                      5: "Export!"},
                         config_values={},
                         interfaces={2: self.file_type,
                                     3: self.directory,
                                     4: self.file_name},
                         menu_name="Export data")
        self.header = header
        self.data_rows = data_rows

        self.configuration = load_export_config()
        if self.configuration.last_dir is None:
            self.configuration.last_dir = get_project_dir()
        if self.configuration.last_file_name is None:
            self.configuration.last_file_name = str(int(time.time()))

        self.menu_value_fetcher = {
            2: lambda: getattr(self.configuration, "last_file_type"),
            3: lambda: getattr(self.configuration, "last_dir"),
            4: lambda: getattr(self.configuration, "last_file_name") + "." + getattr(self.configuration, "last_file_type").lower()}

    def draw(self, no_highlight=False):
        self.dialog.draw_window()
        for position, label in self.menu_labels.items():
            if position not in self.menu_value_fetcher:
                value = ""
            else:
                value = self.menu_value_fetcher[position]()
            if len(value) == 0 and self.position == position:
                self.dialog.window.addstr(position, 2, label,
                                          self.normal_text if no_highlight else self.highlighted_text)
            else:
                self.dialog.window.addstr(position, 2, label, self.normal_text)

            if self.position == position and position != max(self.menu_labels.keys()):
                self.dialog.window.addstr(position, 2 + len(label), value,
                                          self.normal_text if no_highlight else self.highlighted_text)
            else:
                self.dialog.window.addstr(position, 2 + len(label), value, self.normal_text)
        self.dialog.window.refresh()

    def file_type(self):
        type_list = ["CSV", "TXT"]
        width = len(max(type_list, key=len)) + 4
        selector = SelectWindow(self.screen, len(type_list) + 2, width, self.dialog.window.getbegyx()[0] + 3,
                                self.dialog.window.getbegyx()[1] + 23, self.normal_text, self.highlighted_text,
                                type_list)
        if (selection := selector.get_selection()) is not None:
            self.configuration.last_file_type = selection

    def directory(self):
        directory = get_text_input(self.dialog.window, self.dialog.width - 26, 3, 25,
                                   str(self.configuration.last_dir))
        if not os.path.isdir(directory):
            self.dialog.window.addstr(3, 25, "  Directory doesn't exist  ")
            self.dialog.window.refresh()
            curses.napms(1000)
        else:
            self.configuration.last_dir = directory

    def file_name(self):
        file_name = get_text_input(self.dialog.window, self.dialog.width - 20, 4, 18,
                                   str(self.configuration.last_file_name))
        self.configuration.last_file_name = file_name

    def action(self):
        save_export_config(self.configuration)
        try:
            file = os.path.join(self.configuration.last_dir,
                                self.configuration.last_file_name + "." + self.configuration.last_file_type.lower())
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
            self.add_status_text(f"Failed to export: {repr(e)}", failed=True)
        else:
            self.add_status_text("Successful export")
