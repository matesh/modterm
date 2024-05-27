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

from enum import Enum
from typing import List, Optional
from dataclasses import dataclass
import inspect

CONFIG_DIR = "modterm"

HOLDING = "Read holding registers"
INPUT = "Read input registers"
COIL = "Read coils"
DISCRETE = "Read discrete inputs"

LittleEndian = "Little endian"
BigEndian = "Big endian"

TCP = "TCP"
RTU = "RTU"

formats = {
    "UINT16": "16bit_uint",
    "INT16": "16bit_int",
    "UINT32": "32bit_uint",
    "INT32": "32bit_int",
    # "FLOAT32": "32bit_float"
}


class ConfigType(Enum):
    ModbusConfig = "modbus_config.conf"
    ReadConfig = "read_config.conf"
    WriteConfig = "write_config.conf"
    UnitSweepConfig = "scan_config.conf"
    ExportConfig = "export.conf"


@dataclass
class ModbusConfig:
    mode: str = TCP
    ip: str = "localhost"
    port: int = 502
    interface: str = "/dev/ttyO1"
    baud_rate: int = 9600
    parity: str = "N"
    bytesize: int = 8
    stopbits: int = 1
    word_order: str = BigEndian
    byte_order: str = BigEndian

    @classmethod
    def from_dict(cls, config_dict: dict):
        return cls(**{
            k: v for k, v in config_dict.items()
            if k in inspect.signature(cls).parameters
        })


@dataclass
class ReadConfig:
    command: str = HOLDING
    start: int = 0
    number: int = 1
    unit: int = 1
    block_size: int = 125

    @classmethod
    def from_dict(cls, config_dict):
        return cls(**{
            k: v for k, v in config_dict.items()
            if k in inspect.signature(cls).parameters
        })


@dataclass
class WriteConfig:
    address: int = 0
    unit: int = 1
    format: str = list(formats.keys())[0]
    multicast: bool = False
    value: float = 1

    @classmethod
    def from_dict(cls, config_dict):
        return cls(**{
            k: v for k, v in config_dict.items()
            if k in inspect.signature(cls).parameters
        })


@dataclass
class ExportConfig:
    last_dir: Optional[str] = None
    last_file_name: str = None
    last_file_type: str = ".csv"

    @classmethod
    def from_dict(cls, config_dict):
        return cls(**{
            k: v for k, v in config_dict.items()
            if k in inspect.signature(cls).parameters
        })


@dataclass
class UnitSweepConfig:
    start_unit: int = 1
    last_unit: int = 255
    command: str = HOLDING
    start_register: int = 0
    number_of_registers: int = 1
    timeout: float = 0.2

    @classmethod
    def from_dict(cls, config_dict):
        return cls(**{
            k: v for k, v in config_dict.items()
            if k in inspect.signature(cls).parameters
        })


@dataclass
class TableContents:
    header: Optional[List[str]]
    rows: List[List[str]]
