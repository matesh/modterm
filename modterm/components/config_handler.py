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
from typing import Optional, Union, Type
from dataclasses import asdict
import os
import sys
from pathlib import Path
from json import loads, dumps
from modterm.components.definitions import CONFIG_DIR, ConfigType, ModbusConfig, ReadConfig, WriteConfig, \
    UnitSweepConfig, ExportConfig


class ConfigOperation(Enum):
    LOAD = "Load"
    SAVE = "Save"


def get_project_dir():
    if sys.platform.startswith("win"):
        appdata_dir = os.getenv('LOCALAPPDATA')
        project_dir = os.path.join(appdata_dir, CONFIG_DIR)
    elif sys.platform.startswith("linux"):
        home_dir = str(Path.home())
        project_dir = os.path.join(home_dir, ".config", CONFIG_DIR)
    elif sys.platform.startswith("darwin"):
        home_dir = str(Path.home())
        project_dir = os.path.join(home_dir, "Library", "ApplicationSupport", CONFIG_DIR)
    else:
        # TODO ?
        return None
    if project_dir is not None and not os.path.isdir(project_dir):
        try:
            os.makedirs(project_dir)
        except Exception:
            # TODO ?
            return None
    return project_dir


def config_file_manager(action: ConfigOperation,
                        config_type: ConfigType,
                        config_class: Optional[Union[Type[ModbusConfig],
                                                     Type[ReadConfig],
                                                     Type[WriteConfig],
                                                     Type[UnitSweepConfig],
                                                     Type[ExportConfig]]] = None,
                        config_to_save: Optional[Union[ModbusConfig,
                                                       ReadConfig,
                                                       WriteConfig,
                                                       UnitSweepConfig,
                                                       ExportConfig]] = None) -> Optional[Union[ModbusConfig,
                                                                                                ReadConfig,
                                                                                                WriteConfig,
                                                                                                UnitSweepConfig,
                                                                                                ExportConfig]]:

    if (config_dir := get_project_dir()) is None:
        # TODO log error
        return None

    if not os.path.isdir(config_dir):
        os.makedirs(config_dir)

    config_file = os.path.join(config_dir, config_type.value)

    if action == ConfigOperation.LOAD:
        if not os.path.isfile(config_file):
            loaded_config = {}
        try:
            with open(config_file, "r") as configfile:
                loaded_config: dict = loads(configfile.read())
        except Exception as e:
            loaded_config = {}
            pass
        return config_class.from_dict(loaded_config)
    else:
        if config_to_save is None:
            return None
        with open(config_file, "w") as configfile:
            configfile.write(dumps(asdict(config_to_save)))


def load_modbus_config() -> ModbusConfig:
    return config_file_manager(action=ConfigOperation.LOAD,
                               config_class=ModbusConfig,
                               config_type=ConfigType.ModbusConfig)


def save_modbus_config(config: ModbusConfig):
    return config_file_manager(action=ConfigOperation.SAVE,
                               config_type=ConfigType.ModbusConfig,
                               config_to_save=config)


def load_read_config() -> ReadConfig:
    return config_file_manager(action=ConfigOperation.LOAD,
                               config_type=ConfigType.ReadConfig,
                               config_class=ReadConfig)


def save_read_config(config: ReadConfig):
    return config_file_manager(action=ConfigOperation.SAVE,
                               config_type=ConfigType.ReadConfig,
                               config_to_save=config)


def load_write_config() -> WriteConfig:
    return config_file_manager(action=ConfigOperation.LOAD,
                               config_type=ConfigType.WriteConfig,
                               config_class=WriteConfig)


def save_write_config(config: WriteConfig):
    return config_file_manager(action=ConfigOperation.SAVE,
                               config_type=ConfigType.WriteConfig,
                               config_to_save=config)


def load_unit_sweep_config() -> UnitSweepConfig:
    return config_file_manager(action=ConfigOperation.LOAD,
                               config_type=ConfigType.UnitSweepConfig,
                               config_class=UnitSweepConfig)


def save_unit_sweep_config(config: UnitSweepConfig):
    return config_file_manager(action=ConfigOperation.SAVE,
                               config_type=ConfigType.UnitSweepConfig,
                               config_to_save=config)


def save_export_config(config: ExportConfig):
    return config_file_manager(action=ConfigOperation.SAVE,
                               config_type=ConfigType.ExportConfig,
                               config_to_save=config)


def load_export_config() -> ExportConfig:
    return config_file_manager(action=ConfigOperation.LOAD,
                               config_type=ConfigType.ExportConfig,
                               config_class=ExportConfig)
