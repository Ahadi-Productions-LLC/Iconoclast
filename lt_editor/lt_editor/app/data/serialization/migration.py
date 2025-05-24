from typing import Dict
from app.data.serialization.migrators.migrator_base import MigratorBase
from app.utilities.typing import NestedPrimitiveDict

MIGRATORS: Dict[int, MigratorBase] = {
}

def migrate_db(data: NestedPrimitiveDict, version: int) -> NestedPrimitiveDict:
    if version not in MIGRATORS:
        raise NotImplementedError("Migration to next version from {} not implemented".format(version))
    return MIGRATORS[version].migrate_database(data)

def migrate_resources(resources: NestedPrimitiveDict, version: int) -> NestedPrimitiveDict:
    if version not in MIGRATORS:
        raise NotImplementedError("Migration to next version from {} not implemented".format(version))
    return MIGRATORS[version].migrate_resources(resources)