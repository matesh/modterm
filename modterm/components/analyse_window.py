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

from modterm.components.window_base import WindowBase
from pymodbus.payload import BinaryPayloadDecoder as Decoder


class AnalyseWindow:
    def __init__(self, screen, normal_text, highlighted_text, registers, logger):
        width = 150 if 152 < screen.getmaxyx()[1] else screen.getmaxyx()[1] - 2
        height = 23 if 22 < screen.getmaxyx()[0] else screen.getmaxyx()[0] - 2
        self.logger = logger
        self.screen = screen
        self.normal_text = normal_text
        self.highlighted_text = highlighted_text
        self.registers = registers

        self.column_paddings = [9, 0, 0, 0, 0]
        self.text_rows = [["Word/Byte", "Big/Big", "Big/Little", "Little/Big", "Little/Little"]]
        types = {
            "HEX16": "decode_16bit_uint",
            "UINT16": "decode_16bit_uint",
            "INT16": "decode_16bit_int",
            "HEX32": "decode_32bit_uint",
            "UINT32": "decode_32bit_uint",
            "INT32": "decode_32bit_int",
            "HEX64": "decode_64bit_uint",
            "UINT64": "decode_64bit_uint",
            "INT64": "decode_64bit_int",
            "Float32": "decode_32bit_float",
            "Float64": "decode_64bit_float",
        }

        format_strings = {
            "HEX16": "{:04X}",
            "HEX32": "{:08X}",
            "HEX64": "{:016X}",
        }

        decoders = [
            Decoder.fromRegisters(self.registers, wordorder=">", byteorder=">"),
            Decoder.fromRegisters(self.registers, wordorder=">", byteorder="<"),
            Decoder.fromRegisters(self.registers, wordorder="<", byteorder=">"),
            Decoder.fromRegisters(self.registers, wordorder="<", byteorder="<")]

        for type, decode_method in types.items():
            row = [type,]
            if self.column_paddings[0] < len(type):
                self.column_paddings[0] = len(type)
            for idx, decoder in enumerate(decoders, start=1):
                try:
                    if type.startswith("HEX"):
                        data = format_strings[type].format(getattr(decoder, decode_method)())
                        i = 4
                        while i < len(data):
                            data = data[:i] + " " + data[i:]
                            i += 5
                    else:
                        data = str(getattr(decoder, decode_method)())
                    decoder.reset()
                except Exception as e:
                    data = f"N/A"
                if self.column_paddings[idx] < len(data):
                    self.column_paddings[idx] = len(data)
                row.append(data)

            self.text_rows.append(row)

        self.bits = []
        i = 60
        cols = []
        while 0 <= i:
            cols.append("{num: >{padding}} ".format(num=i, padding=3))
            i -= 4
        self.bits.append("{num: >{padding}} ".format(num=" ".join(cols), padding=15 + 64 + 15))
        for formatter in ("UINT64", "UINT32", "UINT16"):
            for decoder_idx, decoder in enumerate(decoders, start=1):
                try:
                    largest_int = getattr(decoder, types[formatter])()
                except Exception:
                    break
                bit_string = "{0:064b}".format(largest_int)
                idx = 4
                while idx < len(bit_string):
                    bit_string = bit_string[:idx] + " " + bit_string[idx:]
                    idx += 5
                self.bits.append("{num: >{padding}} ".format(num=self.text_rows[0][decoder_idx], padding=13) + bit_string)
            else:
                break

        width = sum(self.column_paddings) + 8
        if width > screen.getmaxyx()[1] - 2:
            width = screen.getmaxyx()[1] - 2

        self.dialog = WindowBase(screen, height, width, title="Register details", min_width=40, min_height=15)
        self.is_valid = self.dialog.is_valid
        if not self.is_valid:
            return

    def draw(self):
        self.dialog.draw_window()
        self.logger.info(self.column_paddings)
        pos = 2
        for row in self.text_rows:
            self.logger.info(row)
            string = ""
            for pidx, value in enumerate(row):
                stuff = "{num: >{padding}} ".format(num=value, padding=self.column_paddings[pidx])
                string = string + stuff
                self.logger.info(string)
            self.dialog.window.addstr(pos, 2, string, self.normal_text)
            pos += 1

        pos += 1
        self.dialog.window.addstr(pos, 2, "Bits", self.normal_text)
        pos += 1

        for row in self.bits:
            self.dialog.window.addstr(pos, 2, row, self.normal_text)
            pos += 1

        self.dialog.window.refresh()
        x = self.screen.getch()
