from enum import StrEnum


class HydraSpecialKey(StrEnum):
    """Keywords of hydra."""

    TARGET = "_target_"
    ARGS = "_args_"
    RECURSIVE = "_recursive_"
    PARTIAL = "_partial_"
    CONVERT = "_convert_"


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
