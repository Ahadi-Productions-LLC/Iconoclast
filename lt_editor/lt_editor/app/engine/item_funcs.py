from __future__ import annotations
import logging
import math
from typing import TYPE_CHECKING, Dict, List, Set

from app.data.database.database import DB
from app.engine import item_system, skill_system, text_funcs
from app.engine.objects.item import ItemObject
from app.engine.objects.skill import SkillObject
from app.utilities import utils

from app.engine.game_state import game

if TYPE_CHECKING:
    from app.engine.objects.unit import UnitObject
    from app.utilities.typing import NID

def is_magic(unit: UnitObject, item: ItemObject, distance: int = 0) -> bool:
    """
    Determines if an item is a magic item.

    Args:
        unit (UnitObject): The unit attempting to use the item.
        item (ItemObject): The item to check.
        distance (int, optional): The distance at which the item is used. Defaults to 0.

    Distance matters if the item is a magic_at_range type item, since it will only be magical while used at a range > 1.

    Returns:
        bool: True if the item is a magic item, False otherwise.
    """
    if item.magic or (item.magic_at_range and distance > 1):
        return True
    return False

def is_ranged(unit: UnitObject, item: ItemObject) -> bool:
    """
    Determines if the item's max range is greater than 1.

    Args:
        unit (UnitObject): The unit attempting to use the item.
        item (ItemObject): The item to check.

    Returns:
        bool: True if the item is ranged, False otherwise.
    """
    if max(get_range(unit, item), default=0) > 1:
        return True
    return False

def is_heal(unit: UnitObject, item: ItemObject) -> bool:
    """
    Determines if an item is a healing item.

    Args:
        unit (UnitObject): The unit attempting to use the item.
        item (ItemObject): The item to check.

    Returns:
        bool: True if the item is a healing item, False otherwise.
    """
    if item.heal or item.magic_heal:
        return True
    return False

def available(unit: UnitObject, item: ItemObject) -> bool:
    """
    Checks if an item can be used by the unit.

    Args:
        unit (UnitObject): The unit attempting to use the item.
        item (ItemObject): The item to check.

    Returns:
        bool: True if the item can be used, False otherwise.
    """
    return item_system.available(unit, item) and skill_system.available(unit, item)

def has_magic(unit: UnitObject) -> bool:
    """
    Checks if the unit has any magic items.

    Args:
        unit (UnitObject): The unit to check.

    Returns:
        bool: True if the unit has any magic items, False otherwise.
    """
    return any(is_magic(unit, item) for item in unit.items if available(unit, item))

def can_use(unit: UnitObject, item: ItemObject) -> bool:
    """
    Checks if the unit can "use" a specific item, i.e., can the unit actually click Use in the item menu. 

    Args:
        unit (UnitObject): The unit attempting to use the item.
        item (ItemObject): The item to check.

    Returns:
        bool: True if the unit can "use" the item, False otherwise.
    """
    if item_system.can_use(unit, item) and available(unit, item):
        targets = game.target_system.get_valid_targets(unit, item)
        if targets:
            return True
    return False

def can_repair(unit: UnitObject, item: ItemObject) -> bool:
    """
    Checks if the item can be repaired

    Args:
        unit (UnitObject): The unit holding the item.
        item (ItemObject): The item to repair.

    Returns:
        bool: True if the item can be repaired, False otherwise.
    """
    if item.uses and item.data['uses'] < item.data['starting_uses'] and \
            not item_system.unrepairable(unit, item):
        return True
    return False

def has_repair(unit: UnitObject) -> bool:
    """
    Checks if the unit has any items that can be repaired.

    Args:
        unit (UnitObject): The unit to check.

    Returns:
        bool: True if the unit has items that can be repaired, False otherwise.
    """
    return any(can_repair(unit, item) for item in unit.items)

def buy_price(unit: UnitObject, item: ItemObject) -> int:
    """
    Calculates how much an item costs to buy from a shop for the unit.

    Args:
        unit (UnitObject): The unit attempting to buy the item.
        item (ItemObject): The item to buy.

    Returns:
        int: The buy price of the item.
    """
    value = item_system.buy_price(unit, item)
    if value:
        value *= skill_system.modify_buy_price(unit, item)
    else:
        return 0
    return int(value)

def sell_price(unit: UnitObject, item: ItemObject) -> int:
    """
    Calculates how much an item costs to sell to a shop for the unit.

    Args:
        unit (UnitObject): The unit attempting to sell the item.
        item (ItemObject): The item to sell.

    Returns:
        int: The sell price of the item.
    """
    value = item_system.sell_price(unit, item)
    if value:
        if unit:
            value *= skill_system.modify_sell_price(unit, item)
    else:
        return 0
    return int(value)

def repair_price(unit: UnitObject, item: ItemObject) -> int:
    """
    Calculates how much an item costs to repair for the unit.

    Args:
        unit (UnitObject): The unit holding the item.
        item (ItemObject): The item to repair.

    Returns:
        int: The repair price of the item.
    """
    repair_cost = 0
    if item.uses:
        charges_used = item.data['starting_uses'] - item.data['uses']
        cost_per_charge = buy_price(unit, item) / item.data['uses']
        repair_cost = math.ceil(charges_used * cost_per_charge)
    return int(repair_cost)

def create_item(unit, item_nid, droppable: bool = False, parent: ItemObject = None, 
                assign_ownership: bool = True) -> ItemObject:
    """Creates an item and all of it's subitems give the item's nid
    If assign_ownership is True, informs the item which unit and which parent_item
    owns it. Sometimes set to False so that you can use an action like 
    AddItemToMultiItem to set these properties instead."""
    item_prefab = DB.items.get(item_nid)
    if not item_prefab:
        logging.error("Couldn't find %s" % item_nid)
        return
    item = ItemObject.from_prefab(item_prefab)
    if unit and assign_ownership:
        item.owner_nid = unit.nid
    item_system.init(item)
    if parent:  # sub item specific operations
        for component in item.components:
            component.item = parent
        if assign_ownership:
            parent.subitem_uids.append(item.uid)
            parent.subitems.append(item)
            item.parent_item = parent
    else:  # main item specific operations
        item.droppable = droppable

    if item.multi_item:
        for subitem_nid in item.multi_item.value:
            create_item(unit, subitem_nid, parent=item)

    elif item.sequence_item:
        for subitem_nid in item.sequence_item.value:
            create_item(unit, subitem_nid, parent=item)

    return item

def create_items(unit, item_nid_list: list) -> list:
    items = []
    for val in item_nid_list:
        if isinstance(val, tuple) or isinstance(val, list):
            item_nid, droppable = val
        else:
            item_nid = val
            droppable = False
        item = create_item(unit, item_nid, droppable)
        if item:
            items.append(item)
        else:
            logging.error("Cannot find item with nid %s" % item_nid)
    return items

def get_all_items(unit: UnitObject) -> List[ItemObject]:
    """
    Retrieves all items possessed by a unit, including multi-items.

    Args:
        unit (UnitObject): The unit whose items to retrieve.

    Returns:
        List[ItemObject]: A list of all items possessed by the unit, including multi-items.
    """
    items = []
    for item in unit.items:
        if item.multi_item:
            subitems = get_all_items_from_multi_item(unit, item)
            items += subitems
        else:
            items.append(item)
    return items

def get_all_items_with_multiitems(item_list: List[ItemObject]) -> List[ItemObject]:
    """
    Retrieves all items and their subitems, including multi-items, from a list of items.

    Args:
        item_list (List[ItemObject]): The list of items to process.

    Returns:
        List[ItemObject]: A list of all items and their subitems, including multi-items.
    """
    items = []
    for item in item_list:
        if item.multi_item:
            subitems = get_all_items_with_multiitems(item.subitems)
            items += subitems
        items.append(item)
    return items

def get_all_items_and_abilities(unit: UnitObject) -> List[ItemObject]:
    """
    Retrieves all items and extra abilities possessed by a unit, including multi-items.

    Args:
        unit (UnitObject): The unit whose items and abilities to retrieve.

    Returns:
        List[ItemObject]: A list of all items and extra abilities possessed by the unit, including multi-items.
    """
    items = get_all_items(unit)
    extra_abilities: Dict[str, ItemObject] = skill_system.get_extra_abilities(unit)
    return items + [ability for name, ability in extra_abilities.items()]

def is_weapon_recursive(unit: UnitObject, item: ItemObject) -> bool:
    """
    Recursively checks if an item or any of its subitems is a weapon.

    Args:
        unit (UnitObject): The unit holding the item.
        item (ItemObject): The item to check.

    Returns:
        bool: True if the item or any of its subitems is a weapon, False otherwise.
    """
    if item_system.is_weapon(unit, item):
        return True
    if item.multi_item:
        if any([is_weapon_recursive(unit, sitem) for sitem in item.subitems]):
            return True
    return False

def is_spell_recursive(unit: UnitObject, item: ItemObject) -> bool:
    """
    Recursively checks if an item or any of its subitems is a spell.

    Args:
        unit (UnitObject): The unit holding the item.
        item (ItemObject): The item to check.

    Returns:
        bool: True if the item or any of its subitems is a spell, False otherwise.
    """
    if item_system.is_spell(unit, item):
        return True
    if item.multi_item:
        if any([is_spell_recursive(unit, sitem) for sitem in item.subitems]):
            return True
    return False

def get_all_items_from_multi_item(unit: UnitObject, item: ItemObject) -> List[ItemObject]:
    """
    Retrieves all items from a multi-item.

    Args:
        unit (UnitObject): The unit to which the multi-item belongs.
        item (ItemObject): The multi-item to process.

    Returns:
        List[ItemObject]: A list of all items contained within the multi-item.
    """
    all_items = []
    if item.multi_item:
        for subitem in item.subitems:
            if subitem.multi_item:
                all_subitems = get_all_items_from_multi_item(unit, subitem)
                all_items += all_subitems
            else:
                all_items.append(subitem)
    return all_items

def get_all_tradeable_items(unit: UnitObject) -> List[ItemObject]:
    """
    Retrieves all tradeable items possessed by a unit.

    Args:
        unit (UnitObject): The unit whose tradeable items to retrieve.

    Returns:
        List[ItemObject]: A list of all tradeable items possessed by the unit.
    """
    items = []
    for item in unit.items:
        if item_system.tradeable(unit, item):
            items.append(item)
    return items

def get_all_storeable_items(unit: UnitObject) -> List[ItemObject]:
    """
    Retrieves all storeable items possessed by a unit. Storeable items can be placed into the convoy

    Args:
        unit (UnitObject): The unit whose storeable items to retrieve.

    Returns:
        List[ItemObject]: A list of all storeable items possessed by the unit.
    """
    items = []
    for item in unit.items:
        if item_system.storeable(unit, item):
            items.append(item)
    return items

def get_num_items(unit: UnitObject) -> int:
    """
    Retrieves the maximum number of non-accessories a unit can carry.

    Args:
        unit (UnitObject): The unit to query.

    Returns:
        int: The maximum number of non-accessories the unit can carry.
    """
    return DB.constants.value('num_items') + skill_system.num_items_offset(unit)

def get_num_accessories(unit: UnitObject) -> int:
    """
    Retrieves the maximum number of accessories a unit can carry.

    Args:
        unit (UnitObject): The unit to query.

    Returns:
        int: The maximum number of accessories the unit can carry.
    """
    return DB.constants.value('num_accessories') + skill_system.num_accessories_offset(unit)

def too_much_in_inventory(unit: UnitObject) -> bool:
    """
    Checks if a unit is carrying too many items.

    Args:
        unit (UnitObject): The unit to check.

    Returns:
        bool: True if the unit is carrying too many items, False otherwise.
    """
    return len(unit.accessories) > get_num_accessories(unit) or \
        len(unit.nonaccessories) > get_num_items(unit)

def inventory_full(unit: UnitObject, item: ItemObject) -> bool:
    """
    Checks if a unit's inventory is full.

    Args:
        unit (UnitObject): The unit to check.
        item (ItemObject): The item to potentially add to the unit's inventory.

    Returns:
        bool: True if the unit's inventory is full, False otherwise.
    """
    if item_system.is_accessory(unit, item):
        return len(unit.accessories) >= get_num_accessories(unit)
    else:
        return len(unit.nonaccessories) >= get_num_items(unit)

def get_range(unit: UnitObject, item: ItemObject) -> Set[int]:
    """
    Retrieves the range of an item for a unit.

    Args:
        unit (UnitObject): The unit attempting to use the item.
        item (ItemObject): The item whose range to retrieve.

    Returns:
        Set[int]: A set containing the valid ranges of the item.
    """
    min_range = item_system.minimum_range(unit, item)
    max_range = item_system.maximum_range(unit, item)

    max_range = max(0, max_range)
    min_range = max(0, min_range)
    max_range += skill_system.modify_maximum_range(unit, item)
    min_range += skill_system.modify_minimum_range(unit, item)
    limit_max = skill_system.limit_maximum_range(unit, item)
    max_range = utils.clamp(max_range, 0, limit_max)

    return set(range(min_range, max_range + 1))

def get_range_string(unit: UnitObject, item: ItemObject):
    """
    Retrieves the range of an item as a string.

    Args:
        unit (UnitObject): The unit holding the item.
        item (ItemObject): The item whose range to retrieve.

    Returns:
        str: A string representation of the item's range.
    """
    if unit:
        item_range = get_range(unit, item)
        min_range = min(item_range, default=0)
        max_range = max(item_range, default=0)
    else:
        min_range = item_system.minimum_range(None, item)
        max_range = item_system.maximum_range(None, item)
    if max_range >= 99:
        rng = '%d+' % min_range
    elif max_range < 0:
        rng = text_funcs.translate('Varies')
    elif min_range != max_range:
        rng = '%d-%d' % (min_range, max_range)
    else:
        rng = '%d' % max_range
    return rng

def get_max_range(unit: UnitObject) -> int:
    """
    Retrieves the maximum range of all available items for a unit.

    Args:
        unit (UnitObject): The unit to query.

    Returns:
        int: The maximum range of all available items for the unit.
    """
    items = [item for item in get_all_items(unit) if available(unit, item)]
    return max([max(get_range(unit, item), default=0) for item in items], default=0)

def create_skill(unit: UnitObject, skill_nid: NID) -> SkillObject:
    skill_prefab = DB.skills.get(skill_nid)
    if not skill_prefab:
        logging.error("Couldn't find skill %s" % skill_nid)
        return None
    skill = SkillObject.from_prefab(skill_prefab)
    if unit:
        skill.owner_nid = unit.nid
    skill_system.init(skill)

    def create_subskill(subskill_nid):
        subskill_prefab = DB.skills.get(subskill_nid)
        if not subskill_prefab:
            logging.error("Couldn't find skill %s" % skill_nid)
            return None
        subskill = SkillObject.from_prefab(subskill_prefab)
        # Child skills are not owned by their parent skill unit
        # Since they are given to others
        # if unit:
        #     subskill.owner_nid = unit.nid
        skill_system.init(subskill)
        skill.subskill_uid = subskill.uid
        skill.subskill = subskill
        subskill.parent_skill = skill

    if skill.aura:
        child_skill_nid = skill.aura.value
        create_subskill(child_skill_nid)

    return skill

def create_skills(unit: UnitObject, skill_nid_list: List[NID]) -> List[SkillObject]:
    skills = []
    for skill_nid in skill_nid_list:
        skill = create_skill(unit, skill_nid)
        if skill:
            skills.append(skill)
    return skills

def num_stacks(unit: UnitObject, skill_nid: NID) -> int:
    """
    Calculates the number of stacks of a specific skill possessed by a unit.

    Args:
        unit (UnitObject): The unit whose skills to count.
        skill_nid (NID): The NID of the skill to count.

    Returns:
        int: The number of stacks of the specified skill possessed by the unit.
    """
    return len([skill for skill in unit.skills if skill.nid == skill_nid])

def can_be_used_in_base(unit: UnitObject, item: ItemObject) -> bool:
    """
    Checks if an item can be used by a unit in the base/prep.

    Args:
        unit (UnitObject): The unit attempting to use the item.
        item (ItemObject): The item to check.

    Returns:
        bool: True if the item can be used by the unit in the base, False otherwise.
    """
    return (item_system.can_use(unit, item) and
            available(unit, item) and
            item_system.can_use_in_base(unit, item) and
            item_system.simple_target_restrict(unit, item))
