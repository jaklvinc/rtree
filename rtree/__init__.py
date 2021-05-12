from enum import Enum
from .storage import RTreeStorage
from .node import Entry, Node


class RTreeSplitType(Enum):
    TYPE1 = 1,
    TYPE2 = 2,
    TYPE3 = 3


class RTree:
    def __init__(self, storage: RTreeStorage):
        self._storage = storage
    
    def _split_node(self):
        pass
    
    def _add_to_node(self, node : Node ):
        pass
    
    def insert(self, idx : tuple() , data : int ):
        root_node=self._storage.get_node(0)
        new_entry=Entry(idx,data)


        pass

    def find(self):
        pass

    def find_in_range(self):
        pass