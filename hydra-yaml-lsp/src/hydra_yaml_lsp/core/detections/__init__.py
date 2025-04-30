from .interpolation import (
    InterpolationHighlight,
    InterpolationPosition,
    detect_interpolation_positions,
)
from .special_key import SpecialKeyPosition, detect_special_keys

__all__ = [
    "SpecialKeyPosition",
    "detect_special_keys",
    "InterpolationHighlight",
    "InterpolationPosition",
    "detect_interpolation_positions",
]
