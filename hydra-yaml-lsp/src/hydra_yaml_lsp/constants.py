from enum import StrEnum


class HydraSpecialKey(StrEnum):
    """Keywords of hydra."""

    TARGET = "_target_"
    ARGS = "_args_"
    RECURSIVE = "_recursive_"
    PARTIAL = "_partial_"
    CONVERT = "_convert_"
