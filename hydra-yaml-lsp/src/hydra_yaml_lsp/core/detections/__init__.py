from .interpolation import (
    InterpolationHighlight,
    InterpolationPosition,
    detect_interpolation_positions,
)
from .special_key import SpecialKeyPosition, detect_special_keys
from .target_value import (
    TargetValueHighlight,
    TargetValuePosition,
    detect_target_values,
)

__all__ = [
    "SpecialKeyPosition",
    "detect_special_keys",
    "InterpolationHighlight",
    "InterpolationPosition",
    "detect_interpolation_positions",
    "TargetValueHighlight",
    "TargetValuePosition",
    "detect_target_values",
]
