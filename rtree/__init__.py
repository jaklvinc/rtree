from enum import Enum
from rtree.storage import RTreeStorage
from rtree.node import Entry, Node
from queue import Queue


class RTreeSplitType(Enum):
    TYPE1 = 1,
    TYPE2 = 2,
    TYPE3 = 3


class RTree:
    def __init__(self, storage: RTreeStorage):
        self._storage = storage
    
    def _split_node(self):
        pass
    
    def _add_to_node(self, node : Node ):
        pass
    
    def insert(self, idx : tuple() , data : int ):
        root_node=self._storage.get_node(0)
        new_entry=Entry(first_pos = idx, data = data )

        if ( root_node.is_leaf() ):
            if ( not root_node.is_full() ):
                pass
        else:
            pass

    def find(self , search_pos : tuple() , node_idx : int = 0 ) -> int :
        node_queue = Queue(0)
        node_queue.put(self._storage.get_node(node_idx))

        #loads from queue until entry on our position is found or not
        while(not node_queue.empty()):
            this_node = node_queue.get()

            #if the node is not leaf, adds all child nodes that overlap our position to the queue
            if ( not this_node.is_leaf() ):
                for entry in this_node.entries:
                    is_in = True
                    for x in range(entry.get_first_pos().count()):
                        if (    ( entry.get_first_pos()[x] > search_pos[x]) 
                            or ( entry.get_second_pos()[x] < search_pos[x]) ):
                            is_in = False
                    if ( is_in ):
                        node_queue.put(self._storage.get_node(this_node.get_child_idx()))
            # if the node is leaf, iterates through the entries and if found, returns the data on our desired position
            else:
                for entry in this_node.entries:
                    if ( entry.get_first_pos() == search_pos ):
                        return entry.get_data()
        return -1

    def find_in_range(self):
        pass