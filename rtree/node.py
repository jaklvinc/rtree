from abc import abstractclassmethod


class Entry:
    '''Class that stores both leaf and non-leaf entries
    
    For leaf entry, fill @first_pos and @data. \\
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


class Node:
    def __init__(self, is_leaf : bool , max_size : int ):
        self._is_leaf = is_leaf
        self._max_size = max_size

        self.entries = list(Entry)
    
    def is_leaf(self) -> bool:
        return self._is_leaf
    
    def is_full(self) -> bool:
        return (self._entries.count() == self._max_size )
    
    def add_entry(self, entry: Entry) -> None:
        
        pass
