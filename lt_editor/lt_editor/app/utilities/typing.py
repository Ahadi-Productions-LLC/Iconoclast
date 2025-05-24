from typing import Dict, Tuple, Union

Pos = Tuple[int, int]

Point = Tuple[int, int]
Segment = Tuple[Point, Point]

NID = str
UID = int
Color3 = Tuple[int, int, int]
Color4 = Tuple[int, int, int, int]

Primitive = Union[int, float, str, bool, None]
NestedPrimitiveList = Union[Primitive, 'NestedPrimitiveList', 'NestedPrimitiveDict']
NestedPrimitiveDict = Dict[str, Union[Primitive, 'NestedPrimitiveDict', 'NestedPrimitiveList']]
