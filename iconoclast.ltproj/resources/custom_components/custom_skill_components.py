from __future__ import annotations

import random

from app.data.database.components import ComponentType
from app.data.database.database import DB
from app.data.database.skill_components import SkillComponent, SkillTags
from app.engine import (action, banner, combat_calcs, engine, equations,
                        image_mods, item_funcs, item_system, skill_system)
from app.engine.game_state import game                        
from app.engine.objects.unit import UnitObject
from app.utilities import utils, static_random
import app.engine.combat.playback as pb

class SlowHeal(SkillComponent):
    nid = 'SlowHeal'
    desc = "Unit restores 1 HP at beginning of turn"
    tag = SkillTags.STATUS

    expose = ComponentType.Float
    value = 1
    
    
    def _get_heal_amount(self, unit):
        empower_heal = skill_system.empower_heal(unit, self)
        empower_heal_received = skill_system.empower_heal_received(self, unit)
        return self.value + empower_heal + empower_heal_received

    def on_upkeep(self, actions, playback, unit):
        max_hp = equations.parser.hitpoints(unit)
        if unit.get_hp() < max_hp:
            hp_change = int(self.value)
            actions.append(action.ChangeHP(unit, hp_change))
            # Playback
            playback.append(pb.HitSound('MapHeal'))
            playback.append(pb.DamageNumbers(unit, -hp_change))
            if hp_change >= 30:
                name = 'MapBigHealTrans'
            elif hp_change >= 15:
                name = 'MapMediumHealTrans'
            else:
                name = 'MapSmallHealTrans'
            playback.append(pb.CastAnim(name))



class DoNothing(SkillComponent):
    nid = 'do_nothing'
    desc = 'does nothing'
    tag = SkillTags.CUSTOM

    expose = ComponentType.Int
    value = 1
