from abc import abstractclassmethod

class Entry:
    def __init__(self,first_idx : tuple() , second_idx : tuple() , child_idx : int ) -> None :
        self._first_idx=first_idx
        self._second_idx=second_idx
        self._child_idx=child_idx
    
    def __init__(self,first_idx : tuple() , data : int) -> None:
        self._first_idx=first_idx
        self._data=data


class Node:
    def __init__(self, is_leaf : bool , max_size : int ):
        self._is_leaf = is_leaf
        self._max_size = max_size

        self._entries = list(Entry)
    
    def is_leaf(self) -> bool:
        return self._is_leaf
    
    def add_entry(self, entry : Entry ) -> bool:
        if ( self._entries.count() < self._max_size ):
            self._entries.append(entry)
        #TODO
        pass
