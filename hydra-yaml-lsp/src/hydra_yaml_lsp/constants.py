from enum import StrEnum
from typing import TypedDict


class SpecialKeyInfo(TypedDict):
    """Information about a Hydra special key for completion and hover
    features."""

    detail: str
    documentation: str


class HydraSpecialKey(StrEnum):
    """Keywords of hydra."""

    TARGET = "_target_"
    ARGS = "_args_"
    RECURSIVE = "_recursive_"
    PARTIAL = "_partial_"
    CONVERT = "_convert_"

    @property
    def info(self) -> SpecialKeyInfo:
        """Get detailed information about the special key.

        Returns:
            A dictionary with detail and documentation about the special key.
        """
        match self:
            case HydraSpecialKey.TARGET:
                return {
                    "detail": "Target module path",
                    "documentation": "Specifies the Python object to instantiate or call.",
                }
            case HydraSpecialKey.ARGS:
                return {
                    "detail": "Arguments for the target",
                    "documentation": "Provides positional arguments for the target function or class.",
                }
            case HydraSpecialKey.RECURSIVE:
                return {
                    "detail": "Recursive resolution flag",
                    "documentation": "Controls whether to recursively instantiate nested configurations.",
                }
            case HydraSpecialKey.PARTIAL:
                return {
                    "detail": "Partial instantiation flag",
                    "documentation": "When true, returns a functools.partial instead of calling the target.",
                }
            case HydraSpecialKey.CONVERT:
                return {
                    "detail": "Conversion specification",
                    "documentation": "Specifies how to convert the object after instantiation.",
                }


class HydraUtilityFunctions(StrEnum):
    GET_OBJECT = "get_object"
    GET_CLASS = "get_class"
    GET_METHOD = "get_method"
    GET_STATIC_METHOD = "get_static_method"

    @property
    def import_path(self) -> str:
        return f"hydra.utils.{self.value}"

    @classmethod
    def is_hydra_utility_function(cls, path: str) -> bool:
        return path.rsplit(".", 1)[-1] in cls
