from enum import Enum
from rtree.storage import RTreeStorage


class RTreeSplitType(Enum):
    TYPE1 = 1,
    TYPE2 = 2,
    TYPE3 = 3


class RTree:
    def __init__(self, storage: RTreeStorage):
        self._storage = storage