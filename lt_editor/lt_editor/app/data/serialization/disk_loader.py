from typing import Dict
from app.data.serialization.loaders.loader_base import LoaderBase
from app.data.serialization.migration import migrate_db, migrate_resources
from app.data.serialization.versions import CURRENT_SERIALIZATION_VERSION
from app.utilities.typing import NestedPrimitiveDict
from app.data.serialization.loaders import loader0

LOADERS: Dict[int, LoaderBase] = {
    0: loader0.Loader0(),
}

def _dispatch_load_resources(data_dir: str, version: int) -> NestedPrimitiveDict:
    if version < 0:
        raise ValueError("Unsupported serialization version {}".format(version))
    while version not in LOADERS:
        version -= 1
    return LOADERS[version].load_resources(data_dir)

def _dispatch_load_database(data_dir: str, version: int) -> NestedPrimitiveDict:
    if version < 0:
        raise ValueError("Unsupported serialization version {}".format(version))
    while version not in LOADERS:
        version -= 1
    return LOADERS[version].load_database(data_dir)

def load_database(data_dir: str, version: int) -> NestedPrimitiveDict:
    current_version = CURRENT_SERIALIZATION_VERSION
    loaded = _dispatch_load_database(data_dir, version)
    while version < current_version:
        loaded = migrate_db(loaded, version)
        version += 1
    return loaded

def load_resources(data_dir: str, version: int) -> NestedPrimitiveDict:
    current_version = CURRENT_SERIALIZATION_VERSION
    loaded = _dispatch_load_resources(data_dir, version)
    while version < current_version:
        loaded = migrate_resources(loaded, version)
        version += 1
    return loaded