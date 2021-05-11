from abc import ABC, abstractmethod
from enum import Enum
import copy


# TODO: probably move all of this into package?

class SplitType(Enum):
    TYPE1 = 1,
    TYPE2 = 2,
    TYPE3 = 3


class Index:
    def __init__(self,data):
        self.container = data
        self.child = None

class Node:
    def __init__(self,M):
        self.M = M
        self.storedData = list(Index)
    
    def Add(self,data = tuple()):
        idx = Index(data)
        if ( self.storedData.count() < self.M ):
            self.storedData.append(idx)
        else:
            for index in self.storedData:
                pass



class Tree:
    def __init__(self,dim,insertType,M = 4):
        self.dim = dim
        self.insType = insertType
        self.m = M
        self.root = None
    
    def Insert(self,toAdd = tuple()):
        if ( toAdd.count() != self.dim ):
            return False
            
        node = Node(self.m)
        if ( self.root == None ):
            self.root=node
        self.root.Add(toAdd)


class RTreeStorage(ABC):
    @abstractmethod
    def get_dim(self) -> int:
        pass

    @abstractmethod
    def get_m(self) -> int:
        pass

    @abstractmethod
    def get_split_type(self) -> SplitType:
        pass

    @abstractmethod
    def get_node(self, index: int) -> Node:
        pass

    @abstractmethod
    def set_node(self, index: int, node: Node):
        pass

    # Returns index
    @abstractmethod
    def add_node(self, node: Node) -> int:
        pass


class MemoryRTreeStorage(RTreeStorage):
    def __init__(self, dim: int, m: int, split_type: SplitType):
        self._dim = dim
        self._m = m
        self._split_type = split_type

        self._data = []

    def get_dim(self) -> int:
        return self._dim

    def get_m(self) -> int:
        return self._m

    def get_split_type(self) -> SplitType:
        return self._split_type

    def get_node(self, index: int) -> Node:
        return copy.deepcopy(self._data[index])

    def set_node(self, index: int, node: Node):
        self._data[index] = copy.deepcopy(node)

    def add_node(self, node: Node) -> int:
        self._data.append(copy.deepcopy(node))
        return len(self._data) - 1


# WIP
class DiskRTreeStorage(RTreeStorage):
    def __init__(self, filename: str):
        pass

    def get_dim(self) -> int:
        pass

    def get_m(self) -> int:
        pass

    def get_split_type(self) -> SplitType:
        pass

    def get_node(self, index: int) -> Node:
        pass

    def set_node(self, index: int, node: Node):
        pass

    def add_node(self, node: Node) -> int:
        pass


class RTree:
    def __init__(self, storage: RTreeStorage):
        self._storage = storage
