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


def pick_next(entries_left: Queue, first_bounding_rect: Tuple[list, list], second_bounding_rect: Tuple[list, list]) -> LeafEntry:
    max_dif_size = -1
    max_dif_entry = entries_left.get()
    for i in range(entries_left.qsize()):
        check_entry = entries_left.get()
        first_dif = two_box_area(check_entry.get_bounding_box(), first_bounding_rect) - \
            bounding_box_area(first_bounding_rect)
        second_dif = two_box_area(check_entry.get_bounding_box(), second_bounding_rect) - \
            bounding_box_area(second_bounding_rect)
        dif = abs(first_dif - second_dif)
        if dif > max_dif_size:
            max_dif_size = dif
            entries_left.put(max_dif_entry)
            max_dif_entry = check_entry
    return max_dif_entry


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

    def _quadratic_split(self, split_this: Node) -> Tuple[Node, Node]:
        max_area = -1
        max_area_pair = Tuple[LeafEntry, LeafEntry]
        for pair in combinations(split_this.entries, 2):
            bounding_box = min_bounding_box(pair[0].get_bounding_box(), pair[1].get_bounding_box())
            box_area = bounding_box_area(bounding_box)
            if box_area > max_area:
                max_area = box_area
                max_area_pair = (pair[0], pair[1])

        entries_left = Queue(0)
        for entry in split_this.entries:
            if entry != max_area_pair[0] and entry != max_area_pair[1]:
                entries_left.put(entry)

        first_node_bounding_rect = (max_area_pair[0].coord,max_area_pair[0].coord)
        first_node = Node(is_leaf=True, max_size=self._storage.get_node_size())
        first_node.add_entry(max_area_pair[0])

        second_node_bounding_rect = (max_area_pair[1].coord, max_area_pair[1].coord)
        second_node = Node(is_leaf=True, max_size=self._storage.get_node_size())
        second_node.add_entry(max_area_pair[1])

        while not entries_left.empty():
            add_now = pick_next(entries_left, first_node_bounding_rect, second_node_bounding_rect)
            first_node_new_rect = min_bounding_box(add_now.get_bounding_box(), first_node_bounding_rect)
            second_node_new_rect = min_bounding_box(add_now.get_bounding_box(), second_node_bounding_rect)

            first_node_dif = bounding_box_area(first_node_new_rect)-bounding_box_area(first_node_bounding_rect)
            second_node_dif = bounding_box_area(second_node_new_rect)-bounding_box_area(second_node_bounding_rect)

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

        return first_node, second_node
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

    def _search_dist(self, point: List[int], dist: int) -> List[LeafEntry]:
        node_queue = Queue(0)
        node_queue.put(self._storage.get_node(0))
        return_list = list()

        while not node_queue.empty():
            this_node = node_queue.get()
            if not this_node.is_leaf():
                for entry in this_node.entries:
                    if overlaps_distance(point, dist, entry.get_bounding_box()):
                        node_queue.put(self._storage.get_node(this_node.get_child_idx()))
            else:
                for entry in this_node.entries:
                    if overlaps_distance(point, dist, entry.get_bounding_box()):
                        return_list.append(entry)
        return return_list

    def search_range(self, search_box: Tuple[list, list]) -> List[LeafEntry]:
        node_queue = Queue(0)
        node_queue.put(self._storage.get_node(0))
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

    def search_n_around(self, search_around: List[int], number_of_entries: int) -> List[LeafEntry]:
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
                return closest_list[:number_of_entries]
            new_distance = (min_distance + max_distance) / 2
            output_list = self._search_dist(search_around, new_distance)
            if len(output_list) == number_of_entries:
                return output_list
            if len(output_list) > number_of_entries:
                if len(output_list) < len(closest_list) or not list_init:
                    list_init = True
                    closest_list = output_list
                max_distance = new_distance
            if len(output_list) < number_of_entries:
                min_distance = new_distance
