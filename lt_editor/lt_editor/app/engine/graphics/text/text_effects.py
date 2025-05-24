"""Note to all devs trying to add a new TextEffect:
Unless you have special requirements, make sure your new effect has
a cycle period that is a divisor of 240, some suggestions are
30, 60, or 120 but any divisor of 240 is fine.
Static effects should have a cycle period of 1.
A cycle period of 240 corresponds to 4 seconds for a full effect cycle
at the default FPS of 60. This makes sure that caching does not require
excessive amounts of memory to store all those frames.
Making sure an effect has a cycle period of a divisor of 240 makes sure
that the least common multiple of the combination of effect cycle periods
is always a maximum of 240.
"""

from __future__ import annotations
from typing import List, Dict, Tuple

import math
from random import Random

from app.utilities.typing import NID
from app.utilities.utils import tuple_add

_rng = Random()

# corresponds to 4s at 60FPS
RECOMMENDED_CYCLE_PERIOD = 240
# corresponds to 10s at 60FPS
MAX_RECOMMENDED_CYCLE_PERIOD = 600


class TextSettings:

    def __init__(self, color: NID, offset: Tuple[float, float]):
        self.color = color
        self.offset = offset

    def apply(self, effects: List[TextEffect]):
        for effect in effects:
            effect.apply(self)


class TextEffect:
    """A text effect that applies a consistent effect to a text chunk"""

    nid: NID = "text_effect"
    cycle_period: int = 1

    def __init__(self):
        raise Exception("TextEffect should not be directly instantiated")

    def __str__(self):
        return self.nid

    def __repr__(self):
        return self.nid

    def update(self):
        """update the internal state of this TextEffect, should only be called once per frame"""
        pass

    def apply(self, settings: TextSettings):
        """modifies settings in place

        Args:
            settings (TextSettings): settings to modify
        """
        pass

    def as_tags(self) -> Tuple[str, str]:
        """recreate the starting and ending tags used for this text effect

        Returns:
            Tuple[str, str]: starting and ending tags for this
        """
        return "", ""

    def max_offset(self) -> Tuple[int, int, int, int]:
        """get the maximum offset in each cardinal direction rounded up to the nearest integer

        Returns:
            Tuple[int, int, int, int]: north, east, south, west
        """
        return 0, 0, 0, 0


class NoneEffect(TextEffect):
    nid = "None"

    def __init__(self):
        pass


class ColorEffect(TextEffect):
    nid = "color"

    def __init__(self, idx: int, color: NID):
        self._idx = idx
        self._color = color

    def __str__(self):
        return f"{self._color}"

    def apply(self, settings: TextSettings):
        settings.color = self._color

    def as_tags(self) -> Tuple[str, str]:
        return (f"<{self._color}>", "</>")


class JitterEffect(TextEffect):
    nid = "jitter"
    cycle_period = (
        1000003  # a very large prime that you probably shouldn't try to cache
    )

    @classmethod
    def _get_jitter(cls, magnitude: float = 1) -> Tuple[float, float]:
        return (_rng.gauss(0, 1) * magnitude, _rng.gauss(0, 1) * magnitude)

    def __init__(self, idx: int = 0, magnitude: float = 1, wait: int = 3):
        self._idx = idx
        self._magnitude = magnitude
        self._wait = wait

        self._jitter = self._jitter = self._get_jitter(self._magnitude)
        self._count = 0

    def update(self):
        # prevent infinitely counting up
        self._count = (self._count + 1) % self._wait
        if self._count % self._wait == 0:
            self._jitter = self._get_jitter(self._magnitude)

    def apply(self, settings: TextSettings):
        settings.offset = tuple_add(settings.offset, self._jitter)

    def as_tags(self) -> Tuple[str, str]:
        return (
            f"<{self.nid} idx={self._idx} magnitude={self._magnitude} wait={self._wait}>",
            "</>",
        )

    def max_offset(self) -> Tuple[float, float, float, float]:
        # 95% chance to be within 2 std, if it gets cut off oh well
        return (abs(self._magnitude) * 2, ) * 4


def _initialize_sin_sequence(cycle_period: int) -> List[float]:
    return [math.sin(x * 2 * math.pi / cycle_period) for x in range(cycle_period)]


class SinEffect(TextEffect):
    nid = "sin"
    cycle_period = 30

    _sin_sequence = _initialize_sin_sequence(cycle_period)

    def __init__(self, idx: int = 0, x_amplitude: float = 0, y_amplitude: float = 3.5):
        self._idx = idx
        self._amplitude = (x_amplitude, y_amplitude)
        self._count = 0

    def update(self):
        self._count = (self._count + 1) % self.cycle_period

    def apply(self, settings: TextSettings):
        idx = (self._count + self._idx * self.cycle_period // 10) % self.cycle_period
        x_offset = settings.offset[0] + self._sin_sequence[idx] * self._amplitude[0]
        y_offset = settings.offset[1] + self._sin_sequence[idx] * self._amplitude[1]
        settings.offset = (x_offset, y_offset)

    def as_tags(self) -> Tuple[str, str]:
        return (
            f"<{self.nid} idx={self._idx} x_amplitude={self._amplitude[0]} y_amplitude={self._amplitude[1]}>",
            "</>",
        )

    def max_offset(self) -> Tuple[int, int, int, int]:
        return (
            abs(self._amplitude[1]),
            abs(self._amplitude[0]),
        ) * 2


class CoordinatedTextEffect:
    """A text effect that decays into a character wise application of a TextEffect with incrementing idx.
    This class is only used for preprocessing and decays to a TextEffect applied per character after
    preprocessing. Depending on the implementation of the TextEffect, and how it interacts
    with an idx variable, it can be used to generate coordinated text effects.
    """

    nid: NID = "coordinated_text_effect"

    def __init__(self):
        raise Exception("CoordinatedTextEffect should not be directly instantiated")

    def __str__(self):
        return self.nid

    def next(self) -> TextEffect:
        """generate the next text effect in the sequence to implement this coordinated effect

        Returns:
            TextEffect: the next text effect in the sequence
        """
        pass


class Jitter2Effect(CoordinatedTextEffect):
    nid = "jitter2"

    def __init__(self, magnitude: float = 1, wait: int = 3):
        self._magnitude = magnitude
        self._wait = wait
        self._idx = 0

    def next(self) -> TextEffect:
        impl = JitterEffect(self._idx, self._magnitude, self._wait)
        self._idx += 1
        return impl


class WaveEffect(CoordinatedTextEffect):
    nid = "wave"

    def __init__(self, amplitude: float = 3.5):
        self._amplitude = amplitude
        self._idx = 0

    def next(self) -> TextEffect:
        impl = SinEffect(self._idx, 0, self._amplitude)
        self._idx += 1
        return impl


class Wave2Effect(CoordinatedTextEffect):
    nid = "wave2"

    def __init__(self, x_amplitude: float = 2, y_amplitude: float = 3.5):
        self._amplitude = (x_amplitude, y_amplitude)
        self._idx = 0

    def next(self) -> TextEffect:
        impl = SinEffect(self._idx, self._amplitude[0], self._amplitude[1])
        self._idx += 1
        return impl


TEXT_EFFECTS: Dict[NID, TextEffect] = {
    effect.nid: effect
    for effect in TextEffect.__subclasses__()
}

COORDINATED_TEXT_EFFECTS: Dict[NID, CoordinatedTextEffect] = {
    effect.nid: effect
    for effect in CoordinatedTextEffect.__subclasses__()
}
