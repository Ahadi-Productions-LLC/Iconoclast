from dataclasses import dataclass, asdict

from app.data.serialization.dataclass_serialization import dataclass_from_dict

@dataclass
class Metadata():
    date: str = ""
    engine_version: str = ""
    serialization_version: int = 0
    project: str = ""
    has_fatal_errors: bool = False
    as_chunks: bool = False

    def save(self):
        return asdict(self)

    def restore(self, d):
        if not d:
            return
        restored = dataclass_from_dict(self.__class__, d)
        self.__dict__ = restored.__dict__