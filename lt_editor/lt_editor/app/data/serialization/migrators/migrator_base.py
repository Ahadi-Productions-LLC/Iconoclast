from typing import Protocol

from app.utilities.typing import NestedPrimitiveDict


class MigratorBase(Protocol):
    def migrate_database(self, db_dict: NestedPrimitiveDict) -> NestedPrimitiveDict:
        ...

    def migrate_resources(self, resource_dict: NestedPrimitiveDict) -> NestedPrimitiveDict:
        ...