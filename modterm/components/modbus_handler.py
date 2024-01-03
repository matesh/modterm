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
from typing import Optional, List, Union
from dataclasses import dataclass
from pymodbus.client import ModbusTcpClient
from pymodbus.pdu import ExceptionResponse, ModbusExceptions
from pymodbus.exceptions import ConnectionException, ModbusIOException
from pymodbus.client.serial import ModbusSerialClient
from modterm.components.definitions import HOLDING, INPUT, LittleEndian, ModbusConfig, ReadConfig, WriteConfig, \
                                           TableContents, TCP, UnitSweepConfig
import logging
from pymodbus import pymodbus_apply_logging_config
from pymodbus.payload import BinaryPayloadDecoder, BinaryPayloadBuilder
from modterm.components.debug_output import log

pymodbus_apply_logging_config(logging.CRITICAL)


@dataclass
class Header:
    title: str
    padding: int


word_columns = [
    Header("Addr", 6),
    Header("HAdr", 5),
    Header("HexV", 5),
    Header("U16", 6),
    Header("I16", 7),
    Header("U32", 11),
    Header("I32", 12),
    Header("F32", 12),
    Header("St", 2),
    Header("Bits", 19)]


WORDS_HEADER = []
for header_def in word_columns:
    WORDS_HEADER.append("{number: >{align}}".format(number=header_def.title, align=header_def.padding))


class ModbusHandler:
    def __init__(self, status_text_callback: callable):
        self.status_text_callback = status_text_callback
        self.last_data = []
        self.last_command = None

    def get_client(self, modbus_config: ModbusConfig, timeout: float = None) -> Optional[Union[ModbusTcpClient,
                                                                                               ModbusSerialClient]]:
        if modbus_config.mode == TCP:
            client = ModbusTcpClient(host=modbus_config.ip,
                                     port=modbus_config.port,
                                     timeout=1 if timeout is None else timeout)
        else:
            client = ModbusSerialClient(port=modbus_config.interface,
                                        baudrate=modbus_config.baud_rate,
                                        bytesize=modbus_config.bytesize,
                                        parity=modbus_config.parity,
                                        stopbits=modbus_config.stopbits,
                                        timeout=1 if timeout is None else timeout)
        try:
            client.connect()
        except ConnectionException:
            self.status_text_callback("Failed to connect")
            return None
        return client

    def get_data_rows(self, screen, modbus_config: ModbusConfig, read_config: ReadConfig) -> Optional[TableContents]:
        client = self.get_client(modbus_config)
        if client is None:
            return None

        self.status_text_callback("Starting transaction")
        if read_config.command == HOLDING:
            self.last_data = self.get_registers(screen, client.read_holding_registers, read_config)
            self.last_command = read_config.command
        else:  # elif read_config.command == INPUT:
            self.last_data = self.get_registers(screen, client.read_input_registers, read_config)
            self.last_command = read_config.command
        # else:
        #     self.last_data = self.get_registers(client.read_coils, read_config)
        #     self.last_command = read_config.command
        return self.process_result(modbus_config, read_config)

    def process_words(self, modbus_config: ModbusConfig, read_config: ReadConfig) -> TableContents:
        return_rows = []
        start_reg = read_config.start
        byteorder = "<" if modbus_config.byte_order == LittleEndian else ">"
        wordorder = "<" if modbus_config.word_order == LittleEndian else ">"
        for idx, register in enumerate(self.last_data):
            this_failed = False
            other_failed = False
            if register is None:
                this_failed = True
            if len(self.last_data) <= idx + 1 or self.last_data[idx+1] is None:
                other_failed = True
            return_row = []

            if other_failed and not this_failed:
                decoder = BinaryPayloadDecoder.fromRegisters(self.last_data[idx:idx + 1],
                                                             byteorder=byteorder,
                                                             wordorder=wordorder)
            elif not this_failed and not other_failed:
                decoder = BinaryPayloadDecoder.fromRegisters(self.last_data[idx:idx + 2],
                                                             byteorder=byteorder,
                                                             wordorder=wordorder)
            else:
                for header in word_columns:
                    if header.title == "St":
                        return_row.append("--")
                    else:
                        return_row.append("{text: >{padding}}".format(text="N/A", padding=header.padding))
                return_rows.append(return_row)
                continue

            for header in word_columns:
                if header.title == "Addr":
                    return_row.append('{num: >{width}}'.format(num=idx + start_reg, width=header.padding))
                if header.title == "HAdr":
                    return_row.append("{num: >{padding}X}".format(num=idx+start_reg, padding=header.padding))
                if header.title == "HexV":
                    return_row.append("{num: >{padding}X}".format(num=register, padding=header.padding))
                if header.title == "U16":
                    decoder.reset()
                    return_row.append("{num: >{padding}}".format(num=decoder.decode_16bit_uint(),
                                                                 padding=header.padding))
                if header.title == "I16":
                    decoder.reset()
                    return_row.append("{num: >{padding}}".format(num=decoder.decode_16bit_int(),
                                                                 padding=header.padding))
                if header.title == "U32":
                    if other_failed:
                        return_row.append("{text: >{padding}}".format(text="N/A", padding=header.padding))
                    else:
                        decoder.reset()
                        return_row.append("{num: >{padding}}".format(num=decoder.decode_32bit_uint(),
                                                                     padding=header.padding))
                if header.title == "I32":
                    if other_failed:
                        return_row.append("{text: >{padding}}".format(text="N/A", padding=header.padding))
                    else:
                        decoder.reset()
                        return_row.append("{num: >{padding}}".format(num=decoder.decode_32bit_int(),
                                                                     padding=header.padding))
                if header.title == "F32":
                    if other_failed:
                        return_row.append("{text: >{padding}}".format(text="N/A", padding=header.padding))
                    else:
                        decoder.reset()
                        number = decoder.decode_32bit_float()
                        number_string = "{0:0.3f}".format(number)
                        if len(str(number_string)) > 11:
                            number_string = "{0:0.5e}".format(number)
                        return_row.append("{num: >{padding}}".format(num=number_string, padding=header.padding))
                if header.title == "St":
                    if register != 0x00:
                        if not modbus_config.byte_order == LittleEndian:
                            first = register >> 8
                            second = register & 0xff
                        else:
                            second = register >> 8
                            first = register & 0xff
                        first = chr(first) if first > 31 and first != 127 else "-"
                        second = chr(second) if second > 31 and second != 127 else "-"
                        return_row.append("{}{}".format(first if len(first) != 0 else "-",
                                                        second if len(second) != 0 else "-"))
                    else:
                        return_row.append("--")

                if header.title == "Bits":
                    decoder.reset()
                    bits = "{0:016b}".format(decoder.decode_16bit_uint())
                    return_row.append(f"{bits[0:4]} {bits[4:8]} {bits[8:12]} {bits[12:16]}")
            return_rows.append(return_row)
        return TableContents(header=WORDS_HEADER, rows=return_rows)

    # def process_coils(self, modbus_config: ModbusConfig, read_config: ReadConfig):
    #     return [""], [""]

    def process_result(self, modbus_config: ModbusConfig, read_config: ReadConfig) -> Optional[TableContents]:
        if self.last_data == [] or self.last_command is None:
            return None
        if self.last_command == INPUT or self.last_command == HOLDING:
            return self.process_words(modbus_config, read_config)
        # return self.process_coils(modbus_config)

    def read_registers(self, command: callable, address: int, count: int, slave: int) -> List[Optional[int]]:
        try:
            result = command(address=address, count=count, slave=slave)
        except ConnectionException as e:
            self.status_text_callback(f"Failed to connect: {repr(e)}")
            return [None] * count
        if result.isError():
            self.status_text_callback(f"Failed to read {slave}, {address}, {count}, {result}")
            return [None] * count
        self.status_text_callback(f"Successfully read {slave}, {address}, {count}")
        return result.registers

    def get_register_blocks(self, command: callable, read_config: ReadConfig) -> List[Optional[int]]:
        if read_config.number < 120:
            return self.read_registers(command,
                                       address=read_config.start,
                                       count=read_config.number,
                                       slave=read_config.unit)
        regs_to_return = []
        start = read_config.start
        count = read_config.number
        number = 120
        count -= 120
        while True:
            regs = self.read_registers(command, address=start, count=number, slave=read_config.unit)
            if regs is None:
                regs_to_return += [None] * number
                continue
            else:
                regs_to_return += regs
            if count == 0:
                return regs_to_return
            if 120 < count:
                start += number
                number = 120
                count -= 120
            else:
                start += number
                number = count
                count = 0

    def read_registers_individually(self, screen, command: callable, read_config:ReadConfig) -> List[Optional[int]]:
        regs_to_return = []
        screen.nodelay(True)
        for register in range(read_config.start, read_config.number):
            regs_to_return += self.read_registers(command, address=register, count=1, slave=read_config.unit)
            key = screen.getch()
            if key == 27:
                self.status_text_callback("Interrupted!")
                break
            curses.napms(100)
        screen.nodelay(False)
        return regs_to_return

    def get_registers(self, screen, command: callable, read_config: ReadConfig) -> List[Optional[int]]:
        if read_config.individuals:
            return self.read_registers_individually(screen, command, read_config)
        return self.get_register_blocks(command, read_config)

    def write_registers(self, modbus_config: ModbusConfig, write_config: WriteConfig, format_mapping: dict):
        # if write_config["multicast"]
        client = self.get_client(modbus_config)
        if client is None:
            return None
        format = format_mapping[write_config.format]
        encoder = BinaryPayloadBuilder(wordorder="<" if modbus_config.word_order == LittleEndian else ">",
                                       byteorder="<" if modbus_config.byte_order == LittleEndian else ">")
        encode_call = getattr(encoder, "add_{}".format(format))
        encode_call(int(write_config.value))
        try:
            result = client.write_registers(address=int(write_config.address),
                                            values=encoder.to_registers(),
                                            slave=write_config.unit)
        except Exception as e:
            self.status_text_callback(f"Failed to write register: {e}")
            return
        if hasattr(result, "isError") and result.isError():
            self.status_text_callback(f"Failed to write register: {result}")
        else:
            self.status_text_callback(f"Register(s) successfully written")

    def unit_sweep(self, screen, modbus_config: ModbusConfig, sweep_config: UnitSweepConfig) -> Optional[TableContents]:
        to_return = TableContents(header=[
            "Unit",
            " Scan result"
        ], rows=[])
        client = self.get_client(modbus_config, timeout=sweep_config.timeout)
        if sweep_config.command == HOLDING:
            command = client.read_holding_registers
        else:
            command = client.read_input_registers
        unit = sweep_config.start_unit
        screen.nodelay(True)
        while unit <= sweep_config.last_unit:
            key = screen.getch()
            if key == 27:
                self.status_text_callback("Interrupted!")
                break
            try:
                result = command(address=sweep_config.start_register,
                                 count=sweep_config.number_of_registers,
                                 slave=unit)
            except Exception as e:
                to_return.rows += [" {num: >{width}}".format(num=unit, width=4),
                                   f"No response: {repr(e)}"]
            else:
                if result.isError():
                    if type(result) == ModbusIOException:
                        self.status_text_callback(f"Unit {unit}: No response: ModbusIOException")
                        to_return.rows.append(["{num: >{width}}".format(num=unit, width=4),
                                               f" No response: ModbusIOException"])
                    elif type(result) == ExceptionResponse:
                        self.status_text_callback(f"Unit {unit}: Received exception: {ModbusExceptions.decode(result.exception_code)}")
                        to_return.rows.append(["{num: >{width}}".format(num=unit, width=4),
                                               f" Received exception: {result}"])
                    else:
                        self.status_text_callback(f"Unit {unit}: Received no known response")
                        to_return.rows.append(["{num: >{width}}".format(num=unit, width=4),
                                               f" Received no known response: {result}"])
                else:
                    self.status_text_callback(f"Unit {unit}: Valid register response received!")
                    to_return.rows.append(["{num: >{width}}".format(num=unit, width=4),
                                           f" Valid modbus register response received!"])
            unit += 1
        screen.nodelay(False)
        return to_return
