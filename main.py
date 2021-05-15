from rtree import RTree, RTreeSplitType
from control_panel import ControlPanel


def main():
    tree = RTree.create_in_memory(2, 1024, RTreeSplitType.BRUTE_FORCE)
    tree.insert([1, 1], 1)
    tree.insert([2, 2], 2)

    try:
        panel = ControlPanel('./data')
        panel.run()
    except IOError:
        print('It seems you have file named \'data\' in this directory. Please remove it and run this script again')


if __name__ == "__main__":
    main()
