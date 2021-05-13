import plotly.graph_objects as go
from typing import List
from collections import deque
from rtree import RTree, RTreeSplitType
from rtree.node import Node, NonLeafEntry, LeafEntry
import random


class Visualizer:
    @classmethod
    def visualize(cls, tree: RTree):
        dim = tree._storage.get_dim()

        if dim < 1 or dim > 3:
            raise AttributeError

        if tree._storage.count() <= 0:
            return

        queue = deque()
        queue.append(tree._storage.get_node(0))

        data = [[] for _ in range(dim)]
        fig = go.Figure()

        while queue:
            node = queue.popleft()
            if node.is_leaf():
                for le in node.entries:
                    for i, x in enumerate(le.coord):
                        data[i].append(x)
            else:
                for nle in node.entries:
                    queue.append(tree._storage.get_node(nle.child_idx))
                    box = cls._box(nle.first_coord, nle.second_coord, dim)
                    box.name = 'Node {}'.format(nle.child_idx)
                    fig.add_trace(box)
        fig.add_trace(cls._data(data, dim))
        fig.show()

    @classmethod
    def _box(cls, p1: List[int], p2: List[int], dim: int):
        if dim == 1:
            return cls._box1d(p1, p2)
        if dim == 2:
            return cls._box2d(p1, p2)
        return cls._box3d(p1, p2)

    @classmethod
    def _data(cls, data: List[List[int]], dim: int):
        if dim == 1:
            return go.Scatter(x=data[0], y=[0 for _ in data[0]], name='Data', mode='markers')
        if dim == 2:
            return go.Scatter(x=data[0], y=data[1], name='Data', mode='markers')
        return go.Scatter3d(x=data[0], y=data[1], z=data[2], name='Data', mode='markers')

    @classmethod
    def _box1d(cls, p1: List[int], p2: List[int]) -> go.Scatter:
        return go.Scatter(x=[p1[0], p2[0]], y=[0, 0], mode='lines')

    @classmethod
    def _box2d(cls, p1: List[int], p2: List[int]) -> go.Scatter:
        x = []
        y = []

        p_x = [p1[0], p2[0]]
        p_y = [p1[1], p2[1]]

        x_path = [0, 1, 1, 0, 0]
        y_path = [0, 0, 1, 1, 0]

        for i in range(len(x_path)):
            x.append(p_x[x_path[i]])
            y.append(p_y[y_path[i]])

        return go.Scatter(x=x, y=y, mode='lines')

    @classmethod
    def _box3d(cls, p1: List[int], p2: List[int]) -> go.Scatter3d:
        x = []
        y = []
        z = []

        p_x = [p1[0], p2[0]]
        p_y = [p1[1], p2[1]]
        p_z = [p1[2], p2[2]]

        x_path = [0, 1, 1, 0, 0, 0, 1, 1, 0, 0, None, 1, 1, None, 1, 1, None, 0, 0]
        y_path = [0, 0, 1, 1, 0, 0, 0, 1, 1, 0, None, 0, 0, None, 1, 1, None, 1, 1]
        z_path = [0, 0, 0, 0, 0, 1, 1, 1, 1, 1, None, 0, 1, None, 0, 1, None, 0, 1]

        for i in range(len(x_path)):
            if x_path[i] is None:
                x.append(None)
            else:
                x.append(p_x[x_path[i]])

            if y_path[i] is None:
                y.append(None)
            else:
                y.append(p_y[y_path[i]])

            if z_path[i] is None:
                z.append(None)
            else:
                z.append(p_z[z_path[i]])

        return go.Scatter3d(x=x, y=y, z=z, mode='lines')


if __name__ == "__main__":
    '''tree = RTree.create_in_memory(2, 1024, RTreeSplitType.BRUTE_FORCE)

    root = Node(False, 10, (0, 0))
    node1 = Node(True, 10, (0, 0))
    node2 = Node(True, 10, (0, 0))
    root.entries = [NonLeafEntry([0, 0], [1, 1], 1), NonLeafEntry([2, 0], [3, 2], 2)]
    node1.entries = [LeafEntry([0, 1], 0), LeafEntry([1, 0], 1)]
    node2.entries = [LeafEntry([2, 1], 2), LeafEntry([3, 1], 3)]

    tree._storage.set_node(0, root)
    tree._storage.add_node(node1)
    tree._storage.add_node(node2)

    Visualizer.visualize(tree)

    '''
    tree = RTree.create_in_memory(2, 1024, RTreeSplitType.QUADRATIC)

    number_of_entries = 1

    first_coord = [random.randint(0, 100) for x in range(number_of_entries)]
    second_coord = [random.randint(0, 100) for x in range(number_of_entries)]
    for x, y, z in zip(first_coord, second_coord, range(number_of_entries)):
        tree.insert([x, y], z)

    Visualizer.visualize(tree)
