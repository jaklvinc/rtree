from typing import Tuple


class NonLeafEntry:
    def __init__(self, first_coord: list, second_coord: list, child_idx: int):
        self.first_coord = first_coord
        self.second_coord = second_coord
        self.child_idx = child_idx

    def __eq__(self, other):
        if not isinstance(other, NonLeafEntry):
            return False
        return self.first_coord == other.first_coord and self.second_coord == other.second_coord and self.child_idx == other.child_idx

    def __ne__(self, other):
        return not self.__eq__(other)

    def get_bounding_box(self) -> Tuple[list, list]:
        return self.first_coord, self.second_coord


class LeafEntry:
    def __init__(self, coord: list, data_point: int):
        self.coord = coord
        self.data_point = data_point

    def get_bounding_box(self) -> Tuple[list, list]:
        return self.coord, self.coord

    def __eq__(self, other):
        if not isinstance(other, LeafEntry):
            return False
        return self.coord == other.coord and self.data_point == other.data_point

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.data_point)


class Node:
    def __init__(self, is_leaf: bool, max_size: int):
        self._is_leaf = is_leaf
        self._max_size = max_size

        self.entries = list()
    
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
