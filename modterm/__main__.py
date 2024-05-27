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
import os.path
import sys
import time
from os import environ, path
import logging
from logging.handlers import RotatingFileHandler
from modterm.components.config_handler import save_modbus_config, load_read_config, get_project_dir

logger = logging.getLogger("ModTerm")
logger.setLevel('INFO')

if (project_dir := get_project_dir()) is not None:
    file_handler = RotatingFileHandler(path.join(project_dir, "modterm.log"),
                                       maxBytes=2000000,
                                       backupCount=3,
                                       errors='replace')
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(file_handler)
else:
    # Or else?
    pass

from modterm.components.help import display_help
from modterm.components.scrollable_list import ScrollableList
from modterm.components.header_menu import HeaderMenu
from modterm.components.read_registers_menu import ReadRegistersMenu
from modterm.components.write_registers_menu import WriteRegistersMenu
from modterm.components.unit_sweep_menu import UnitSweepMenu
from modterm.components.popup_message import show_popup_message
from modterm.components.export_menu import ExportMenu


def app(screen):
    screen.keypad(1)
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)
    highlighted_text = curses.color_pair(1)
    normal_text = curses.A_NORMAL
    curses.curs_set(0)
    screen.refresh()
    menu = HeaderMenu(screen, normal_text, highlighted_text)
    data_window = ScrollableList(screen.getmaxyx()[0] - 5,
                                 screen.getmaxyx()[1],
                                 5,
                                 0,
                                 normal_text,
                                 highlighted_text)
    data_window.draw()
    menu.draw()
    x = screen.getch()
    modbus_handler = None
    logger.info("ModTerm started up")
    while x != curses.KEY_F10:
        data_window.check_navigate(x)
        if menu.check_navigate(x):
            if modbus_handler is not None and modbus_handler is not None:

                table_data = modbus_handler.process_words(modbus_config=menu.configuration,
                                                          read_config=load_read_config())
                data_window.draw(table_data)

        if x == ord("\n"):
            # TODO enter press
            pass
        if x == curses.KEY_F1:
            display_help(screen)
        if x == ord("r"):
            read_registers_menu = ReadRegistersMenu(screen, normal_text, highlighted_text)
            if read_registers_menu.is_valid:
                table_data = read_registers_menu.read_registers(menu.configuration)
                if table_data is not None:
                    data_window.draw(table_data)
                    modbus_handler = read_registers_menu.modbus_handler
                save_modbus_config(menu.configuration)
        if x == ord("w"):
            write_registers_menu = WriteRegistersMenu(screen, normal_text, highlighted_text)
            if write_registers_menu.is_valid:
                write_registers_menu.write_register(menu.configuration)
                save_modbus_config(menu.configuration)
        if x == ord("s"):
            unit_sweep_menu = UnitSweepMenu(screen, normal_text, highlighted_text)
            if unit_sweep_menu.is_valid:
                table_data = unit_sweep_menu.sweep_units(modbus_config=menu.configuration)
                if table_data is not None:
                    data_window.draw(table_data)
                    modbus_handler = unit_sweep_menu.modbus_handler
                save_modbus_config(menu.configuration)
        if x == ord("e"):
            if data_window.header is None or len(data_window.data_rows) == 0:
                show_popup_message(screen, width=40, title="Error",
                                   message="Nothing to export!")
            else:
                export_menu = ExportMenu(screen, normal_text, highlighted_text, data_window.header, data_window.data_rows)
                if export_menu.is_valid:
                    export_menu.export_dialog()
        menu.draw()
        try:
            data_window.draw()
        except Exception:
            logger.critical("Failed to draw data window!", exc_info=True)
            show_popup_message(screen, width=40, title="Error", message="Failed to draw data window! Please refer to the log for details and report any software issues.")
        # screen.addstr(screen.getmaxyx()[0] - 1, screen.getmaxyx()[1] - 4, str(x))
        screen.refresh()
        x = screen.getch()


def main():
    rc = 0
    try:
        environ.setdefault('ESCDELAY', '25')
        stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        stdscr.keypad(True)
        try:
            curses.start_color()
        except:
            pass
        app(stdscr)
    except Exception as e:
        logger.critical("Critical error in main", exc_info=True)
        rc = 1
    finally:
        if 'stdscr' in locals():
            stdscr.keypad(False)
            curses.echo()
            curses.nocbreak()
            curses.endwin()
    if rc == 1:
        print(f"Critical error, please check the log file in {project_dir} and report any software issues")
    logger.info(f"ModTerm session exited with code {rc}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
