from app.data.database.database import DB
from app.engine.objects.difficulty_mode import DifficultyModeObject
from app.utilities.data import Data

from app.engine.objects.unit import UnitObject
from app.engine.objects.region import RegionObject
from app.engine.objects.ai_group import AIGroupObject
from app.engine.objects.tilemap import TileMapObject

from app.data.database.level_units import UnitGroup
from app.utilities.typing import NID

class LevelObject():
    """Representation of a Level or Chapter in the engine. Contains information
    about the tilemap of the level, which is the chapter's main party, what music
    should exist for each phase, etc.

    Attributes:
        nid (NID): The unique ID for the level
        name (str): The name of the level (displayed in the Chapter Title card)
        tilemap (TileMapObject): The current tilemap for the level
        bg_tilemap (TileMapObject): The current background tilemap for the level
        party (NID): The chapter's main party
        music (dict): Keys are the phase, value is the song name
        objective (dict): The objective text
        units: (Data[UnitObject]): Database of the units in the level
        regions: (Data[RegionObject]): Database of regions in the level
        ai_groups (Data[AIGroupObject]): Database of AI Groups in the level
    """
    def __init__(self):
        self.nid: NID = None
        self.name: str = None
        self.tilemap: TileMapObject = None
        self.bg_tilemap: TileMapObject = None
        self.party: NID = None

        self.music = {}
        self.objective = {}

        self.units: Data[UnitObject] = Data()
        self.regions: Data[RegionObject] = Data()
        self.unit_groups = Data()
        self.ai_groups: Data[AIGroupObject] = Data()

    @classmethod
    def from_prefab(cls, prefab, tilemap, bg_tilemap, unit_registry, current_mode: DifficultyModeObject):
        level = cls()
        level.nid = prefab.nid
        level.name = prefab.name
        level.tilemap = tilemap
        level.bg_tilemap = bg_tilemap
        level.party = prefab.party

        level.music = {k: v for k, v in prefab.music.items()}
        level.objective = {k: v for k, v in prefab.objective.items()}

        # Load in units
        level.units = Data()
        for unit_prefab in prefab.units:
            if unit_prefab.nid in unit_registry:
                unit = unit_registry[unit_prefab.nid]
                unit.starting_position = tuple(unit_prefab.starting_position) if unit_prefab.starting_position else None
                if not unit.dead:
                    unit.position = unit.starting_position
                else:
                    unit.position = None
                level.units.append(unit)
            else:
                new_unit = UnitObject.from_prefab(unit_prefab, current_mode)
                level.units.append(new_unit)

        level.regions = Data([RegionObject.from_prefab(p) for p in prefab.regions])
        level.unit_groups = Data([UnitGroup.from_prefab(p) for p in prefab.unit_groups])
        level.ai_groups = Data([AIGroupObject.from_prefab(p) for p in prefab.ai_groups])

        return level

    # If the attribute is not found
    def __getattr__(self, attr):
        if attr.startswith('__') and attr.endswith('__'):
            return super().__getattr__(attr)
        elif self.nid:
            prefab = DB.levels.get(self.nid)
            if prefab and hasattr(prefab, attr):
                return getattr(prefab, attr)
        # not in prefab, so...
        raise AttributeError('LevelObject has no attribute %s' % attr)

    @classmethod
    def from_scratch(cls, nid, tilemap, bg_tilemap, party, unit_registry, current_mode: DifficultyModeObject):
        level = cls()
        level.nid = nid
        level.name = nid
        level.tilemap = tilemap
        level.bg_tilemap = bg_tilemap
        level.party = party

        level.music = {}
        level.objective = {
            'simple': "",
            'win': "",
            'loss': ""}

        level.units: Data[UnitObject] = Data()
        level.regions: Data[RegionObject] = Data()
        level.unit_groups = Data()
        level.ai_groups: Data[AIGroupObject] = Data()

        return level

    def save(self):
        s_dict = {'nid': self.nid,
                  'name': self.name,
                  'tilemap': self.tilemap.save(),
                  'bg_tilemap': self.bg_tilemap.save() if self.bg_tilemap else None,
                  'party': self.party,
                  'music': self.music,
                  'objective': self.objective,
                  'units': [unit.nid for unit in self.units],
                  'regions': [region.nid for region in self.regions],
                  'unit_groups': [unit_group.save() for unit_group in self.unit_groups],
                  'ai_groups': [ai_group.save() for ai_group in self.ai_groups],
                  }
        return s_dict

    @classmethod
    def restore(cls, s_dict: dict, game):
        level = cls()
        level.nid = s_dict['nid']
        level.name = s_dict.get('name', "")
        level.tilemap = TileMapObject.restore(s_dict['tilemap'])
        level.bg_tilemap = TileMapObject.restore(s_dict['bg_tilemap']) if s_dict.get('bg_tilemap', None) else None
        level.party = s_dict.get('party', "")

        level.music = s_dict.get('music', {})
        level.objective = s_dict.get('objective', {})

        level.units = Data([game.get_unit(unit_nid) for unit_nid in s_dict.get('units', [])])
        level.regions = Data([game.get_region(region_nid) for region_nid in s_dict.get('regions', [])])
        level.unit_groups = Data([UnitGroup.restore(unit_group) for unit_group in s_dict.get('unit_groups', [])])
        level.ai_groups = Data([AIGroupObject.restore(ai_group) for ai_group in s_dict.get('ai_groups', [])])

        return level
