from __future__ import annotations

from typing import List, Optional, Tuple

from app.constants import WINWIDTH, WINHEIGHT
from app.engine import engine
from app.engine.text_funcs import line_wrap
from app.engine.graphics.text.text_renderer import render_text

class DialogLogEntry:
    FONT_HEIGHT = 16
    CHIBI_SIZE = 32
    FONT = 'text'

    def __init__(self, name: str, chibi: Optional[engine.Surface], text: str):
        self.name = name
        self.chibi = chibi
        self.plain_text = text
        self.text_lines: List[str] = self.format_text(self.plain_text)

        self.size = (WINWIDTH, max(self.CHIBI_SIZE, self.FONT_HEIGHT + len(self.text_lines) * self.FONT_HEIGHT))

    @property
    def height(self) -> int:
        return self.size[1]

    def format_text(self, plain_text: str) -> List[str]:
        max_width = WINWIDTH - self.CHIBI_SIZE
        chunks = plain_text.split('{br}')  # Initial user defined splits
        text_lines = []
        for chunk in chunks:
            text_lines += line_wrap(self.FONT, chunk, max_width)
        return text_lines

    def draw(self, surf: engine.Surface, topleft: Tuple[int, int]) -> engine.Surface:
        x, y = topleft
        # Draw name
        if self.name:
            render_text(surf, [self.FONT], [self.name], ['yellow'], (x + self.CHIBI_SIZE, y))

        # Draw text
        for idx, line in enumerate(self.text_lines):
            render_text(surf, [self.FONT], [line], ['white'], (x + self.CHIBI_SIZE, y + self.FONT_HEIGHT + (idx * self.FONT_HEIGHT)))

        # Draw chibi
        if self.chibi:
            surf.blit(self.chibi, (x, y))

        return surf

class DialogLogUI:
    SCROLL_DISTANCE = 4
    BG_COLOR = (33, 33, 33, 192)

    def __init__(self):
        self.entries: List[DialogLogEntry] = []
        self.scroll: int = 0  # Measured in pixels from bottom of dialog tray -- positive numbers scroll UP!

    def __len__(self) -> int:
        return len(self.entries)

    def add_entry(self, speaker: str, chibi: Optional[engine.Surface], text: str):
        entry = DialogLogEntry(speaker, chibi, text)
        self.entries.append(entry)

    def pop_entry(self) -> DialogLogEntry:
        entry = self.entries.pop()
        return entry

    def scroll_up(self) -> int:
        """
        # Returns how much it scrolled by
        """
        old_scroll = self.scroll
        self.scroll += self.SCROLL_DISTANCE
        max_scroll = sum(entry.height for entry in self.entries) - WINHEIGHT  # WINHEIGHT to account for screen size
        max_scroll = max(0, max_scroll)
        self.scroll = min(max_scroll, self.scroll)
        return self.scroll - old_scroll

    def scroll_down(self) -> int:
        """
        # Returns how much it scrolled by
        """
        old_scroll = self.scroll
        self.scroll -= self.SCROLL_DISTANCE
        self.scroll = max(0, self.scroll)
        return old_scroll - self.scroll

    def scroll_to_bottom(self) -> int:
        """
        # Returns how much it scrolled by
        """
        old_scroll = self.scroll
        self.scroll = 0
        return old_scroll - self.scroll

    def draw(self, surf: engine.Surface) -> engine.Surface:
        # Draw fuzzy black background
        new_surf = engine.create_surface((WINWIDTH, WINHEIGHT), True)
        engine.fill(new_surf, self.BG_COLOR)
        surf.blit(new_surf, (0, 0))

        total_entry_height = sum(entry.height for entry in self.entries)

        # draw bottom up
        if total_entry_height < WINHEIGHT:
            screen_y_pos: int = total_entry_height  # scroll should always be zero here
        else:
            screen_y_pos: int = WINHEIGHT + self.scroll

        for entry in reversed(self.entries):
            screen_y_pos -= entry.height
            if screen_y_pos > WINHEIGHT or screen_y_pos < -entry.height:
                continue  # Not viewable, can just skip
            entry.draw(surf, (0, screen_y_pos))
        return surf
