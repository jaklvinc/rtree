class Node:
    def __init__(self, first_idx : tuple() ):
        self._first_idx=first_idx

class LeafNode(Node):
    def __init__(self, first_idx: tuple(), data: int):
        super().__init__(first_idx)
        self._data=data



class NonLeafNode(Node):
    def __init__(self, first_idx: tuple(), second_idx: tuple(), child_node : int ):
        super().__init__(first_idx, second_idx)
        self._second_idx=second_idx
        self._child_node=child_node
