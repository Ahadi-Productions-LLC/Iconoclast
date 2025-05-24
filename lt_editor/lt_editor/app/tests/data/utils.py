import json
from pathlib import Path
from typing import Type

from app.utilities.data import Data


def load_catalog_with_path(catalog_t: Type[Data], path: Path) -> Data:
    catalog = catalog_t()
    data = json.loads(path.read_text())
    catalog.restore(data)
    return catalog