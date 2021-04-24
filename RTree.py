
class Index:
    def __init__(self,data):
        self.container = data
        self.child = None

class Node:
    def __init__(self,M):
        self.M = M
        self.storedData = list(Index)
    
    def Add(self,data = tuple()):
        idx = Index(data)
        if ( self.storedData.count() < self.M ):
            self.storedData.append(idx)
        else:
            for index in self.storedData:
                pass



class Tree:
    def __init__(self,dim,insertType,M = 4):
        self.dim = dim
        self.insType = insertType
        self.m = M
        self.root = None
    
    def Insert(self,toAdd = tuple()):
        if ( toAdd.count() != self.dim ):
            return False
            
        node = Node(self.m)
        if ( self.root == None ):
            self.root=node
        self.root.Add(toAdd)



        

