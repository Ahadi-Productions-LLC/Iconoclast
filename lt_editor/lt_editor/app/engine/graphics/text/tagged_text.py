from __future__ import annotations
from typing import List, Dict, Tuple, Optional, Iterator

import math

from app.constants import FRAMERATE
from app.engine import engine
from app.engine.fonts import FONT
from app.engine.graphics.text.text_effects import (
    TextSettings,
    TextEffect,
    RECOMMENDED_CYCLE_PERIOD,
    MAX_RECOMMENDED_CYCLE_PERIOD,
)
from app.utilities.enums import HAlignment
from app.utilities.typing import NID


class TaggedTextChunk:

    def __init__(self, text: str, font: NID, effects: List[TextEffect]):
        self.text = text
        self.font = font
        self.effects = effects

    def __len__(self):
        return len(self.text)

    def __getitem__(self, item) -> Optional[TaggedTextChunk]:
        substr = self.text[item]
        if substr:
            return TaggedTextChunk(substr, self.font, self.effects)
        else:
            return None

    def __repr__(self):
        return f"({self.text}, {self.font}, {self.effects})"

    def width(self) -> int:
        """return the pixel width of this text chunk when rendered

        Returns:
            int: pixel width
        """
        return FONT[self.font].width(self.text) if self.font != "icon" else 16

    def draw(self, surf: engine.Surface, topleft: Tuple[int, int]) -> int:
        """draw this TaggedTextChunk onto surf at topleft

        Args:
            surf (engine.Surface): surface to draw on
            topleft (Tuple[int, int]): top left location to begin drawing

        Returns:
            int: pixel width of the drawn TaggedTextChunk
        """
        if self.font == "icon":
            # not sure why but this import needs to go here to avoid a circular dependency
            from app.engine.icons import draw_icon_by_alias

            settings = TextSettings("", (0, 0))
            settings.apply(self.effects)
            draw_icon_by_alias(
                surf, self.text.strip(),
                (topleft[0] + settings.offset[0], topleft[1] + settings.offset[1]))
            return self.width()

        settings = TextSettings("", (0, 0))
        settings.apply(self.effects)
        FONT[self.font].blit(
            self.text, surf,
            (topleft[0] + settings.offset[0], topleft[1] + settings.offset[1]),
            settings.color)
        return self.width()


class TaggedText:
    global_caching = True

    def __init__(self):
        self.chunks: List[TaggedTextChunk] = []
        self._size: int = 0  # this is the total length of the individual chunks
        self._caching: bool = False
        self._cache: Dict[int, engine.Surface] = {}
        self._effect_cycle_period_lcm: int = 1
        self._max_offset: Tuple[int, int, int, int] = (0, 0, 0, 0)

    @property
    def caching_enabled(self):
        return self._caching

    def __len__(self) -> int:
        return self._size

    def __iter__(self) -> Iterator[TaggedTextChunk]:
        for chunk in self.chunks:
            yield chunk

    def __getitem__(self, item) -> TaggedText:
        if isinstance(item, slice):
            if item.step is not None:
                raise ValueError(
                    f"no support for indexing with a custom step {item.step}")
            return self._get_slice(item.start, item.stop)
        else:
            if not isinstance(item, int):
                raise KeyError(f"only supports integer or slice keys not {type(item)}")
            if item >= self._size:
                raise IndexError
            return self._get_slice(item, item + 1)

    def __repr__(self):
        return "".join(repr(chunk) for chunk in self.chunks)

    def _get_slice(self, start: Optional[int], stop: Optional[int]) -> TaggedText:
        if start is None:
            start = 0
        if stop is None:
            stop = max(start, len(self))

        if start < 0 or stop < 0:
            raise IndexError(f"no support for negative indexes {start}:{stop}")

        tagged_text = TaggedText()
        if start >= stop:
            return tagged_text

        if start == 0 and stop >= self._size:
            return self

        chunk_idx = 0
        while stop > 0:
            # handle past-the-end slicing
            if chunk_idx == len(self.chunks):
                break
            curr_chunk = self.chunks[chunk_idx]
            subchunk = curr_chunk[start:stop]
            if subchunk:
                tagged_text.append_chunk(subchunk)
            start = max(start - len(curr_chunk), 0)
            stop -= len(curr_chunk)
            chunk_idx += 1

        return tagged_text

    def append(self, text: str, font: NID, effects: List[TextEffect]):
        """add a chunk as parameters to TaggedTextChunk

        Args:
            text (str): raw text
            font (NID): associated font
            effects (List[TextEffect]): associated effects
        """
        self.append_chunk(TaggedTextChunk(text, font, effects))

    def append_chunk(self, chunk: TaggedTextChunk):
        """add a chunk as TaggedTextChunk

        Args:
            chunk (TaggedTextChunk): chunk to add
        """
        self._size += len(chunk)
        self.chunks.append(chunk)
        # find the lcm between current and cycles of all new effects
        self._effect_cycle_period_lcm = math.lcm(
            self._effect_cycle_period_lcm, *[e.cycle_period for e in chunk.effects])
        # find the element-wise max offset between current and max offsets of all new effects
        self._max_offset = tuple(
            max(*x)
            for x in zip(self._max_offset, *[e.max_offset() for e in chunk.effects]))

    def width(self) -> int:
        """return the pixel width

        Returns:
            int: pixel width
        """
        return sum([t.width() for t in self.chunks])

    def update_effects(self):
        """update the internal state of all text effects, should be called once per frame
        WARNING: this function relies on __eq__ not being implemented for TaggedTextChunk
        """
        effects_updated = set()
        for chunk in self.chunks:
            for effect in chunk.effects:
                if effect not in effects_updated:
                    effect.update()
                    effects_updated.add(effect)

    def get_cycle_period(self) -> int:
        return self._effect_cycle_period_lcm

    def set_caching_if_recommended(self) -> bool:
        """Enable or disable caching depending if it is recommended.
        Recommended threshold corresponds to an effect cycle period of <= 4s at 60FPS.
        Anything above this threshold is not recommended to turn on caching.

        Returns:
            bool: Whether caching was enabled or disabled.
        """
        caching = False
        if self.get_cycle_period() <= RECOMMENDED_CYCLE_PERIOD:
            caching = True
        self._caching = caching
        return caching

    def set_caching_if_under_max_threshold(self) -> bool:
        """Enable or disable caching depending if it is under the maximum threshold for caching.
        Maximum threshold corresponds to an effect cycle period of <= 10s at 60FPS.
        Anything above this threshold is strongly not recommended to turn on caching.

        Returns:
            bool: Whether caching was enabled or disabled.
        """
        caching = False
        if self.get_cycle_period() <= MAX_RECOMMENDED_CYCLE_PERIOD:
            caching = True
        self._caching = caching
        return caching

    def force_enable_caching(self):
        """Forces caching even if it is strongly not recommended.
        Beware of excessive memory use depending on how long the effect cycle period
        is and how long you leave the text on screen for.
        """
        self._caching = True

    def _get_cached_text_surf(self, cache_index, test_surf=None):
        if cache_index not in self._cache:
            offset_up, offset_right, offset_down, offset_left = self._max_offset
            padding_x = offset_left + offset_right
            padding_y = offset_up + offset_down
            # setup a new text surf
            if test_surf:
                text_surf = test_surf
            else:
                text_surf = engine.create_surface(
                    (self.width() + padding_x + 1, 16 + padding_y), transparent=True)
            text_surf_tx, text_surf_ty = offset_left, offset_up
            for chunk in self.chunks:
                text_surf_tx += chunk.draw(text_surf, (text_surf_tx, text_surf_ty))
            self._cache[cache_index] = text_surf
        else:
            # grab existing text surf
            text_surf = self._cache[cache_index]
        return text_surf

    def _draw(self,
              surf: engine.Surface,
              topleft: Tuple[int, int],
              align: HAlignment = HAlignment.LEFT,
              cache_counter: int = 0,
              test_surf: Optional[engine.Surface] = None) -> engine.Surface:

        # for non-left alignments
        if align == HAlignment.CENTER or align == HAlignment.RIGHT:
            width = self.width()
            tx, ty = topleft
            if align == HAlignment.CENTER:
                tx -= width // 2
            elif align == HAlignment.RIGHT:
                tx -= width
        else:
            tx, ty = topleft

        if self._caching and self.global_caching:
            cache_index = cache_counter % self.get_cycle_period()
            text_surf = self._get_cached_text_surf(cache_index, test_surf=test_surf)
            text_surf_ty, _, _, text_surf_tx = self._max_offset
            surf.blit(text_surf, (tx - text_surf_tx, ty - text_surf_ty))
        else:
            # blit normally
            for chunk in self.chunks:
                tx += chunk.draw(surf, (tx, ty))

        return surf

    def draw(self,
             surf: engine.Surface,
             topleft: Tuple[int, int],
             align: HAlignment = HAlignment.LEFT) -> engine.Surface:
        """Render this tagged text onto surf. Creates and uses a cached surface if caching is enabled.

        Args:
            surf (engine.Surface): Surface to draw on.
            topleft (Tuple[int, int]): Where to start drawing on surf.
            align (HAlignment, optional): Text alignment. Defaults to HAlignment.LEFT.
            cache_index (int, optional): Which cached surface to use when caching is enabled. Defaults to 0.
            test_surf: (Optional[engine.Surface], optional): For testing only. Defaults to None.

        Returns:
            engine.Surface: Surface with styled text drawn on it.
        """
        return self._draw(surf, topleft, align, engine.get_time() // FRAMERATE)

    def test_draw(self,
                  surf: engine.Surface,
                  topleft: Tuple[int, int],
                  cache_counter: int,
                  test_surf: engine.Surface,
                  align: HAlignment = HAlignment.LEFT) -> engine.Surface:
        """Testing only"""
        return self._draw(surf, topleft, align, cache_counter, test_surf)
