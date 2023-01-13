import argparse

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional

from dataclasses_json import DataClassJsonMixin
from yaml import safe_load


@dataclass
class ProgramConfig(DataClassJsonMixin):
    command: str
    wrapper: Optional[str] = None


@dataclass
class Config(DataClassJsonMixin):
    programs: Dict[str, Dict[str, ProgramConfig]] = field(default_factory=dict)
    """domain -> name -> program"""


# -----------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("config", help="Path to YAML configuration file")
    args = parser.parse_args()

    with open(args.config, "r", encoding="utf-8") as config_file:
        config_dict = safe_load(config_file)

    config = Config.from_dict(config_dict)
    print(config)
