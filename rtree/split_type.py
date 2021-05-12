from enum import Enum


class RTreeSplitType(Enum):
    BRUTE_FORCE = 1,
    QUADRATIC = 2,
    LINEAR = 3
