from itertools import combinations
from collections import deque
from .split_type import RTreeSplitType
from .storage import Storage, MemoryStorage, DiskStorage
from .node import Node, LeafEntry, NonLeafEntry
from typing import Tuple, List


def bounding_box_area(box: Tuple[list, list]) -> int:
    area = 1
    dimensions = (abs(x - y) + 1 for x, y in zip(box[0], box[1]))
    for dimension in dimensions:
        area *= dimension
    return area


def min_bounding_box(first: Tuple[list, list], second: Tuple[list, list]) -> Tuple[list, list]:
    first_coords = list()
    second_coords = list()
    for x, _ in enumerate(first[0]):
        first_coords.append(min(first[0][x], second[0][x]))
        second_coords.append(max(first[1][x], second[1][x]))
    return first_coords, second_coords


def two_box_area(first: Tuple[list, list], second: Tuple[list, list]) -> int:
    return bounding_box_area(min_bounding_box(first, second))


def overlaps(first: Tuple[list, list], second: Tuple[list, list]) -> bool:
    for x in range(len(first[0])):
        if first[0][x] > second[1][x] or first[1][x] < second[0][x]:
            return False
    return True


def overlaps_distance(point: List[int], distance: int, box: Tuple[list, list]) -> bool:
    my_dist = 0
    for x in range(pow(2, len(box[0]))):
        bin_x = bin(x)[2:].zfill(len(box[0]))
        indices = [int(i) for i in bin_x]
        for idx, elem in zip(range(len(indices)), indices):
            my_dist += abs(point[idx] - box[elem][idx])
        if my_dist < distance:
            return True
    return False


def pick_next(entries_left: deque, first_bounding_rect: Tuple[list, list], second_bounding_rect: Tuple[list, list]):
    max_dif_size = -1
    max_dif_entry = entries_left.popleft()
    for i in range(len(entries_left)):
        check_entry = entries_left.popleft()
        first_dif = two_box_area(check_entry.get_bounding_box(), first_bounding_rect) - \
            bounding_box_area(first_bounding_rect)
        second_dif = two_box_area(check_entry.get_bounding_box(), second_bounding_rect) - \
            bounding_box_area(second_bounding_rect)
        dif = abs(first_dif - second_dif)
        if dif > max_dif_size:
            max_dif_size = dif
            entries_left.append(max_dif_entry)
            max_dif_entry = check_entry
        else:
            entries_left.append(check_entry)
    return max_dif_entry


def new_parent_entry(node: Node, idx: int) -> NonLeafEntry:
    node_new_coords = node.entries[0].get_bounding_box()
    for entry in node.entries[1:]:
        node_new_coords = min_bounding_box(node_new_coords, entry.get_bounding_box())
    node_new_entry = NonLeafEntry(node_new_coords[0],
                                  node_new_coords[1],
                                  idx)
    return node_new_entry


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

    def get_dimensions(self) -> int:
        return self._storage.get_dim()

    def _choose_leaf(self, node_idx: int, new_entry: LeafEntry):
        # TODO MULTIWAY SEARCH
        node = self._storage.get_node(node_idx)
        if node.is_leaf():
            if node.add_entry(new_entry):
                self._storage.set_node(node_idx, node)
                return node_idx, node
            else:
                return node_idx, self._split_node(node)
        else:
            min_diff = float('inf')
            min_entry = None
            min_entry_idx = -1
            for idx, entry in enumerate(node.entries):
                new_bounding_box = min_bounding_box(entry.get_bounding_box(), new_entry.get_bounding_box())
                new_box_diff = bounding_box_area(new_bounding_box)-bounding_box_area(entry.get_bounding_box())

                if new_box_diff < min_diff:
                    min_entry_idx = idx
                    min_diff = new_box_diff
                    min_entry = entry
                elif new_box_diff == min_diff:
                    if bounding_box_area(entry.get_bounding_box()) < bounding_box_area(min_entry.get_bounding_box()):
                        min_entry_idx = idx
                        min_diff = new_box_diff
                        min_entry = entry

            idx, ret = self._choose_leaf(min_entry.child_idx, new_entry)
            if type(ret) is tuple:
                self._storage.set_node(min_entry.child_idx, ret[0])
                first_node_new_entry = new_parent_entry(ret[0], min_entry.child_idx)
                node.entries[min_entry_idx] = first_node_new_entry

                second_node_idx = self._storage.add_node(ret[1])
                second_node_new_entry = new_parent_entry(ret[1], second_node_idx)

                if node.add_entry(second_node_new_entry):
                    self._storage.set_node(node_idx, node)
                    return node_idx, node
                else:
                    return node_idx, self._split_node(node)
            else:
                node_new_entry = new_parent_entry(ret, min_entry.child_idx)
                node.entries[min_entry_idx] = node_new_entry
                self._storage.set_node(node_idx, node)
                return node_idx, node
        pass

    @staticmethod
    def _left_to_enter(split_this: Node, first_entry, second_entry):
        entries_left = deque()
        for entry in split_this.entries:
            if entry != first_entry and entry != second_entry:
                entries_left.append(entry)
        return entries_left

    @staticmethod
    def _add_accordingly(add_now, first_node_bounding_rect, second_node_bounding_rect, first_node, second_node):
        first_node_new_rect = min_bounding_box(add_now.get_bounding_box(), first_node_bounding_rect)
        second_node_new_rect = min_bounding_box(add_now.get_bounding_box(), second_node_bounding_rect)

        first_node_dif = bounding_box_area(first_node_new_rect) - bounding_box_area(first_node_bounding_rect)
        second_node_dif = bounding_box_area(second_node_new_rect) - bounding_box_area(second_node_bounding_rect)

        if first_node_dif < second_node_dif:
            first_node.add_entry(add_now)
            first_node_bounding_rect = first_node_new_rect
        elif second_node_dif < first_node_dif:
            second_node.add_entry(add_now)
            second_node_bounding_rect = second_node_new_rect
        elif bounding_box_area(first_node_bounding_rect) < bounding_box_area(second_node_bounding_rect):
            first_node.add_entry(add_now)
            first_node_bounding_rect = first_node_new_rect
        elif bounding_box_area(second_node_bounding_rect) < bounding_box_area(first_node_bounding_rect):
            second_node.add_entry(add_now)
            second_node_bounding_rect = second_node_new_rect
        elif len(first_node.entries) < len(second_node.entries):
            first_node.add_entry(add_now)
            first_node_bounding_rect = first_node_new_rect
        else:
            second_node.add_entry(add_now)
            second_node_bounding_rect = second_node_new_rect
        return first_node_bounding_rect, second_node_bounding_rect

    def _linear_split(self, split_this: Node):
        root_node = self._storage.get_node(0)
        # bounding box of all entries in the tree
        total_bounding_box = root_node.entries[0].get_bounding_box()
        for x, _ in enumerate(root_node.entries):
            total_bounding_box = min_bounding_box(total_bounding_box, root_node.entries[x].get_bounding_box())

        max_normalized_separation = float("-inf")
        first_entry = None
        second_entry = None
        for dim, _ in enumerate(split_this.entries[0].get_bounding_box()[0]):
            w = abs(total_bounding_box[1][dim]-total_bounding_box[0][dim])
            lowest_high_side = float('inf')
            lowes_high_entry = None
            highest_low_side = float('-inf')
            highest_low_entry = None
            for entry in split_this.entries:
                entry_box = entry.get_bounding_box()
                if entry_box[0][dim] > highest_low_side:
                    highest_low_side = entry_box[0][dim]
                    highest_low_entry = entry
                if entry_box[1][dim] < lowest_high_side:
                    lowest_high_side = entry_box[1][dim]
                    lowes_high_entry = entry
            separation = abs(lowest_high_side-highest_low_side)
            normalized_separation= separation/w
            if normalized_separation > max_normalized_separation:
                max_normalized_separation = normalized_separation
                first_entry = highest_low_entry
                second_entry = lowes_high_entry
        entries_left = self._left_to_enter(split_this, first_entry, second_entry)

        first_node_bounding_rect = (first_entry.get_bounding_box()[0], first_entry.get_bounding_box()[1])
        first_node = Node(is_leaf=split_this.is_leaf(), max_size=self._storage.get_node_size())
        first_node.add_entry(first_entry)

        second_node_bounding_rect = (second_entry.get_bounding_box()[0], second_entry.get_bounding_box()[1])
        second_node = Node(is_leaf=split_this.is_leaf(), max_size=self._storage.get_node_size())
        second_node.add_entry(second_entry)

        while entries_left:
            to_add = entries_left.popleft()
            first_node_bounding_rect, second_node_bounding_rect = self._add_accordingly(to_add,
                                                                                        first_node_bounding_rect,
                                                                                        second_node_bounding_rect,
                                                                                        first_node,
                                                                                        second_node)
        return first_node, second_node

    def _quadratic_split(self, split_this: Node) -> Tuple[Node, Node]:
        max_area = -1
        max_area_pair = tuple()
        for pair in combinations(split_this.entries, 2):
            bounding_box = min_bounding_box(pair[0].get_bounding_box(), pair[1].get_bounding_box())
            box_area = bounding_box_area(bounding_box)
            if box_area > max_area:
                max_area = box_area
                max_area_pair = (pair[0], pair[1])

        entries_left = self._left_to_enter(split_this, [0], max_area_pair[1])

        first_node_bounding_rect = (max_area_pair[0].get_bounding_box()[0], max_area_pair[0].get_bounding_box()[1])
        first_node = Node(is_leaf=split_this.is_leaf(), max_size=self._storage.get_node_size())
        first_node.add_entry(max_area_pair[0])

        second_node_bounding_rect = (max_area_pair[1].get_bounding_box()[0], max_area_pair[1].get_bounding_box()[1])
        second_node = Node(is_leaf=split_this.is_leaf(), max_size=self._storage.get_node_size())
        second_node.add_entry(max_area_pair[1])

        while entries_left:
            add_now = pick_next(entries_left, first_node_bounding_rect, second_node_bounding_rect)
            first_node_bounding_rect, second_node_bounding_rect = self._add_accordingly(add_now,
                                                                                        first_node_bounding_rect,
                                                                                        second_node_bounding_rect,
                                                                                        first_node,
                                                                                        second_node)

        return first_node, second_node

    def _all_splits(self, indices: List[int], x: int, to_print, splits: List[List[int]]):
        while x != len(indices):
            to_append = [int(item) for item in to_print]
            to_append.append(x)
            if len(to_append) != len(indices):
                splits.append(to_append)
            self._all_splits(indices, x + 1, to_print + str(x), splits)
            x += 1
        return

    def _brute_force_split(self, split_this: Node):

        split_indices = [x for x, _ in enumerate(split_this.entries)]
        splits = list()
        self._all_splits(split_indices, 0, '', splits)
        min_area_combined = float('inf')
        min_first_entries = None
        min_second_entries = None
        for split in splits:
            include_indices = [0] * len(split_this.entries)
            first_entries = list()
            second_entries = list()
            for index in split:
                include_indices[index] = 1
            for index, zero_one in enumerate(include_indices):
                if zero_one == 0:
                    first_entries.append(split_this.entries[index])
                else:
                    second_entries.append(split_this.entries[index])

            first_bounding_box = first_entries[0].get_bounding_box()
            for entry in first_entries:
                first_bounding_box = min_bounding_box(first_bounding_box, entry.get_bounding_box())
            first_area = bounding_box_area(first_bounding_box)

            second_bounding_box = second_entries[0].get_bounding_box()
            for entry in second_entries:
                second_bounding_box = min_bounding_box(second_bounding_box, entry.get_bounding_box())
            second_area = bounding_box_area(second_bounding_box)

            total_area = first_area+second_area
            if total_area < min_area_combined:
                min_first_entries = first_entries
                min_second_entries = second_entries
                min_area_combined = total_area

        first_node = Node(is_leaf=split_this.is_leaf(), max_size=self._storage.get_node_size())
        second_node = Node(is_leaf=split_this.is_leaf(), max_size=self._storage.get_node_size())

        for entry in min_first_entries:
            first_node.add_entry(entry)

        for entry in min_second_entries:
            second_node.add_entry(entry)

        return first_node, second_node

    def _split_node(self, split_this: Node):
        insert_node = self._storage.get_split_type()
        if insert_node == RTreeSplitType.BRUTE_FORCE:
            return self._brute_force_split(split_this)
        elif insert_node == RTreeSplitType.QUADRATIC:
            return self._quadratic_split(split_this)
        elif insert_node == RTreeSplitType.LINEAR:
            return self._linear_split(split_this)
        pass

    def insert(self, indices: List[int], data: int):
        to_insert = LeafEntry(indices, data)
        idx, ret = self._choose_leaf(0, to_insert)
        if type(ret) is tuple:
            new_root = Node(False, self._storage.get_node_size())
            first_node_idx = self._storage.add_node(ret[0])
            second_node_idx = self._storage.add_node(ret[1])
            new_first_node = new_parent_entry(ret[0], first_node_idx)
            new_second_node = new_parent_entry(ret[1], second_node_idx)
            new_root.add_entry(new_first_node)
            new_root.add_entry(new_second_node)
            self._storage.set_node(0, new_root)
        pass

    def _search_dist(self, point: List[int], dist: int) -> List[LeafEntry]:
        node_queue = deque()
        node_queue.append(self._storage.get_node(0))
        return_list = list()

        while node_queue:
            this_node = node_queue.popleft()
            if not this_node.is_leaf():
                for entry in this_node.entries:
                    if overlaps_distance(point, dist, entry.get_bounding_box()):
                        node_queue.append(self._storage.get_node(entry.child_idx))
            else:
                for entry in this_node.entries:
                    if overlaps_distance(point, dist, entry.get_bounding_box()):
                        return_list.append(entry)
        return return_list

    def search_range(self, search_box: Tuple[list, list]) -> List[Tuple[List, int]]:
        node_queue = deque()
        node_queue.append(self._storage.get_node(0))
        return_list = set()

        # loads from queue until entry on our position is found or not
        while node_queue:
            this_node = node_queue.popleft()

            # if the node is not leaf, adds all child nodes that overlap our position to the queue
            if not this_node.is_leaf():
                for entry in this_node.entries:
                    if overlaps(entry.get_bounding_box(), search_box):
                        node_queue.append(self._storage.get_node(entry.child_idx))
            # if the node is leaf, iterates through the entries and if found, returns the data on our desired position
            else:
                for entry in this_node.entries:
                    if overlaps(entry.get_bounding_box(), search_box):
                        return_list.add(entry)
        ret_list = list()
        for entry in return_list:
            ret_list.append((entry.coord, entry.data_point))
        return ret_list

    def search_knn(self, search_around: List[int], number_of_entries: int) -> List[LeafEntry]:
        root_node = self._storage.get_node(0)
        # bounding box of all entries in the tree
        total_bounding_box = root_node.entries[0].get_bounding_box()
        for x in range(1, len(root_node.entries)):
            total_bounding_box = min_bounding_box(total_bounding_box, root_node.entries[x].get_bounding_box())
        first_coord_distance = 0
        second_coord_distance = 0
        for x in range(len(total_bounding_box[0])):
            first_coord_distance += abs(total_bounding_box[0][x] - search_around[x])
            second_coord_distance += abs(total_bounding_box[1][x] - search_around[x])
        # max distance from point that is worth trying to cover
        max_distance = max(first_coord_distance, second_coord_distance)

        output_list = self._search_dist(search_around, max_distance)
        if len(output_list) <= number_of_entries:
            return output_list

        min_distance = 0
        closest_list = list
        list_init = False
        while len(output_list) != number_of_entries:
            if abs(max_distance - min_distance) <= 1:
                return closest_list # TODO
            new_distance = (min_distance + max_distance) / 2
            output_list = self._search_dist(search_around, new_distance)
            if len(output_list) == number_of_entries:
                return output_list
            if len(output_list) > number_of_entries:
                if not list_init or len(output_list) < len(closest_list):
                    list_init = True
                    closest_list = output_list
                max_distance = new_distance
            if len(output_list) < number_of_entries:
                min_distance = new_distance
