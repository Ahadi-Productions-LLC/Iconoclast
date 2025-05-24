from __future__ import annotations

import random
from typing import Optional

from app.engine.sprites import SPRITES
from app.engine import engine

import logging

# For bg surfs that don't have `_bg` in their name
HARDCODED_BG_SURFS = [
    'name_tag'
]

SLICE_9_WIDTH = 8
SLICE_9_HEIGHT = 8

def create_base_surf(width: int, height: int, base: Optional[str] = 'menu_bg_base') -> engine.Surface:
    """
    Given the width and height of a desired surface along with a base surface (usually 24x24),
    uses slice 9 pattern to create a surface of the desired size.

    If the base surface is larger than 24x24, each of it's additional slice 9 sprites are randomized
    during the drawing of the desired surface
    """

    sprite = SPRITES.get(base, 'menu_bg_base')
    if base and '_bg' not in base and base not in HARDCODED_BG_SURFS:
        new_base_surf = engine.create_surface((width, height), transparent=True)
        new_base_surf.blit(sprite, (0, 0))
        return new_base_surf

    base_width = sprite.get_width()
    base_height = sprite.get_height()

    assert (base_width % SLICE_9_WIDTH) == 0
    assert (base_height % SLICE_9_HEIGHT) == 0

    desired_width = width - (width % SLICE_9_WIDTH)
    desired_height = height - (height % SLICE_9_HEIGHT)
    surf = engine.create_surface((desired_width, desired_height), transparent=True)

    # Gather up the pieces of the base surface
    # Corners
    topleft = engine.subsurface(sprite, (0, 0, SLICE_9_WIDTH, SLICE_9_HEIGHT))
    topright = engine.subsurface(sprite, (base_width - SLICE_9_WIDTH, 0, SLICE_9_WIDTH, SLICE_9_HEIGHT))
    botleft = engine.subsurface(sprite, (0, base_height - SLICE_9_HEIGHT, SLICE_9_WIDTH, SLICE_9_HEIGHT))
    botright = engine.subsurface(sprite, (base_width - SLICE_9_WIDTH, base_height - SLICE_9_HEIGHT, SLICE_9_WIDTH, SLICE_9_HEIGHT))

    top, left, right, bot, center = [], [], [], [], []
    # Sides
    for x in range(SLICE_9_WIDTH, base_width - SLICE_9_WIDTH, SLICE_9_WIDTH):
        top.append(engine.subsurface(sprite, (x, 0, SLICE_9_WIDTH, SLICE_9_HEIGHT)))
        bot.append(engine.subsurface(sprite, (x, base_height - SLICE_9_HEIGHT, SLICE_9_WIDTH, SLICE_9_HEIGHT)))
    for y in range(SLICE_9_HEIGHT, base_height - SLICE_9_HEIGHT, SLICE_9_HEIGHT):
        left.append(engine.subsurface(sprite, (0, y, SLICE_9_WIDTH, SLICE_9_HEIGHT)))
        right.append(engine.subsurface(sprite, (base_width - SLICE_9_WIDTH, y, SLICE_9_WIDTH, SLICE_9_HEIGHT)))

    # Center
    for x in range(SLICE_9_WIDTH, base_width - SLICE_9_WIDTH, SLICE_9_WIDTH):
        for y in range(SLICE_9_HEIGHT, base_height - SLICE_9_HEIGHT, SLICE_9_HEIGHT):
            center.append(engine.subsurface(sprite, (x, y, SLICE_9_WIDTH, SLICE_9_HEIGHT)))

    # Now draw on the desired sprite
    for x in range(SLICE_9_WIDTH, desired_width - SLICE_9_WIDTH, SLICE_9_WIDTH):
        for y in range(SLICE_9_HEIGHT, desired_height - SLICE_9_HEIGHT, SLICE_9_HEIGHT):
            surf.blit(random.choice(center), (x, y))

    # Edges
    for x in range(SLICE_9_WIDTH, desired_width - SLICE_9_WIDTH, SLICE_9_WIDTH):
        surf.blit(random.choice(top), (x, 0))
        surf.blit(random.choice(bot), (x, desired_height - SLICE_9_HEIGHT))

    for y in range(SLICE_9_HEIGHT, desired_height - SLICE_9_HEIGHT, SLICE_9_HEIGHT):
        surf.blit(random.choice(left), (0, y))
        surf.blit(random.choice(right), (desired_width - SLICE_9_WIDTH, y))

    # Corners
    surf.blit(topleft, (0, 0))
    surf.blit(topright, (desired_width - SLICE_9_WIDTH, 0))
    surf.blit(botleft, (0, desired_height - SLICE_9_HEIGHT))
    surf.blit(botright, (desired_width - SLICE_9_WIDTH, desired_height - SLICE_9_HEIGHT))

    return surf

def create_highlight_surf(width) -> engine.Surface:
    if width < 5:
        raise ValueError("Highlight surf too short - why are you even calling this?")
    sprite: engine.Surface = SPRITES.get('equipment_highlight')

    base_width = sprite.get_width()
    base_height = sprite.get_height()

    left_endcap = engine.subsurface(sprite, (0, 0, 2, base_height))
    middle_segment = engine.subsurface(sprite, (3, 0, 1, base_height))
    right_endcap = engine.subsurface(sprite, (base_width - 2, 0, 2, base_height))

    surf = engine.create_surface((width, base_height), transparent=True)
    surf.blit(left_endcap, (0, 0))
    for middle_x in range(2, width - 2):
        surf.blit(middle_segment, (middle_x, 0))
    surf.blit(right_endcap, (width - 2, 0))

    return surf
