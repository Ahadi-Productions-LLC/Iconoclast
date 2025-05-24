from dataclasses import dataclass

from app.utilities.data import Prefab

@dataclass
class AIGroup(Prefab):
    nid: str = ""
    trigger_threshold: int = 0