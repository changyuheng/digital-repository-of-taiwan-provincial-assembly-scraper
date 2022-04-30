import dataclasses
import os.path
import pathlib
from typing import Any, BinaryIO, Optional

import dacite
import tomli
import tomli_w

from .log import get_logger


CONFIG_VERSION: int = 2
CONFIG_FILENAME: str = 'config.toml'
CONFIG_PATH: pathlib.Path = pathlib.Path(CONFIG_FILENAME)


@dataclasses.dataclass
class Config:
    data_version: int = CONFIG_VERSION
    account: str = ""
    password: str = ""
    browser: str = "edge"


def get_config() -> Config:
    global _config

    if not _config:
        if os.path.isfile(CONFIG_PATH):
            f: BinaryIO
            with open(CONFIG_PATH, 'rb') as f:
                config_dict: dict[str, Any] = tomli.load(f)
            _config = dacite.from_dict(data_class=Config, data=config_dict)

    if not _config:
        _config = Config()
        set_config()

    return _config


def print_config(file: BinaryIO = None) -> None:
    config: Config = get_config()
    if file is None:
        print(tomli_w.dumps(dataclasses.asdict(config)), end="")
    else:
        tomli_w.dump(dataclasses.asdict(config), file)


def set_config() -> None:
    f: BinaryIO
    with open(CONFIG_PATH, 'wb') as f:
        tomli_w.dump(dataclasses.asdict(_config), f)


_config: Optional[Config] = None
