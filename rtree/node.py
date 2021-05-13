from typing import Tuple


class NonLeafEntry:
    def __init__(self, first_coord: list, second_coord: list, child_idx: int):
        self.first_coord = first_coord
        self.second_coord = second_coord
        self.child_idx = child_idx

    def get_bounding_box(self) -> Tuple[list, list]:
        return self.first_coord, self.second_coord


class LeafEntry:
    def __init__(self, coord: list, data_point: int):
        self.coord = coord
        self.data_point = data_point

    def get_bounding_box(self) -> Tuple[list, list]:
        return self.coord, self.coord


class Node:
    def __init__(self, is_leaf: bool, max_size: int, parent: Tuple[int, int] = 0):
        self._is_leaf = is_leaf
        self._max_size = max_size
        self._parent_entry = parent

        self.entries = list()

    def get_parent_entry(self) -> Tuple[int, int]:
        return self._parent_entry
    
    def is_leaf(self) -> bool:
        return self._is_leaf
    
    def add_entry(self, entry) -> bool:
        if len(self.entries) == self._max_size:
            self.entries.append(entry)
            return False
        else:
            self.entries.append(entry)
            return True

    def set_entry(self, entry, idx: int) -> None:
        self.entries[idx] = entry
        pass
