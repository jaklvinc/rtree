from abc import abstractclassmethod


class Entry:
    '''Class that stores both leaf and non-leaf entries
    
    For leaf entry, fill @first_pos=@second_pos and @data. \\
    For non-leaf entry, fill @first_pos, @second_pos and @child_idx.
    '''
    def __init__(self,first_pos : tuple() , second_pos : tuple() , child_idx : int = -1 , data : int = -1 ) -> None :
        self._first_pos=first_pos
        self._second_pos=second_pos
        self._child_idx=child_idx
        self._data=data
    
    def get_data(self) -> int :
        return self._data
    
    def get_child_idx(self) -> int:
        return self._child_idx
    
    def get_first_pos(self) -> tuple() :
        return self._first_pos
    
    def get_second_pos(self) -> tuple() :
        return self._second_pos

'''

@parent is a pair of parent_node and index of parent_entry in that node
'''
class Node:
    def __init__(self, is_leaf : bool , max_size : int , parent : tuple(int) ):
        self._is_leaf = is_leaf
        self._max_size = max_size
        self._mem_idx = -1
        self._parent_entry = parent

        self.entries = list(Entry)
    
    def get_parent_entry(self) -> tuple(int):
        return self._parent_entry
    
    def set_idx(self,  mem_idx : int ) -> None:
        self._mem_idx=mem_idx
        pass
    
    def get_idx(self) -> int:
        return self._mem_idx
    
    def is_leaf(self) -> bool:
        return self._is_leaf
    
    def is_full(self) -> bool:
        return (self._entries.count() == self._max_size )
    
    def add_entry(self, entry: Entry) -> bool:
        if ( self.entries.count() == self._max_size ):
            return False
        else:
            self.entries.append(entry)
            return True
