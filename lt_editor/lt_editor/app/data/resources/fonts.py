from dataclasses import asdict, dataclass, field
import os
from pathlib import Path
from typing import Dict, List, Optional, Set
from typing_extensions import override

from app.data.resources.base_catalog import ManifestCatalog
from app.data.resources.resource_prefab import WithResources
from app.data.serialization.dataclass_serialization import dataclass_from_dict
from app.utilities.data import Prefab
from app.utilities.typing import Color4, NestedPrimitiveDict

@dataclass
class Font(WithResources, Prefab):
    nid: str                                                                             #: NID of the font.
    file_name: str = None                                                                #: Root path without file ending, e.g. `project.ltproj/resources/convo`.
    fallback_ttf: str = None                                                             #: name of the .ttf file (in this directory) to be used as a fallback if the main font cannot render anything
    fallback_size: int = 16                                                              #: what size the fallback font should be rendered at. This may well differ depending on the font, especially at these lower resolutions!
    default_color: Optional[str] = None                                                  #: The key of the default color in the palette, if any.
    outline_font: bool = False                                                           #: whether this font has an outline
    palettes: Dict[str, List[Color4]] = field(default_factory=dict)                      #: A dictionary of color names to the palette of the font color.

    def image_path(self):
        return self.file_name + '.png'

    def index_path(self):
        return self.file_name + '.idx'

    def ttf_path(self):
        if self.fallback_ttf:
            return str(Path(self.file_name).parent / self.fallback_ttf)

    def primary_color(self, color):
        palette = self.palettes.get(color)
        if palette:
            return palette[0]
        return None

    def secondary_color(self, color):
        palette = self.palettes.get(color)
        if palette:
            if len(palette) > 1:
                return palette[1]
            return palette[0]
        return None

    @override
    def set_full_path(self, path: str) -> None:
        self.file_name = path

    @override
    def used_resources(self) -> List[Optional[Path]]:
        paths = [Path(self.image_path()), Path(self.index_path())]
        paths.append(Path(self.ttf_path()) if self.ttf_path() else None)
        return paths

    def save(self):
        s_dict = asdict(self)
        del s_dict["file_name"]
        return s_dict

    @classmethod
    def restore(cls, s_dict):
        return dataclass_from_dict(cls, s_dict)

class FontCatalog(ManifestCatalog[Font]):
    datatype = Font
    manifest = 'fonts.json'
    title = 'fonts'
    filetype = ''