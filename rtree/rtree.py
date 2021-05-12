import itertools
from itertools import combinations
from queue import Queue
from .split_type import RTreeSplitType
from .storage import RTreeStorage
from .node import Entry, Node


class RTree:
    def __init__(self, storage: RTreeStorage):
        self._storage = storage

    def _count_area( first : Entry , second : Entry ) -> int:
        first_coords=list()
        second_coords=list()
        for x in range(first.get_first_pos().count()):
            first_coords.append(min(first.get_first_pos()[x],second.get_first_pos()[x]))
            second_coords.append(max(first.get_second_pos()[x],second.get_second_pos()[x]))
        sizes=( abs(x-y)+1 for x in first_coords for y in second_coords )
        area=1
        for size in sizes:
            area*=size
        return area

    def _choose_leaf(self, node_idx : int , pos : tuple(int) ) -> Node:
        node_queue = Queue(0)
        node_queue.put(node_idx)

        while ( not node_queue.empty() ):
            this_node_idx=node_queue.get()
            node = self._storage.get_node(this_node_idx)
            node.set_idx(this_node_idx)
            if ( node.is_leaf() ):
                return node
            else:
                min_enlarge = float('inf')
                min_entry = Entry
                for entry in node.entries:
                    enlarge_count = 0
                    #Checks how much the Node would enlargen, if the new item would be added to this node
                    for x in range(entry.get_first_pos().count()):
                        enlarge_count+=self._add_if_bigger(entry.get_first_pos()[x],pos[x])
                        enlarge_count+=self._add_if_bigger(pos[x],entry.get_second_pos()[x])

                    if ( enlarge_count < min_enlarge ):
                        min_enlarge=enlarge_count
                        min_entry=entry

                    #for better size optimalization, if the hypothetical enlargements are the same, chooses the smaller area,
                    # so that the tree is balanced better
                    elif ( enlarge_count == min_enlarge ):
                        this_size=0
                        last_min_size=0
                        for x in range(entry.get_first_pos().count()):
                            this_size+=(entry.get_second_pos()[x]-entry.get_first_pos[x])
                            last_min_size+=(min_entry.get_second_pos()[x]-min_entry.get_first_pos()[x])
                        if ( this_size < last_min_size ):
                            min_enlarge=enlarge_count
                            min_entry=entry
                node_queue.put(min_entry.get_child_idx())

    def _brute_force_split(self, split_this : Node ):
        #TODO
        pass

    def _quadratic_split(self, split_this : Node ):
        max_area = float('inf')
        max_area_pair = 0
        for pair in combinations(split_this.entries,2):
            area=self._count_area(pair[0],pair[1])
        #TODO

    def _linear_split(self, split_this : Node ):
        pass

    def _split_node( self, split_this : Node , insert_node : RTreeSplitType ):
        if ( insert_node == RTreeSplitType.BRUTE_FORCE ):
            self._brute_force_split(split_this)
        elif( insert_node == RTreeSplitType.QUADRATIC ):
            self._quadratic_split(split_this)
        elif( insert_node == RTreeSplitType.LINEAR ):
            self._linear_split(split_this)
        pass

    def insert(self, idx : tuple(int) , data : int ):
        to_insert = Entry(first_pos=idx,data=data)
        insert_node=self._choose_leaf( 0 , idx )
        if ( insert_node.add_entry( to_insert ) ):
            self._storage.set_node(insert_node.get_idx(),insert_node)
        else:
            self._split_node(insert_node,self._storage.get_split_type())
        #TODO

    def find(self , search_pos : tuple(int) , node_idx : int = 0 ) -> int :
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
        #TODO
        pass