import time
import random
import math
import os
import plotly.graph_objects as go
from typing import Tuple, List, Any
from rtree import RTree, RTreeSplitType


def time_fn(fn: callable, *args) -> Tuple[float, Any]:
    start = time.perf_counter()
    value = fn(*args)
    end = time.perf_counter()
    return (end - start), value


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


def insert_search_time(dim: int, size: int, split_type: RTreeSplitType, data: List[Tuple[List[int], int]],
                       boxes: List[Tuple[List[int], List[int]]], knn: List[Tuple[List[int], int]],
                       i_y: List[float], s_r_y: List[float], s_k_y: List[float]):
    tree = RTree.create_in_memory( dim, size, split_type)
    i_t, _ = time_fn(insert_data, tree, data)
    i_y.append(i_t)

    s_r_t = 0
    for box in boxes:
        t, _ = time_fn(tree.search_range, box)
        s_r_t += t
    s_r_y.append(s_r_t)

    s_k_t = 0
    for p, k in knn:
        t, _ = time_fn(tree.search_knn, p, k)
        s_k_t += t
    s_k_y.append(s_k_t)


def insert_search_fig(x: List[int], bf: List[float], q: List[float], l: List[float], x_title: str, y_title: str) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=bf, name='Brute force split'))
    fig.add_trace(go.Scatter(x=x, y=q, name='Quadratic split'))
    fig.add_trace(go.Scatter(x=x, y=l, name='Linear split'))
    fig.update_layout(
        xaxis_title=x_title,
        yaxis_title=y_title,
    )
    fig.update_yaxes(tick0=0, dtick=0.5)
    return fig


def seq_search_fig(x: List[int], seq_y: List[float], tree_y: List[float], y_title: str):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=seq_y, name='Normal search'))
    fig.add_trace(go.Scatter(x=x, y=tree_y, name='R-tree search'))
    fig.update_layout(
        xaxis_title='Number of data points',
        yaxis_title=y_title,
    )
    fig.update_xaxes(tick0=100, dtick=100)
    return fig


def experiment_insert_search_node_size():
    data = random_data(2, 1000)
    boxes = [random_box(2) for _ in range(200)]
    knn = [(random_point(2), random.randint(5, 60)) for _ in range(20)]

    x = []
    bf_i_y = []
    q_i_y = []
    l_i_y = []

    bf_s_r_y = []
    q_s_r_y = []
    l_s_r_y = []

    bf_s_k_y = []
    q_s_k_y = []
    l_s_k_y = []

    for size in range(128, 4097, 32):
        if size > 256 and size % 128 != 0:
            continue

        x.append(size)

        if size <= 256:
            insert_search_time(2, size, RTreeSplitType.BRUTE_FORCE, data, boxes, knn, bf_i_y, bf_s_r_y, bf_s_k_y)

        insert_search_time(2, size, RTreeSplitType.QUADRATIC, data, boxes, knn, q_i_y, q_s_r_y, q_s_k_y)
        insert_search_time(2, size, RTreeSplitType.LINEAR, data, boxes, knn, l_i_y, l_s_r_y, l_s_k_y)
        print('  size {} B done'.format(size))

    fig = insert_search_fig(x, bf_i_y, q_i_y, l_i_y, 'Node size [byte]', 'Time to insert 1000 data points [s]')
    fig.update_xaxes(tick0=128, dtick=128)
    fig.write_html('./experiments/insert_node_size.html', auto_open=True)

    fig = insert_search_fig(x, bf_s_r_y, q_s_r_y, l_s_r_y, 'Node size [byte]', 'Time to do range search 200 times [s]')
    fig.update_xaxes(tick0=128, dtick=128)
    fig.update_yaxes(tick0=0, dtick=0.05)
    fig.write_html('./experiments/search_range_node_size.html', auto_open=True)

    fig = insert_search_fig(x, bf_s_k_y, q_s_k_y, l_s_k_y, 'Node size [byte]', 'Time to do knn search 20 times [s]')
    fig.update_xaxes(tick0=128, dtick=128)
    fig.update_yaxes(tick0=0, dtick=0.1)
    fig.write_html('./experiments/search_knn_node_size.html', auto_open=True)


def experiment_insert_search_dimension():
    data = random_data(10, 1000)
    boxes = [random_box(10) for _ in range(200)]
    knn = [(random_point(10), random.randint(5, 60)) for _ in range(20)]

    x = []
    bf_i_y = []
    q_i_y = []
    l_i_y = []

    bf_s_r_y = []
    q_s_r_y = []
    l_s_r_y = []

    bf_s_k_y = []
    q_s_k_y = []
    l_s_k_y = []

    for dim in range(1, 11):
        x.append(dim)

        data_dim = [([x[i] for i in range(dim)], d) for x, d in data]
        boxes_dim = [([x[i] for i in range(dim)], [y[i] for i in range(dim)]) for x, y in boxes]
        knn_dim = [([x[i] for i in range(dim)], k) for x, k in knn]

        insert_search_time(2, 256, RTreeSplitType.BRUTE_FORCE, data_dim, boxes_dim, knn_dim, bf_i_y, bf_s_r_y, bf_s_k_y)
        insert_search_time(2, 256, RTreeSplitType.QUADRATIC, data_dim, boxes_dim, knn_dim, q_i_y, q_s_r_y, q_s_k_y)
        insert_search_time(2, 256, RTreeSplitType.LINEAR, data_dim, boxes_dim, knn_dim, l_i_y, l_s_r_y, l_s_k_y)
        print('  dim {} done'.format(dim))

    fig = insert_search_fig(x, bf_i_y, q_i_y, l_i_y, 'Dimension', 'Time to insert 1000 data points [s]')
    fig.update_xaxes(tick0=1, dtick=1)
    fig.update_yaxes(tick0=0.5, dtick=1)
    fig.write_html('./experiments/insert_dimension.html', auto_open=True)

    fig = insert_search_fig(x, bf_s_r_y, q_s_r_y, l_s_r_y, 'Dimension', 'Time to do range search 200 times [s]')
    fig.update_xaxes(tick0=1, dtick=1)
    fig.update_yaxes(tick0=0, dtick=0.05)
    fig.write_html('./experiments/search_range_dimension.html', auto_open=True)

    fig = insert_search_fig(x, bf_s_k_y, q_s_k_y, l_s_k_y, 'Dimension', 'Time to do knn search 20 times [s]')
    fig.update_xaxes(tick0=1, dtick=1)
    fig.update_yaxes(tick0=0, dtick=0.5)
    fig.write_html('./experiments/search_knn_dimension.html', auto_open=True)


def experiment_seq_search_data_len():
    tree = RTree.create_in_memory(2, 128, RTreeSplitType.QUADRATIC)
    boxes = [random_box(2) for _ in range(200)]

    x = []

    seq_y = []
    tree_y = []

    for i in range(20):
        insert_data(tree, random_data(2, 100))

        x.append(i * 100 + 100)

        seq_sum = 0
        tree_sum = 0
        for box in boxes:
            seq_time, _ = time_fn(seq_search_range, tree, box)
            tree_time, _ = time_fn(tree.search_range, box)

            seq_sum += seq_time
            tree_sum += tree_time
        seq_y.append(seq_sum)
        tree_y.append(tree_sum)
        print('  {} data points done'.format(i * 100 + 100))

    fig = seq_search_fig(x, seq_y, tree_y, 'Time to do range search 200 times [s]')
    fig.update_yaxes(tick0=0, dtick=0.5)
    fig.write_html('./experiments/seq_search_data_len.html', auto_open=True)


def main():
    if not os.path.isdir('./experiments'):
        os.mkdir('./experiments')

    experiments = [
        (experiment_insert_search_node_size, './experiments/insert_node_size.html, ./experiments/search_range_node_size.html, ./experiments/search_knn_node_size.html'),
        (experiment_insert_search_dimension, './experiments/insert_dimension.html, ./experiments/search_range_dimension.html, ./experiments/search_knn_dimension.html'),
        (experiment_seq_search_data_len, './experiments/seq_search_data_len.html'),
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
