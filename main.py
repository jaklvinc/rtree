from rtree import RTree, RTreeSplitType


def main():
    tree = RTree.create_in_memory(2, 1024, RTreeSplitType.BRUTE_FORCE)
    tree.insert([1, 1], 1)
    tree.insert([2, 2], 2)


if __name__ == "__main__":
    main()
