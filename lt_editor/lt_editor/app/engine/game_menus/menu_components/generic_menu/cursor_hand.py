from enum import Enum
from app.engine import engine
from app.sprites import SPRITES

class CursorDrawMode(Enum):
    NO_DRAW = 0
    DRAW = 1
    DRAW_STATIC = 2

class CursorHand():
    def __init__(self) -> None:
        self.cursor_sprite = SPRITES.get('menu_hand')
        self.offsets = [0, 0, 0, 0, 0, 0, 0, 1, 1, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 4, 4, 4, 3, 3, 2, 2, 2, 1, 1, 1, 1]
        self.offset_index = 0
        self.y_offset = 0
        self.mode: CursorDrawMode = CursorDrawMode.DRAW

    def y_offset_up(self):
        self.y_offset = 12

    def y_offset_down(self):
        self.y_offset = -12

    def get_offset(self):
        return self.offsets[self.offset_index]

    def update(self):
        self.offset_index = (self.offset_index + 1) % len(self.offsets)

    def update_y_offset(self):
        if self.y_offset > 0:
            self.y_offset = max(0, self.y_offset - 4)
        elif self.y_offset < 0:
            self.y_offset = min(0, self.y_offset + 4)

    def draw(self, surf, topleft) -> engine.Surface:
        x, y = topleft
        if self.mode == CursorDrawMode.DRAW:
            engine.blit(surf, self.cursor_sprite, (x + self.get_offset(), y + self.y_offset))
        elif self.mode == CursorDrawMode.DRAW_STATIC:
            engine.blit(surf, self.cursor_sprite, (x, y + self.y_offset))
        else:
            pass  # Don't draw
        self.update_y_offset()
        return surf
