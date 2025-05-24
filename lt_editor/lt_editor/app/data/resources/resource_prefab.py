from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

class WithResources(ABC):
    @abstractmethod
    def set_full_path(self, path: str) -> None:
        ...

    @abstractmethod
    def used_resources(self) -> List[Optional[Path]]:
        ...