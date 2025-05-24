from pathlib import Path
from typing import Protocol

from app.utilities.typing import NestedPrimitiveDict


class LoaderBase(Protocol):
    def load_database(self, data_dir: Path) -> NestedPrimitiveDict:
        ...

    def load_resources(self, resource_dir: Path) -> NestedPrimitiveDict:
        ...