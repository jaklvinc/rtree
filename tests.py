from typing import List, Tuple
import math
import random
from rtree import RTree, RTreeSplitType
from rtree.storage import Storage
from visualization import Visualizer


class TestRTree(RTree):
    def __init__(self, storage: Storage):
        super().__init__(storage)
        self._seq_data = []

    def insert(self, indices: List[int], data: int):
        super().insert(indices, data)
        self._seq_data.append((indices, data))

    def seq_search_range(self, search_box: Tuple[list, list]) -> List[Tuple[List[int], int]]:
        result = []
        for x in self._seq_data:
            if self._is_inside(x[0], search_box):
                result.append(x)

        return result

    # Can return more than k points, if the last points are the same distance
    def seq_search_knn(self, point: List[int], k: int) -> List[Tuple[List[int], int]]:
        queue = []

        for x in self._seq_data:
            dist = self._dist(point, x[0])
            inserted = False
            for i, y in enumerate(queue):
                if y[0] > dist:
                    queue.insert(i, (dist, x))
                    inserted = True
                    break
            if not inserted:
                queue.append((dist, x))

            if len(queue) > k:
                if not math.isclose(queue[-1][0], queue[-2][0]):
                    queue.pop()

        return [x for _, x in queue]

    def _is_inside(self, point: List[int], box: Tuple[List[int], List[int]]) -> bool:
        for x in range(len(point)):
            if point[x] > box[1][x] or point[x] < box[0][x]:
                return False
        return True

    def _dist(self, p: List[int], q: List[int]) -> float:
        return math.dist(p, q)


if __name__ == "__main__":
    tree = TestRTree.create_in_memory(2, 128, RTreeSplitType.QUADRATIC)

    for i in range(100):
        tree.insert([random.randint(-100, 100), random.randint(-100, 100)], i)

    Visualizer.visualize(tree)

    print(tree.seq_search_range(([-10, -10], [11, 5])))
    print(tree.seq_search_knn([0, 0], 5))
