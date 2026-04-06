from pathlib import Path

import yaml

_VERSION_PATH = Path(__file__).resolve().parent.parent.parent / "VERSION.yaml"

with open(_VERSION_PATH, encoding="utf-8") as _f:
    VERSION_INFO: dict = yaml.safe_load(_f)

VERSION: int = VERSION_INFO["version"]
