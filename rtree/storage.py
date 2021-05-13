from abc import ABC, abstractmethod
from typing import Tuple
import copy
import os
import math
from .split_type import RTreeSplitType
from .node import Node, NonLeafEntry, LeafEntry


class Storage(ABC):
    @abstractmethod
    def get_dim(self) -> int:
        pass

    @abstractmethod
    def get_node_size(self) -> int:
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

    def _entry_size(self, is_leaf: bool) -> int:
        return 8 * self.get_dim() * (1 if is_leaf else 2) + 8

    def _max_entries(self, is_leaf: bool) -> int:
        return math.floor(self.get_node_size() / self._entry_size(is_leaf))


class MemoryStorage(Storage):
    def __init__(self, dim: int, node_size: int, split_type: RTreeSplitType):
        self._dim = dim
        self._node_size = node_size
        self._split_type = split_type

        self._data = []

    def get_dim(self) -> int:
        return self._dim

    def get_node_size(self) -> int:
        return self._node_size

    def get_split_type(self) -> RTreeSplitType:
        return self._split_type

    def count(self) -> int:
        return len(self._data)

    def get_node(self, index: int) -> Node:
        is_leaf = self._data[index][0]
        node = Node(is_leaf, self._max_entries(is_leaf), (0, 0))
        node.entries = copy.deepcopy(self._data[index][1])
        return node

    def set_node(self, index: int, node: Node):
        self._data[index] = (node.is_leaf(), copy.deepcopy(node.entries))

    def add_node(self, node: Node) -> int:
        self._data.append((node.is_leaf(), copy.deepcopy(node.entries)))
        return len(self._data) - 1


# WIP
class DiskStorage(Storage):
    HEADER_SIZE = 13
    CACHE_SIZE = 1024

    def __init__(self, filename: str):
        self._file = open(filename, 'r+b')
        data = self._file.read(self.HEADER_SIZE)
        self._dim = int.from_bytes(data[:4], byteorder='little', signed=False)
        self._node_size = int.from_bytes(data[4:12], byteorder='little', signed=False)
        self._split_type = RTreeSplitType(int.from_bytes(data[12:], byteorder='little', signed=False))

        self._cache = []

        for i in range(self.CACHE_SIZE):
            # index, changed(bool), is_leaf, entries
            self._cache.append((None, None, None, None))

    @classmethod
    def write_header(cls, filename: str, dimensions: int, node_size: int, split_type: RTreeSplitType):
        data = bytearray(cls.HEADER_SIZE)
        data[:4] = dimensions.to_bytes(4, byteorder='little', signed=False)
        data[4:12] = node_size.to_bytes(8, byteorder='little', signed=False)
        data[12:] = split_type.value.to_bytes(1, byteorder='little', signed=False)

        with open(filename, 'wb') as file:
            file.write(data)

    def get_dim(self) -> int:
        return self._dim

    def get_node_size(self) -> int:
        return self._node_size

    def get_split_type(self) -> RTreeSplitType:
        return self._split_type

    def count(self) -> int:
        self._file.seek(0, 2)
        return round((self._file.tell() - self.HEADER_SIZE) / self._node_size)

    def get_node(self, index: int) -> Node:
        i = self._get(index, True)
        is_leaf = self._cache[i][2]
        node = Node(is_leaf, self._max_entries(is_leaf), (0, 0))
        node.entries = copy.deepcopy(self._cache[i][3])
        return node

    def set_node(self, index: int, node: Node):
        i = self._get(index, False)

        self._cache[i] = (index, True, node.is_leaf(), copy.deepcopy(node.entries))

    def add_node(self, node: Node) -> int:
        index = self.count()
        self._write(index, node.is_leaf(), node.entries)

        return index

    def _get(self, index: int, read: bool):
        if index >= self.count():
            raise IndexError

        i = index % self.CACHE_SIZE
        if self._cache[i][0] is None or self._cache[i][0] != index:
            if self._cache[i][1] is not None and self._cache[i][1]:
                self._write(self._cache[i][0], self._cache[i][2], self._cache[i][3])

            if read:
                is_leaf, entries = self._read(index)
                self._cache[i] = (index, False, is_leaf, entries)
        return i

    def _write(self, index: int, is_leaf: bool, entries: list):
        data = bytearray(self._node_size)
        data[:1] = is_leaf.to_bytes(1, byteorder='little', signed=False)
        data[1:9] = len(entries).to_bytes(8, byteorder='little', signed=False)

        i = 9

        for entry in entries:
            if is_leaf:
                i = self._serialize_coord(data, i, entry.coord)
                data[i:i+8] = entry.data_point.to_bytes(8, byteorder='little', signed=False)
                i += 8
            else:
                i = self._serialize_coord(data, i, entry.first_coord)
                i = self._serialize_coord(data, i, entry.second_coord)
                data[i:i+8] = entry.child_idx.to_bytes(8, byteorder='little', signed=False)
                i += 8

        if len(data) > self.get_node_size():
            raise AttributeError

        self._file.seek(self.HEADER_SIZE + index * self._node_size)
        self._file.write(data)

    def _read(self, index: int) -> Tuple[bool, list]:
        self._file.seek(self.HEADER_SIZE + index * self._node_size)
        data = self._file.read(self._node_size)
        is_leaf = bool.from_bytes(data[:1], byteorder='little', signed=False)
        n = int.from_bytes(data[1:9], byteorder='little', signed=False)
        step = self._entry_size(is_leaf)

        i = 9
        entries = []

        for i in range(n):
            if is_leaf:
                i, coord = self._deserialize_coord(data, i)
                data_point = int.from_bytes(data[i:i+8], byteorder='little', signed=False)
                i += 8
                entries.append(LeafEntry(coord, data_point))
            else:
                i, first_coord = self._deserialize_coord(data, i)
                i, second_coord = self._deserialize_coord(data, i)
                child_idx = int.from_bytes(data[i:i + 8], byteorder='little', signed=False)
                i += 8
                entries.append(NonLeafEntry(first_coord, second_coord, child_idx))

        return is_leaf, entries

    def _serialize_coord(self, data, i: int, coord: list) -> int:
        for x in coord:
            data[i:i+8] = x.to_bytes(8, byteorder='little', signed=True)
            i += 8
        return i

    def _deserialize_coord(self, data, i: int) -> Tuple[int, list]:
        coord = []
        for _ in range(self._dim):
            coord.append(int.from_bytes(data[i:i + 8], byteorder='little', signed=True))
            i += 8
        return i, coord

    def __del__(self):
        for index, changed, is_leaf, entries in self._cache:
            if index is not None and changed:
                self._write(index, is_leaf, entries)
        self._file.close()
