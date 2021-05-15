from typing import List, Tuple
import math
import random
import unittest
from collections import deque
from rtree import RTree, RTreeSplitType
from rtree.storage import Storage


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


class TestCreateInsertSearch(unittest.TestCase):
    def test_create(self):
        self._test_create(1, 128, RTreeSplitType.BRUTE_FORCE)
        self._test_create(2, 512, RTreeSplitType.QUADRATIC)
        self._test_create(3, 1024, RTreeSplitType.LINEAR)
        self._test_create(4, 1024, RTreeSplitType.LINEAR)

    def test_split(self):
        dim = random.randint(1, 5)
        node_size = random.randint(128, 4096)
        tree = TestRTree.create_in_memory(dim, node_size, RTreeSplitType.LINEAR)
        max_entries = tree._storage._max_entries(False)

        for i in range(max_entries + 1):
            tree.insert(self._random_point(dim), i)
            self.assertEqual(tree._storage.count(), 1 if i <= max_entries else 3)

    def test_insert(self):
        dim = random.randint(1, 5)
        tree = self._create_rtree_and_insert(dim, 256, RTreeSplitType.LINEAR, 2183)

        box = ([-1000 for _ in range(dim)], [1000 for _ in range(dim)])

        self.assertEqual(len(tree.search_range(box)), 2183)

    def test_leaks(self):
        dim = random.randint(1, 5)
        tree = self._create_rtree_and_insert(dim, 256, RTreeSplitType.LINEAR, 2000)

        indexes = [0]
        queue = deque()
        queue.append(tree._storage.get_node(0))

        while queue:
            node = queue.popleft()
            if not node.is_leaf():
                for x in node.entries:
                    indexes.append(x.child_idx)
                    queue.append(tree._storage.get_node(x.child_idx))

        for i in range(len(indexes)):
            self.assertIn(i, indexes)

    def test_1d_128_brute_force_200_range(self):
        self._test_range(1, 128, RTreeSplitType.BRUTE_FORCE, 200)

    def test_1d_128_brute_force_200_knn_smaller(self):
        self._test_knn(1, 128, RTreeSplitType.BRUTE_FORCE, 200, 50)

    def test_1d_128_brute_force_200_knn_same(self):
        self._test_knn(1, 128, RTreeSplitType.BRUTE_FORCE, 200, 200)

    def test_1d_128_brute_force_1000_knn_greater(self):
        self._test_knn(1, 128, RTreeSplitType.BRUTE_FORCE, 200, 250)

    def test_2d_128_brute_force_100_range(self):
        self._test_range(2, 128, RTreeSplitType.BRUTE_FORCE, 100)

    def test_2d_128_brute_force_100_knn_smaller(self):
        self._test_knn(2, 128, RTreeSplitType.BRUTE_FORCE, 100, 20)

    def test_2d_128_brute_force_100_knn_same(self):
        self._test_knn(2, 128, RTreeSplitType.BRUTE_FORCE, 100, 100)

    def test_2d_128_brute_force_100_knn_greater(self):
        self._test_knn(2, 128, RTreeSplitType.BRUTE_FORCE, 100, 120)

    def test_2d_128_quadratic_100_range(self):
        self._test_range(2, 128, RTreeSplitType.QUADRATIC, 100)

    def test_2d_128_quadratic_100_knn_smaller(self):
        self._test_knn(2, 128, RTreeSplitType.QUADRATIC, 100, 20)

    def test_2d_128_quadratic_100_knn_same(self):
        self._test_knn(2, 128, RTreeSplitType.QUADRATIC, 100, 100)

    def test_2d_128_quadratic_100_knn_greater(self):
        self._test_knn(2, 128, RTreeSplitType.QUADRATIC, 100, 120)

    def test_2d_128_linear_100_range(self):
        self._test_range(2, 128, RTreeSplitType.LINEAR, 100)

    def test_2d_128_linear_100_knn_smaller(self):
        self._test_knn(2, 128, RTreeSplitType.LINEAR, 100, 20)

    def test_2d_128_linear_100_knn_same(self):
        self._test_knn(2, 128, RTreeSplitType.LINEAR, 100, 100)

    def test_2d_128_linear_100_knn_greater(self):
        self._test_knn(2, 128, RTreeSplitType.LINEAR, 100, 120)

    def test_2d_512_quadratic_1000_range(self):
        self._test_range(2, 512, RTreeSplitType.QUADRATIC, 1000)

    def test_2d_512_quadratic_1000_knn(self):
        self._test_knn(2, 512, RTreeSplitType.QUADRATIC, 1000, 50)

    def test_3d_512_quadratic_1000_range(self):
        self._test_range(3, 512, RTreeSplitType.QUADRATIC, 1000)

    def test_3d_512_quadratic_1000_knn(self):
        self._test_knn(3, 512, RTreeSplitType.QUADRATIC, 1000, 50)

    def test_4d_512_linear_1000_range(self):
        self._test_range(4, 512, RTreeSplitType.LINEAR, 1000)

    def test_4d_512_linear_1000_knn(self):
        self._test_knn(4, 512, RTreeSplitType.LINEAR, 1000, 50)

    def _test_create(self, dim: int, node_size: int, split_type: RTreeSplitType):
        tree = TestRTree.create_in_memory(dim, node_size, split_type)
        self.assertEqual(tree.get_dimensions(), dim)
        self.assertEqual(tree._storage.get_node_size(), node_size)
        self.assertEqual(tree._storage.get_split_type(), split_type)
        self.assertEqual(tree._storage.count(), 1)

    def _test_range(self, dim: int, node_size: int, split_type: RTreeSplitType, n: int):
        tree = self._create_rtree_and_insert(dim, node_size, split_type, n)

        box = self._random_box(dim)

        seq_res = tree.seq_search_range(box)
        res = tree.search_range(box)

        self._assert_range(seq_res, res)

    def _test_knn(self, dim: int, node_size: int, split_type: RTreeSplitType, n: int, k: int):
        tree = self._create_rtree_and_insert(dim, node_size, split_type, n)

        point = self._random_point(dim)

        seq_res = tree.seq_search_knn(point, k)
        res = tree.search_knn(point, k)

        self._assert_knn(seq_res, res, min(k, n))

    def _assert_range(self, seq_res: list, res: list):
        self.assertEqual(len(seq_res), len(res))

        for x in seq_res:
            self.assertTrue(x in res)

    def _assert_knn(self, seq_res: list, res: list, k: int):
        self.assertEqual(len(res), k)

        for x in res:
            self.assertTrue(x in seq_res)

    def _random_point(self, dim: int) -> List[int]:
        return [random.randint(-1000, 1000) for _ in range(dim)]

    def _random_box(self, dim: int) -> Tuple[List[int], List[int]]:
        a = self._random_point(dim)
        b = self._random_point(dim)

        p = []
        q = []

        for i in range(dim):
            p.append(min(a[i], b[i]))
            q.append(max(a[i], b[i]))

        return p, q

    def _create_rtree_and_insert(self, dim: int, node_size: int, split_type: RTreeSplitType, n: int) -> TestRTree:
        tree = TestRTree.create_in_memory(dim, node_size, split_type)
        for i in range(n):
            tree.insert(self._random_point(dim), i)
        return tree


if __name__ == "__main__":
    unittest.main()
