from __future__ import annotations
from typing import TYPE_CHECKING

from app.data.database.components import ComponentType
from app.data.database.skill_components import SkillComponent, SkillTags
from app.engine import action, equations, item_funcs, skill_system
from app.engine.game_state import game
import app.engine.combat.playback as pb
from app.utilities import static_random

if TYPE_CHECKING:
    from app.engine.objects.item import ItemObject

class ModifyAIPriority(SkillComponent):
    nid = 'modify_ai_priority'
    desc = 'Unit will have its priority multiplied by value. 0 is no attack; 1 is neutral; higher numbers will guarantee attacks.'
    tag = SkillTags.ADVANCED

    expose = ComponentType.Float

    value = 0.0

    def ai_priority_multiplier(self, unit):
        return self.value
