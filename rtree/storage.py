from abc import ABC, abstractmethod
import copy
from .split_type import RTreeSplitType
from .node import Node


class RTreeStorage(ABC):
    @abstractmethod
    def get_dim(self) -> int:
        pass

    @abstractmethod
    def get_m(self) -> int:
        pass

    @abstractmethod
    def get_split_type(self) -> RTreeSplitType:
        pass

    # Number of nodes
    @abstractmethod
    def count(self) -> int:
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
    def __init__(self, dim: int, m: int, split_type: RTreeSplitType):
        self._dim = dim
        self._m = m
        self._split_type = split_type

        self._data = []

    def get_dim(self) -> int:
        return self._dim

    def get_m(self) -> int:
        return self._m

    def get_split_type(self) -> RTreeSplitType:
        return self._split_type

    def count(self) -> int:
        return len(self._data)

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

    def get_split_type(self) -> RTreeSplitType:
        pass

    def count(self) -> int:
        pass

    def get_node(self, index: int) -> Node:
        pass

    def set_node(self, index: int, node: Node):
        pass

    def add_node(self, node: Node) -> int:
        pass
