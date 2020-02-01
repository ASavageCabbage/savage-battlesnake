import numpy

class Hamilton(object):

    def __init__(self, width, height, **kwargs):
        # create a grid that represents all possible edges between nodes.
        allSquares = width*height
        self.hamGrid = numpy.zeros((allSquares, allSquares))
        
        # initialize grid so that all node pairs with edges return 1 and all unconnected nodes return 0.
        for i in self.hamGrid:
            if ((i + 1) < allSquares) and ((i % width) != 0):
                self.hamGrid[i][i + 1] = 1
            if ((i - 1) >= 0) and (((i - 1) % width) != 0)):
                self.hamGrid[i][i - 1] = 1
            if ((i + width) < allSquares):
                self.hamGrid[i][i + width] = 1
            if (i - width) >= 0:
                self.hamGrid[i][i - width] = 1
            
        obstacles = kwargs.get('obstacles', [])

        # ensure that no nodes are adjacent to obstacle nodes.
        for obs in obstacles:
            gridNum = obs['x'] + ((obs['y'] - 1)*width)

            if ((gridNum + 1) < allSquares) and ((gridNum % width) != 0):
                self.hamGrid[gridNum][gridNum + 1] = 0
            if ((gridNum - 1) >= 0) and (((gridNum - 1) % width) != 0)):  
                self.hamGrid[gridNum][gridNum - 1] = 0
            if ((gridNum + width) < allSquares):
                self.hamGrid[gridNum][gridNum + width] = 0
            if (gridNum - width) >= 0:
                self.hamGrid[gridNum][gridNum - width] = 0

        head = kwargs.get('player_h', {'x':0, 'y':0})
        self.startNode = head['x'] + ((head['y'] - 1)*width)

        # allVertices is currently broken. Needs to exclude all numbers of obstacle nodes.
        self.allVertices = range(width*height)

    ''' Check if this vertex is an adjacent vertex  
        of the previously added vertex and is not  
        included in the path earlier '''
    def isSafe(self, v, pos, path):
        # Check if current vertex and last vertex  
        # in path are adjacent  
        if self.hamGrid[ path[pos-1] ][v] == 0:
            return False
        # Check if current vertex not already in path  
        for vertex in path:
            if vertex == v:
                return False
        
        return True

    # A recursive utility function to solve  
    # hamiltonian cycle problem 
    def hamCycleUtil(self, path, pos):

        # base case: if all vertices are  
        # included in the path 
        if pos == self.allVertices:
            # Last vertex must be adjacent to the  
            # first vertex in path to make a cyle 
            if self.graph[path[pos-1]][path[0]] == 1:
                return True
            else:
                return False
        
        # Try different vertices as a next candidate  
        # in Hamiltonian Cycle. We don't try for 0 as  
        # we included 0 as starting point in hamCycle() 
        for v in range(1, self.allVertices):
            if self.isSafe(v, pos, path) == True:
                path[pos] = v

                if self.hamCycleUtil(path, pos +1) == True:
                    return True

                # Remove current vertex if it doesn't  
                # lead to a solution 
                path[pos] = -1
            
        return False

    ''' Let us put vertex 0 as the first vertex  
            in the path. If there is a Hamiltonian Cycle,  
            then the path can be started from any point  
            of the cycle as the graph is undirected '''
    def hamCycle(self):
        path = [-1]*self.allVertices

        path[0] = self.startNode

        # this if statement may be problematic because our snake body theoretically stops us from ever completing a perfect path. Need to exclude danger nodes from consideration.
        if self.hamCycleUtil(path,1) == False:
            print ("Solution does not exist\n")
            return False

        self.printSolution(path)
        return True

    def printSolution(self, path):
        print ("Solution Exists: Following",
                "is one Hamiltonian Cycle")
        for vertex in path:
            print (vertex, end = " ")
        print (path[0], "\n")




        




