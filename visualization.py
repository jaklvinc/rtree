import plotly.graph_objects as go
from typing import List
from collections import deque
from rtree import RTree


class Visualizer:
    @classmethod
    def visualize(cls, tree: RTree, html: bool = False):
        dim = tree._storage.get_dim()

        if dim < 1 or dim > 3:
            raise AttributeError

        if tree._storage.count() <= 0:
            return

        queue = deque()
        queue.append((0, tree._storage.get_node(0)))

        data = [[] for _ in range(dim)]
        fig = go.Figure()

        while queue:
            i, node = queue.popleft()
            if node.is_leaf():
                for le in node.entries:
                    for i, x in enumerate(le.coord):
                        data[i].append(x)
            else:
                for nle in node.entries:
                    queue.append((nle.child_idx, tree._storage.get_node(nle.child_idx)))
                    box = cls._box(nle.first_coord, nle.second_coord, dim)
                    box.name = 'R{}(parent R{})'.format(nle.child_idx, i)
                    fig.add_trace(box)
        fig.add_trace(cls._data(data, dim))

        if html:
            fig.write_html("./vis.html", auto_open=True)
        else:
            fig.show()

    @classmethod
    def _box(cls, p: List[int], q: List[int], dim: int):
        if dim == 1:
            return cls._box1d(p, q)
        if dim == 2:
            return cls._box2d(p, q)
        return cls._box3d(p, q)

    @classmethod
    def _data(cls, data: List[List[int]], dim: int):
        if dim == 1:
            return go.Scatter(x=data[0], y=[0 for _ in data[0]], name='Data', mode='markers', marker={'color': '#000000'})
        if dim == 2:
            return go.Scatter(x=data[0], y=data[1], name='Data', mode='markers', marker={'size': 5, 'color': '#000000'})
        return go.Scatter3d(x=data[0], y=data[1], z=data[2], name='Data', mode='markers', marker={'size': 3, 'color': '#000000'})

    @classmethod
    def _box1d(cls, p: List[int], q: List[int]) -> go.Scatter:
        return go.Scatter(x=[p[0], q[0]], y=[0, 0], mode='lines')

    @classmethod
    def _box2d(cls, p: List[int], q: List[int]) -> go.Scatter:
        x = []
        y = []

        p_x = [p[0], q[0]]
        p_y = [p[1], q[1]]

        x_path = [0, 1, 1, 0, 0]
        y_path = [0, 0, 1, 1, 0]

        for i in range(len(x_path)):
            x.append(p_x[x_path[i]])
            y.append(p_y[y_path[i]])

        return go.Scatter(x=x, y=y, mode='lines')

    @classmethod
    def _box3d(cls, p: List[int], q: List[int]) -> go.Scatter3d:
        x = []
        y = []
        z = []

        p_x = [p[0], q[0]]
        p_y = [p[1], q[1]]
        p_z = [p[2], q[2]]

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
