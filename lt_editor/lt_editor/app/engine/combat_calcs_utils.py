from __future__ import annotations
from typing import TYPE_CHECKING, Callable, Optional
if TYPE_CHECKING:
    from app.engine.objects.item import ItemObject
    from app.engine.objects.unit import UnitObject

def resolve_offensive_formula(unit: UnitObject, item: Optional[ItemObject],
                    low_prio_item_formula: Callable[[UnitObject, ItemObject], Optional[str]],
                    low_prio_skill_formula: Callable[[UnitObject], Optional[str]],
                    high_prio_item_formula: Callable[[UnitObject, ItemObject], Optional[str]],
                    high_prio_skill_formula: Callable[[UnitObject], Optional[str]],
                    default_formula: Callable[[UnitObject], str]) -> str:
    """
    Resolve the formula for a unit.

    Args:
        unit (UnitObject): The unit in question.
        item (ItemObject): The item equipped by the unit. May be None.
        low_prio_item_formula (Callable[[UnitObject, ItemObject], Optional[str]]): The low prio item callback for the formula.
        low_prio_skill_formula (Callable[[UnitObject], Optional[str]]): The low prio skill callback for the formula.
        high_prio_item_formula (Callable[[UnitObject, ItemObject], Optional[str]]): The high prio item callback for the formula.
        high_prio_skill_formula (Callable[[UnitObject], Optional[str]]): The high prio skill callback for the formula.
        default_formula (Callable[[UnitObject], str]): The default formula to use."""
    if item:
        return high_prio_skill_formula(unit) or high_prio_item_formula(unit, item) \
            or low_prio_skill_formula(unit) or low_prio_item_formula(unit, item) \
            or default_formula(unit)
    else:
        return high_prio_skill_formula(unit) or low_prio_skill_formula(unit) or default_formula(unit)

def resolve_defensive_formula(def_unit: UnitObject, def_item: Optional[ItemObject],
                              atk_unit: UnitObject, atk_item: Optional[ItemObject],
                              low_prio_item_formula: Callable[[UnitObject, ItemObject], Optional[str]],
                              low_prio_skill_formula: Callable[[UnitObject], Optional[str]],
                              high_prio_item_formula: Callable[[UnitObject, ItemObject], Optional[str]],
                              high_prio_skill_formula: Callable[[UnitObject], Optional[str]],
                              default_formula: Callable[[UnitObject], str]) -> str:
    """
    Resolve the formula for a defensive unit.

    Args:
        def_unit (UnitObject): The defending unit.
        def_item (Optional[ItemObject]): The item equipped by the defending unit. Is not used currently.
        atk_unit (UnitObject): The attacking unit.
        atk_item (ItemObject): The item equipped by the attacking unit. May be None.
        low_prio_item_formula (Callable[[UnitObject, ItemObject], Optional[str]]): The low prio item callback for the formula.
        low_prio_skill_formula (Callable[[UnitObject], Optional[str]]): The low prio skill callback for the formula.
        high_prio_item_formula (Callable[[UnitObject, ItemObject], Optional[str]]): The high prio item callback for the formula.
        high_prio_skill_formula (Callable[[UnitObject], Optional[str]]): The high prio skill callback for the formula.
        default_formula (Callable[[UnitObject], str]): The default formula to use."""
    if atk_item:
        return high_prio_skill_formula(def_unit) or high_prio_item_formula(atk_unit, atk_item) \
            or low_prio_skill_formula(def_unit) or low_prio_item_formula(atk_unit, atk_item) \
            or default_formula(def_unit)
    else:
        return high_prio_skill_formula(def_unit) or low_prio_skill_formula(def_unit) or default_formula(def_unit)