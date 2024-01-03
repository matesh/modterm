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
from math import ceil
from modterm.components. definitions import TableContents


class ScrollableList:
    def __init__(self, height, width, y, x, normal_text, highlighted_text, empty_list_message="No data to display"):
        self.normal_text = normal_text
        self.highlighted_text = highlighted_text
        self.empty_list_message = empty_list_message
        self.height = height - 2
        self.width = width
        self.window = curses.newwin(height, width, y, x)
        self.position = 1
        self.page = 1
        self.data_rows = []
        self.header = None
        self.keymap = {
            curses.KEY_DOWN: self.step_down,
            curses.KEY_UP: self.step_up,
            curses.KEY_LEFT: self.page_up,
            curses.KEY_RIGHT: self.page_down,
            curses.KEY_PPAGE: self.page_up,
            curses.KEY_NPAGE: self.page_down,
            104: self.page_up,
            106: self.step_up,
            107: self.step_down,
            108: self.page_down
        }

    def draw(self, table_data: TableContents = None):
        self.window.erase()
        self.window.border(0)
        self.window.box()
        if table_data is not None and table_data.header is not None and self.header != table_data.header:
            self.header = table_data.header
        if self.header is None:
            height = self.height
            start_row = 0
        else:
            height = self.height - 1
            start_row = 1
        if table_data is not None and table_data.rows is not None and self.data_rows != table_data.rows:
            self.data_rows = table_data.rows
            self.page = 1
            self.position = 1
        if len(self.data_rows) == 0:
            self.window.addstr(1, 1, self.empty_list_message)
            self.window.refresh()
            return

        columns = 0
        if self.header is not None:
            header_string = ""
            for idx, item in enumerate(self.header):
                if len(header_string) + len(item) < self.width - 2:
                    columns = idx
                    header_string += item + " "
                else:
                    break
            self.window.addstr(1, 2, header_string, self.normal_text)

        for i in range(1 + (height * (self.page - 1)), min(height + 1 + (height * (self.page - 1)), len(self.data_rows) + 1)):
            if type(self.data_rows[i-1]) is list:
                string = " ".join(x for x in self.data_rows[i-1])
            else:
                string = str(self.data_rows[i-1])
            if (i + (height * (self.page - 1)) == self.position + (height * (self.page - 1))):
                self.window.addstr(i - (height * (self.page - 1)) + start_row, 2, string, self.highlighted_text)
            else:
                self.window.addstr(i - (height * (self.page - 1)) + start_row, 2, string, self.normal_text)
            if i == height:
                break
        self.window.refresh()

    def step_down(self):
        if self.header is None:
            height = self.height
            start_row = 0
        else:
            height = self.height - 1
            start_row = 1
        if self.position < min(height + (height * (self.page - 1)), len(self.data_rows)):
            self.position = self.position + 1
        elif self.page < int(ceil(len(self.data_rows)/height)):
            self.page = self.page + 1
            self.position = 1 + (height * (self.page - 1))

    def step_up(self):
        if self.header is None:
            height = self.height
        else:
            height = self.height - 1
        if self.page == 1:
            if self.position > 1:
                self.position = self.position - 1
        else:
            if self.position > (1 + (height * (self.page - 1))):
                self.position = self.position - 1
            else:
                self.page = self.page - 1
                self.position = height + (height * (self.page - 1))

    def page_up(self):
        if self.header is None:
            height = self.height
        else:
            height = self.height - 1
        if self.page > 1:
            self.page = self.page - 1
            self.position = 1 + (height * (self.page) - 1)
        else:
            self.position = 1

    def page_down(self):
        if self.header is None:
            height = self.height
        else:
            height = self.height - 1
        if self.page < int(ceil(len(self.data_rows)/height)):
            self.page = self.page + 1
            self.position = (1 + (height * (self.page - 1)))
        else:
            self.position = len(self.data_rows)

    def get_current_row_data(self):
        try:
            return self.data_rows[self.position - 1]
        except IndexError:
            return None

    def check_navigate(self, keystroke):
        try:
            self.keymap[keystroke]()
        except KeyError:
            pass


class SelectWindow:
    def __init__(self, screen,  height, width, y, x, normal_text, highlighted_text, options_list, empty_list_message="No data to display"):
        self.screen = screen
        self.empty_list_message = empty_list_message
        self.scrollable_list = ScrollableList(height, width, y, x, normal_text, highlighted_text, self.empty_list_message)
        self.options = options_list

    def get_selection(self):
        self.scrollable_list.draw(TableContents(None, self.options))
        x = self.screen.getch()
        while x != 27:
            if x == curses.KEY_DOWN:
                self.scrollable_list.step_down()
            if x == curses.KEY_UP:
                self.scrollable_list.step_up()
            if x == curses.KEY_LEFT or x == curses.KEY_PPAGE:
                self.scrollable_list.page_up()
            if x == curses.KEY_RIGHT or x == curses.KEY_NPAGE:
                self.scrollable_list.page_down()
            if x == ord("\n"):
                return self.scrollable_list.get_current_row_data()
            self.scrollable_list.draw()
            x = self.screen.getch()
        return None
