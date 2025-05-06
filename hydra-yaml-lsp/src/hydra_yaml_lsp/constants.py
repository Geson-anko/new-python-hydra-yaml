from enum import StrEnum
from typing import Self, TypedDict


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


class HydraUtilityFunction(StrEnum):
    GET_OBJECT = "get_object"
    GET_CLASS = "get_class"
    GET_METHOD = "get_method"
    GET_STATIC_METHOD = "get_static_method"

    @property
    def import_path(self) -> str:
        return f"hydra.utils.{self.value}"

    @classmethod
    def is_hydra_utility_function(cls, path: str) -> bool:
        return path.startswith("hydra.utils.") and path.rsplit(".", 1)[-1] in cls

    @classmethod
    def from_import_path(cls, path: str) -> Self:
        if cls.is_hydra_utility_function(path):
            return cls(path.rsplit(".", 1)[-1])
        raise ValueError(f"{path=} is not hydra utility function import path!")


class ConvertValueInfo(TypedDict):
    detail: str


class HydraConvertValue(StrEnum):
    NONE = "none"
    PARTIAL = "partial"
    OBJECT = "object"
    ALL = "all"

    @property
    def info(self) -> ConvertValueInfo:
        """Get detailed information about the _convert_ value."""
        match self:
            case HydraConvertValue.NONE:
                return {"detail": "Default behavior, Use OmegaConf containers"}
            case HydraConvertValue.PARTIAL:
                return {
                    "detail": "Convert OmegaConf containers to dict and list, except Structured Configs, which remain as DictConfig instances."
                }
            case HydraConvertValue.OBJECT:
                return {
                    "detail": "Convert OmegaConf containers to dict and list, except Structured Configs, which are converted to instances of the backing dataclass / attr class using OmegaConf.to_object."
                }
            case HydraConvertValue.ALL:
                return {"detail": "Convert everything to primitive containers."}
