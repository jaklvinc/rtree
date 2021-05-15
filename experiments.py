import time
import random
import math
import os
import plotly.graph_objects as go
from typing import Tuple, List, Any
from rtree import RTree, RTreeSplitType
from rtree.node import Node
from rtree.storage import Storage, DiskStorage
from visualization import Visualizer


class StorageStatsDecorator(Storage):
    def __init__(self, storage: Storage):
        self._storage = storage
        self._get_counter = 0
        self._set_counter = 0
        self._add_counter = 0

    def stats_reset_get(self):
        self._get_counter = 0

    def stats_reset_set(self):
        self._set_counter = 0

    def stats_reset_add(self):
        self._add_counter = 0

    def stats_count_get(self) -> int:
        return self._get_counter

    def stats_count_set(self) -> int:
        return self._set_counter

    def stats_count_add(self) -> int:
        return self._add_counter

    def get_dim(self) -> int:
        return self._storage.get_dim()

    def get_node_size(self) -> int:
        return self._storage.get_node_size()

    def get_split_type(self) -> RTreeSplitType:
        return self._storage.get_split_type()

    def count(self) -> int:
        return self._storage.count()

    def get_node(self, index: int) -> Node:
        self._get_counter += 1
        return self._storage.get_node(index)

    def set_node(self, index: int, node: Node):
        self._set_counter += 1
        return self._storage.set_node(index, node)

    def add_node(self, node: Node) -> int:
        self._add_counter += 1
        return self._storage.add_node(node)


class StatsDiskStorage(DiskStorage):
    def __init__(self, filename: str):
        super().__init__(filename)
        self._write_counter = 0
        self._read_counter = 0

    def stats_reset_write(self):
        self._write_counter = 0

    def stats_reset_read(self):
        self._read_counter = 0

    def stats_count_write(self) -> int:
        return self._write_counter

    def stats_count_read(self) -> int:
        return self._read_counter


def time_fn(fn: callable, *args) -> Tuple[float, Any]:
    start = time.perf_counter_ns()
    value = fn(*args)
    end = time.perf_counter_ns()
    return (end - start) / 1000000000, value


def random_point(dim: int) -> List[int]:
    return [random.randint(-1000, 1000) for _ in range(dim)]


def random_data(dim: int, n: int) -> List[Tuple[List[int], int]]:
    return [(random_point(dim), i) for i in range(n)]


def random_box(dim: int) -> Tuple[List[int], List[int]]:
    a = random_point(dim)
    b = random_point(dim)

    p = []
    q = []

    for i in range(dim):
        p.append(min(a[i], b[i]))
        q.append(max(a[i], b[i]))

    return p, q


def random_box_with_side_len(dim: int, side_len: int) -> Tuple[List[int], List[int]]:
    a = random_point(dim)

    p_l = math.floor(side_len / 2)
    q_l = math.ceil(side_len / 2)

    return [x - p_l for x in a], [x + q_l for x in a]


def insert_data(tree: RTree, data: List[Tuple[List[int], int]]):
    for x in data:
        tree.insert(x[0], x[1])


def is_inside(point: List[int], box: Tuple[List[int], List[int]]) -> bool:
    for x in range(len(point)):
        if point[x] > box[1][x] or point[x] < box[0][x]:
            return False
    return True


def distance(p: List[int], q: List[int]) -> float:
    return math.dist(p, q)


def seq_search_range(tree: RTree, search_box: Tuple[list, list]) -> List[Tuple[List[int], int]]:
    result = []

    for i in range(tree._storage.count()):
        node = tree._storage.get_node(i)
        if node.is_leaf():
            for x in node.entries:
                if is_inside(x.coord, search_box):
                    result.append((x.coord, x.data_point))

    return result


def seq_search_knn(tree: RTree, point: List[int], k: int) -> List[Tuple[List[int], int]]:
    queue = []

    for i in range(tree._storage.count()):
        node = tree._storage.get_node(i)
        if not node.is_leaf():
            continue

        for x in node.entries:
            dist = distance(point, x.coord)
            inserted = False
            for i, y in enumerate(queue):
                if y[0] > dist:
                    queue.insert(i, (dist, (x.coord, x.data_point)))
                    inserted = True
                    break
            if not inserted:
                queue.append((dist, (x.coord, x.data_point)))

            if len(queue) > k:
                if not math.isclose(queue[-1][0], queue[-2][0]):
                    queue.pop()

    return [x for _, x in queue]


def insert_search_time(size: int, split_type: RTreeSplitType, data: List[Tuple[List[int], int]], boxes: List[Tuple[List[int], List[int]]], i_y: List[float], s_y: List[float]):
    tree = RTree.create_in_file('./experiments/tmp.rtree', 2, size, split_type)
    i_t, _ = time_fn(insert_data, tree, data)
    i_y.append(i_t)

    s_t = 0
    for box in boxes:
        s, _ = time_fn(tree.search_range, box)
        s_t += s
    s_y.append(s_t)

    print(size, split_type.to_str())


def insert_search_node_size_fig(x: List[int], bf: List[float], q: List[float], l: List[float], y_title: str) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=bf, name='Brute force split'))
    fig.add_trace(go.Scatter(x=x, y=q, name='Quadratic split'))
    fig.add_trace(go.Scatter(x=x, y=l, name='Linear split'))
    fig.update_layout(
        xaxis_title='Node size [byte]',
        yaxis_title=y_title,
    )
    fig.update_xaxes(tick0=128, dtick=128)
    fig.update_yaxes(tick0=0, dtick=0.5)
    return fig


def experiment_insert_search_node_size():
    data = random_data(2, 1000)
    boxes = [random_box(2) for _ in range(200)]

    x = []
    bf_i_y = []
    q_i_y = []
    l_i_y = []

    bf_s_y = []
    q_s_y = []
    l_s_y = []

    for size in range(128, 4097, 32):
        if size > 256 and size % 128 != 0:
            continue

        x.append(size)

        if size <= 256:
            insert_search_time(size, RTreeSplitType.BRUTE_FORCE, data, boxes, bf_i_y, bf_s_y)

        insert_search_time(size, RTreeSplitType.QUADRATIC, data, boxes, q_i_y, q_s_y)
        insert_search_time(size, RTreeSplitType.LINEAR, data, boxes, l_i_y, l_s_y)

    os.remove('./experiments/tmp.rtree')

    fig_i = insert_search_node_size_fig(x, bf_i_y, q_i_y, l_i_y, 'Time to insert 1000 data points [s]')
    fig_i.write_html('./experiments/insert_node_size.html', auto_open=True)

    fig_s = insert_search_node_size_fig(x, bf_s_y, q_s_y, l_s_y, 'Time to do range search 200 times [s]')
    fig_s.write_html('./experiments/search_node_size.html', auto_open=True)


def experiment_seq():
    tree = RTree.create_in_memory(2, 128, RTreeSplitType.QUADRATIC)
    insert_data(tree, random_data(2, 1000))

    x = []
    seq_y = []
    tree_y = []

    for i in range(50):
        x.append(math.pow(i+1, 2))
        seq_sum = 0
        tree_sum = 0

        for _ in range(100):
            box = random_box_with_side_len(2, i+1)

            seq_time, _ = time_fn(seq_search_range, tree, box)
            t_time, _ = time_fn(tree.search_range, box)

            seq_sum += seq_time
            tree_sum += t_time

        seq_y.append(seq_sum)
        tree_y.append(tree_sum)

    print("SEQ: ", seq_y)
    print("TREE:", tree_y)


def main():
    if not os.path.isdir('./experiments'):
        os.mkdir('./experiments')

    experiments = [
        (experiment_insert_search_node_size, './experiments/insert_node_size.html, ./experiments/search_node_size.html')
    ]

    print('Generate:')
    for i, (_, s) in enumerate(experiments):
        print('  [{}] {}'.format(i, s))
    print()

    while True:
        i_str = input('Select experiment or type \'exit\': ')

        if i_str.lower() == 'exit':
            break

        try:
            i = int(i_str)
            if i < 0 or i >= len(experiments):
                continue

            print('Generating {}...'.format(i))
            experiments[i][0]()
            print('Done')
        except ValueError:
            continue


if __name__ == "__main__":
    main()
