from itertools import combinations
from queue import Queue
from .split_type import RTreeSplitType
from .storage import Storage, MemoryStorage, DiskStorage
from .node import Node, LeafEntry, NonLeafEntry
from typing import Tuple, List


def bounding_box_area(box: Tuple[list, list]) -> int:
    area = 1
    dimensions = (abs(x - y) + 1 for x in box[0] for y in box[1])
    for dimension in dimensions:
        area *= dimension
    return area


def min_bounding_box(first: Tuple[list, list], second: Tuple[list, list]) -> Tuple[list, list]:
    first_coords = list()
    second_coords = list()
    for x in range(len(first[0])):
        first_coords.append(min(first[0][x], second[0][x]))
        second_coords.append(max(first[1][x], second[1][x]))
    return first_coords, second_coords


def overlaps(first: Tuple[list, list], second: Tuple[list, list]) -> bool:
    for x in range(len(first[0])):
        if first[0][x] > second[1][x] or first[1][x] < second[0][x]:
            return False
    return True


class RTree:
    def __init__(self, storage: Storage):
        self._storage = storage

    @classmethod
    def from_file(cls, filename: str):
        return cls(DiskStorage(filename))

    @classmethod
    def create_in_file(cls, filename: str, dimensions: int, node_size: int, split_type: RTreeSplitType):
        DiskStorage.write_header(filename, dimensions, node_size, split_type)
        return cls.from_file(filename)

    @classmethod
    def create_in_memory(cls, dimensions: int, node_size: int, split_type: RTreeSplitType):
        return cls(MemoryStorage(dimensions, node_size, split_type))

    def _choose_leaf(self, node_idx: int, new_entry: LeafEntry) -> Node:
        node_queue = Queue(0)
        node_queue.put(node_idx)

        while not node_queue.empty():
            this_node_idx = node_queue.get()
            node = self._storage.get_node(this_node_idx)
            node.set_idx(this_node_idx)
            if node.is_leaf():
                return node
            else:
                min_area = float('inf')
                min_entry = NonLeafEntry
                for entry in node.entries:
                    new_bounding_box = min_bounding_box(entry.get_bounding_box(), new_entry.get_bounding_box())
                    new_box_area = bounding_box_area(new_bounding_box)

                    if new_box_area < min_area:
                        min_area = new_box_area
                        min_entry = entry
                node_queue.put(min_entry.child_idx)

    def _brute_force_split(self, split_this: Node):
        # TODO
        pass

    def _quadratic_split(self, split_this: Node):
        max_area = float(-1)
        max_area_pair = 0
        for pair in combinations(split_this.entries, 2):
            bounding_box = min_bounding_box(pair[0], pair[1])
            box_area = bounding_box_area(bounding_box)
            if box_area > max_area:
                max_area = box_area
                max_area_pair = pair[0], pair[1]


        old_parent = split_this.get_parent_entry()
        if old_parent == 0:
            new_parent_node = Node(is_leaf=False, max_size=self._storage.get_node_size())
            self._storage.set_node(0, new_parent_node)
            old_parent = (0, 0)
        first_node = Node(is_leaf=True, max_size=self._storage.get_node_size())
        first_node.add_entry(max_area_pair[0])
        second_node = Node(is_leaf=True, max_size=self._storage.get_node_size())
        second_node.add_entry(max_area_pair[1])
        # TODO

    def _linear_split(self, split_this: Node):
        pass

    def _split_node(self, split_this: Node, insert_node: RTreeSplitType):
        if insert_node == RTreeSplitType.BRUTE_FORCE:
            self._brute_force_split(split_this)
        elif insert_node == RTreeSplitType.QUADRATIC:
            self._quadratic_split(split_this)
        elif insert_node == RTreeSplitType.LINEAR:
            self._linear_split(split_this)
        pass

    def insert(self, to_insert: LeafEntry):
        insert_node = self._choose_leaf(0, to_insert)
        if insert_node.add_entry(to_insert):
            self._storage.set_node(insert_node.get_idx(), insert_node)
        else:
            self._split_node(insert_node, self._storage.get_split_type())
        # TODO

    def search_range(self, search_box: Tuple[list, list], node_idx: int = 0) -> List[LeafEntry]:
        node_queue = Queue(0)
        node_queue.put(self._storage.get_node(node_idx))
        return_list = list()

        # loads from queue until entry on our position is found or not
        while not node_queue.empty():
            this_node = node_queue.get()

            # if the node is not leaf, adds all child nodes that overlap our position to the queue
            if not this_node.is_leaf():
                for entry in this_node.entries:
                    if overlaps(entry.get_bounding_box(), search_box):
                        node_queue.put(self._storage.get_node(this_node.get_child_idx()))
            # if the node is leaf, iterates through the entries and if found, returns the data on our desired position
            else:
                for entry in this_node.entries:
                    if overlaps(entry.get_bounding_box(), search_box):
                        return_list.append(entry)
        return return_list

    def find_in_range(self):
        # TODO
        pass
