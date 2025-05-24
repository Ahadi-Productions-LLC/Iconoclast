from dataclasses import dataclass

from app.utilities.data import Data, Prefab
from app.utilities import str_utils
from app.utilities.typing import NID

@dataclass
class Faction(Prefab):
    """A faction within the game. 

    Attributes:
        nid (NID): The unique identifier for the faction.
        name (str): The name of the faction.
        desc (str): The description of the faction. Defaults to an empty string.
        icon_nid (NID): The unique identifier of the faction's icon (a 32x32 Icon).
        icon_index (tuple): The index of the faction's icon within an icon spritesheet (x, y). Defaults to (0, 0).
    """
    nid: NID = None
    name: str = None
    desc: str = ""

    icon_nid: NID = None
    icon_index: tuple = (0, 0)

class FactionCatalog(Data[Faction]):
    """A catalog of the factions in your project.

    Access a specific faction with `DB.factions.get('Bandit')` where Bandit is the faction NID.
    """
    datatype = Faction

    def create_new(self, db):
        nids = [d.nid for d in self]
        nid = name = str_utils.get_next_name("New Faction", nids)
        new_faction = Faction(nid, name)
        self.append(new_faction)
        return new_faction
