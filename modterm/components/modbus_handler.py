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
from datetime import datetime
from typing import Optional, List, Union
from dataclasses import dataclass
from pymodbus.client import ModbusTcpClient
from pymodbus.pdu import ExceptionResponse, ModbusExceptions
from pymodbus.exceptions import ConnectionException, ModbusIOException
from pymodbus.client.serial import ModbusSerialClient
from modterm.components.definitions import HOLDING, INPUT, LittleEndian, ModbusConfig, ReadConfig, WriteConfig, \
    TableContents, TCP, UnitSweepConfig, COIL, DISCRETE, COIL_WRITE, IpSweepConfig
import logging
from pymodbus import pymodbus_apply_logging_config
from pymodbus.payload import BinaryPayloadDecoder as Decoder
from pymodbus.payload import BinaryPayloadBuilder as Builder

pymodbus_apply_logging_config(logging.CRITICAL)


(INVALID, WORD, DWORD) = range(3)

logger = logging.getLogger("ModTerm")


@dataclass
class Header:
    title: str
    padding: int


word_columns = [
    Header("Idx", 4),
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


bits_columns = [
    Header("Idx", 4),
    Header("Addr", 6),
    Header("HAdr", 5),
    Header("HexV", 5),
    Header("Val", 6)]


WORDS_HEADER_ROW = []
for header_def in word_columns:
    WORDS_HEADER_ROW.append("{number: >{align}}".format(number=header_def.title, align=header_def.padding))


BITS_HEADER_ROW = []
for header_def in bits_columns:
    BITS_HEADER_ROW.append("{number: >{align}}".format(number=header_def.title, align=header_def.padding))


class ModbusHandler:
    def __init__(self, status_text_callback: callable):
        self.status_text_callback = status_text_callback
        self.last_data = []
        self.last_command = None

    def get_client(self,
                   modbus_config: ModbusConfig,
                   timeout: float = None,
                   multicast_enable=False) -> Optional[Union[ModbusTcpClient, ModbusSerialClient]]:
        if modbus_config.mode == TCP:
            client = ModbusTcpClient(host=modbus_config.ip,
                                     port=modbus_config.port,
                                     timeout=1 if timeout is None else timeout,
                                     broadcast_enable=multicast_enable)
        else:
            client = ModbusSerialClient(port=modbus_config.interface,
                                        baudrate=modbus_config.baud_rate,
                                        bytesize=modbus_config.bytesize,
                                        parity=modbus_config.parity,
                                        stopbits=modbus_config.stopbits,
                                        timeout=1 if timeout is None else timeout,
                                        broadcast_enable=multicast_enable)
        try:
            client.connect()
        except ConnectionException:
            self.status_text_callback("Failed to connect", failed=True)
            return None
        return client

    def get_data_rows(self, screen, modbus_config: ModbusConfig, read_config: ReadConfig) -> Optional[TableContents]:
        client = self.get_client(modbus_config)
        if client is None:
            return None

        self.status_text_callback("Starting transaction")
        if read_config.command == HOLDING:
            self.last_data = self.get_register_blocks(screen, client.read_holding_registers, read_config)
        elif read_config.command == INPUT:
            self.last_data = self.get_register_blocks(screen, client.read_input_registers, read_config)
        elif read_config.command == DISCRETE:
            self.last_data = self.get_register_blocks(screen, client.read_discrete_inputs, read_config, bits=True)
        else:
            self.last_data = self.get_register_blocks(screen, client.read_coils, read_config, bits=True)
        self.last_command = read_config.command
        return self.process_result(modbus_config, read_config)

    def process_words(self, modbus_config: ModbusConfig, read_config: ReadConfig) -> TableContents:
        return_rows = []
        start_reg = read_config.start
        for idx, register in enumerate(self.last_data):
            is_word = bool(register is not None)
            is_dword = bool(len(self.last_data) > idx + 1 and self.last_data[idx+1] is not None)
            return_row = []
            if is_word:
                decoder = Decoder.fromRegisters(self.last_data[idx:idx + 2] if is_dword else self.last_data[idx:idx + 1],
                                                byteorder="<" if modbus_config.byte_order == LittleEndian else ">",
                                                wordorder="<" if modbus_config.word_order == LittleEndian else ">")

            for header in word_columns:
                if header.title == "Idx":
                    return_row.append('{num: >{width}}'.format(num=idx, width=header.padding))
                    continue

                if header.title == "Addr":
                    return_row.append('{num: >{width}}'.format(num=idx + start_reg, width=header.padding))
                    continue
                if header.title == "HAdr":
                    return_row.append("{num: >{padding}X}".format(num=idx+start_reg, padding=header.padding))
                    continue

                if not is_word:
                    return_row.append("{text: >{padding}}".format(text="--", padding=header.padding))
                    continue

                if header.title == "HexV":
                    return_row.append("{num: >{padding}X}".format(num=register, padding=header.padding))
                    continue
                if header.title == "U16":
                    decoder.reset()
                    return_row.append("{num: >{padding}}".format(num=decoder.decode_16bit_uint(),
                                                                 padding=header.padding))
                    continue
                if header.title == "I16":
                    decoder.reset()
                    return_row.append("{num: >{padding}}".format(num=decoder.decode_16bit_int(),
                                                                 padding=header.padding))
                    continue
                if not is_dword and header.title not in ("St", "Bits"):
                    return_row.append("{text: >{padding}}".format(text="--", padding=header.padding))
                    continue

                if header.title == "U32":
                    decoder.reset()
                    return_row.append("{num: >{padding}}".format(num=decoder.decode_32bit_uint(),
                                                                 padding=header.padding))
                    continue
                if header.title == "I32":
                    decoder.reset()
                    return_row.append("{num: >{padding}}".format(num=decoder.decode_32bit_int(),
                                                                 padding=header.padding))
                    continue
                if header.title == "F32":
                    decoder.reset()
                    number = decoder.decode_32bit_float()
                    number_string = "{0:0.3f}".format(number)
                    if len(str(number_string)) > 11:
                        number_string = "{0:0.5e}".format(number)
                    return_row.append("{num: >{padding}}".format(num=number_string, padding=header.padding))
                    continue
                if header.title == "St":
                    if not modbus_config.byte_order == LittleEndian:
                        first = register >> 8
                        second = register & 0xff
                    else:
                        second = register >> 8
                        first = register & 0xff
                    first = chr(first) if 31 < first < 127 else "-"
                    second = chr(second) if 31 < second < 127 else "-"
                    return_row.append("{}{}".format(first if len(first) != 0 else "-",
                                                    second if len(second) != 0 else "-"))
                    continue

                if header.title == "Bits":
                    decoder.reset()
                    bits = "{0:016b}".format(decoder.decode_16bit_uint())
                    return_row.append(f"{bits[0:4]} {bits[4:8]} {bits[8:12]} {bits[12:16]}")
                    continue
            return_rows.append(return_row)
        date = datetime.now().strftime("%H:%M:%S")
        read_type = "Holding" if read_config.command == HOLDING else "Input"
        if modbus_config.mode == TCP:
            source = f"{modbus_config.ip}:{modbus_config.port} unit: {read_config.unit}"
        else:
            source = f"{modbus_config.interface}:{modbus_config.baud_rate}/{modbus_config.bytesize}{modbus_config.parity}{modbus_config.stopbits} unit {read_config.unit}"

        return TableContents(header=WORDS_HEADER_ROW,
                             rows=return_rows,
                             title=f"{date} - {read_type} registers {read_config.start} -> {read_config.start + read_config.number} from {source}",)

    def process_bits(self, modbus_config: ModbusConfig, read_config: ReadConfig):
        return_rows = []
        start_bit = read_config.start
        for idx, bit in enumerate(self.last_data):
            return_row = []
            for header in bits_columns:
                if header.title == "Idx":
                    return_row.append('{num: >{width}}'.format(num=idx, width=header.padding))

                if header.title == "Addr":
                    return_row.append('{num: >{width}}'.format(num=idx + start_bit, width=header.padding))
                    continue

                if header.title == "HAdr":
                    return_row.append("{num: >{padding}X}".format(num=idx+start_bit, padding=header.padding))
                    continue

                if header.title == "HexV":
                    return_row.append("{num: >{padding}X}".format(num=bit, padding=header.padding)
                                      if bit is not None else "{num: >{padding}}".format(num="-", padding=header.padding))
                    continue

                if header.title == "Val":
                    return_row.append("{num: >{padding}}".format(num=str(int(bit)) if bit is not None else "-", padding=header.padding))
                    continue
            return_rows.append(return_row)
        date = datetime.now().strftime("%H:%M:%S")
        read_type = "Coils" if read_config.command == COIL else "Discrete inputs"
        if modbus_config.mode == TCP:
            source = f"{modbus_config.ip}:{modbus_config.port} unit: {read_config.unit}"
        else:
            source = f"{modbus_config.interface}:{modbus_config.baud_rate}/{modbus_config.bytesize}{modbus_config.parity}{modbus_config.stopbits} unit {read_config.unit}"
        return TableContents(header=BITS_HEADER_ROW,
                             rows=return_rows,
                             title=f"{date} - {read_type} {read_config.start} -> {read_config.start + read_config.number} from {source}",)

    def process_result(self, modbus_config: ModbusConfig, read_config: ReadConfig) -> Optional[TableContents]:
        if self.last_data == [] or self.last_command is None:
            return None
        if self.last_command == INPUT or self.last_command == HOLDING:
            try:
                return self.process_words(modbus_config, read_config)
            except Exception:
                logger.critical("Failed to process registers", exc_info=True)
        elif self.last_command == COIL or self.last_command == DISCRETE:
            try:
                return self.process_bits(modbus_config, read_config)
            except Exception:
                logger.critical("Failed to process bits", exc_info=True)

    def read_registers(self, command: callable, address: int, count: int, slave: int, bits:bool = False) -> List[Optional[int]]:
        try:
            result = command(address=address, count=count, slave=slave)
        except ConnectionException as e:
            self.status_text_callback(f"Failed to connect: {repr(e)}", failed=True)
            return [None] * count
        if result.isError():
            self.status_text_callback(f"Failed to read {slave}, {address}, {count}, {result}", failed=True)
            return [None] * count
        self.status_text_callback(f"Successfully read {slave}, {address}, {count}")
        if not bits:
            return result.registers
        return result.bits[:count]

    def get_register_blocks(self, screen, command: callable, read_config: ReadConfig, bits: bool = False) -> List[Optional[int]]:
        if read_config.number <= read_config.block_size:
            return self.read_registers(command,
                                       address=read_config.start,
                                       count=read_config.number,
                                       slave=read_config.unit,
                                       bits=bits)
        regs_to_return = []
        start = read_config.start
        count = read_config.number
        number = read_config.block_size
        count -= read_config.block_size
        screen.nodelay(True)
        while True:
            regs = self.read_registers(command, address=start, count=number, slave=read_config.unit, bits=bits)
            key = screen.getch()
            if key == 27:
                self.status_text_callback("Interrupted!", failed=True)
                return regs_to_return
            if regs is None:
                regs_to_return += [None] * number
                continue
            else:
                regs_to_return += regs
            if count == 0:
                return regs_to_return
            if read_config.block_size < count:
                start += number
                number = read_config.block_size
                count -= read_config.block_size
            else:
                start += number
                number = count
                count = 0

    def write_registers(self, modbus_config: ModbusConfig, write_config: WriteConfig, format_mapping: dict):
        unit_id = 0 if write_config.multicast else write_config.unit

        client = self.get_client(modbus_config,
                                 multicast_enable=write_config.multicast)
        if client is None:
            return None
        if write_config.command != COIL_WRITE:
            format = format_mapping[write_config.format]
            encoder = Builder(wordorder="<" if modbus_config.word_order == LittleEndian else ">",
                              byteorder="<" if modbus_config.byte_order == LittleEndian else ">")
            encode_call = getattr(encoder, "add_{}".format(format))
            try:
                encode_call(write_config.value)
            except Exception as e:
                self.status_text_callback(f"Failed to encode value! {repr(e)}", failed=True)
                return
        try:
            if write_config.command == COIL_WRITE:
                try:
                    value = bool(int(write_config.value))
                except Exception as e:
                    self.status_text_callback(f"Failed to convert coil value: {e}", failed=True)
                    return
                result = (client.write_coil(address=int(write_config.address),
                                            value=value,
                                            slave=unit_id))
            else:
                result = client.write_registers(address=int(write_config.address),
                                                values=encoder.to_registers(),
                                                slave=unit_id)
        except Exception as e:
            self.status_text_callback(f"Failed to write register: {e}", failed=True)
            return
        if write_config.multicast:
            self.status_text_callback("Multicast message sent with unit ID 0, no response expected")
            return
        if hasattr(result, "isError") and result.isError():
            self.status_text_callback(f"Failed to write register: {result}", failed=True)
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
        elif sweep_config.command == COIL:
            command = client.read_coils
        elif sweep_config.command == DISCRETE:
            command = client.read_discrete_inputs
        else:
            command = client.read_input_registers
        unit = sweep_config.start_unit
        screen.nodelay(True)
        while unit <= sweep_config.last_unit:
            key = screen.getch()
            if key == 27:
                self.status_text_callback("Interrupted!", failed=True)
                break
            try:
                result = command(address=sweep_config.start_register,
                                 count=sweep_config.number_of_registers,
                                 slave=unit)
            except Exception as e:
                self.status_text_callback(f"Unit {unit}: No response: {repr(e)}", failed=True)
                to_return.rows.append([" {num: >{width}}".format(num=unit, width=3),
                                       f" No response: {repr(e).strip()}"])
            else:
                if result.isError():
                    if type(result) == ModbusIOException:
                        self.status_text_callback(f"Unit {unit}: No response: ModbusIOException", failed=True)
                        to_return.rows.append([" {num: >{width}}".format(num=unit, width=3),
                                               f" No response: ModbusIOException"])
                    elif type(result) == ExceptionResponse:
                        self.status_text_callback(f"Unit {unit}: Received exception: {ModbusExceptions.decode(result.exception_code)}", failed=True)
                        to_return.rows.append([" {num: >{width}}".format(num=unit, width=3),
                                               f" Received exception: {result}"])
                    else:
                        self.status_text_callback(f"Unit {unit}: Received no known response", failed=True)
                        to_return.rows.append([" {num: >{width}}".format(num=unit, width=3),
                                               f" No know response received: {result}"])
                else:
                    self.status_text_callback(f"Unit {unit}: Valid register response received!")
                    to_return.rows.append([" {num: >{width}}".format(num=unit, width=3),
                                           f" Valid modbus register response received!"])
            unit += 1
        return to_return

    def ip_sweep(self, screen, modbus_config, confiuration: IpSweepConfig) -> Optional[TableContents]:
        to_return = TableContents(header=[
            "IP Address",
            "      Scan result"
        ], rows=[])
        address = confiuration.start_address
        screen.nodelay(True)
        while address <= confiuration.end_address:
            key = screen.getch()
            if key == 27:
                self.status_text_callback("Interrupted!", failed=True)
                break
            ip = confiuration.subnet + f".{address}"
            client = ModbusTcpClient(host=ip,
                                     port=confiuration.port,
                                     timeout=confiuration.timeout)
            if confiuration.command == HOLDING:
                command = client.read_holding_registers
            elif confiuration.command == COIL:
                command = client.read_coils
            elif confiuration.command == DISCRETE:
                command = client.read_discrete_inputs
            else:
                command = client.read_input_registers
            try:
                result = command(address=confiuration.start_register,
                                 count=confiuration.number_of_registers,
                                 slave=confiuration.unit_id)
            except Exception as e:
                self.status_text_callback(f"{ip}: No response: {repr(e)}", failed=True)
                to_return.rows.append(["{num: <{width}}".format(num=ip, width=15),
                                       f" No response: {repr(e).strip()}"])
            else:
                if result.isError():
                    self.status_text_callback(f"{ip}: No response: {repr(result)}", failed=True)
                    to_return.rows.append(["{num: <{width}}".format(num=ip, width=15),
                                           f" No response: {repr(result).strip()}"])
                else:
                    self.status_text_callback(f"{ip}: Valid register response received!")
                    to_return.rows.append(["{num: <{width}}".format(num=ip, width=15),
                                           f" Valid modbus register response received!"])

            address += 1
        return to_return


@dataclass
class HistoryItem:
    table_content: TableContents
    modbus_handler: ModbusHandler
