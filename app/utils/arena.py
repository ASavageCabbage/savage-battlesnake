import numpy
import math

# Should probably move these into a separate config file
# or make them static class attributes
FOODMAPVALS = [0, 3, 2, 1]
DEATH = 10
HILLTOP = -10 # Value for all points from which to propagate hills
DANGER = 1
FOOD = -1 # Value for all points from which to propogate wells
DECAYFACTOR = 0.5
MOVE_DICT = {
    'up': (0, -1),
    'down': (0, 1),
    'left': (-1, 0),
    'right': (1, 0)
}
class Arena(object):
    '''
    Definition of play arena with location of obstacles
    Contains methods to check basic validity of proposed next moves
    '''
    def __init__(self, width, height, **kwargs):
        '''Boot 'er up!

        Parameters:
        width -- width of arena (positive integer)
        height -- height of arena (positive integer)

        Optional Keyword Arguments:
        player_h -- {'x':x, 'y':y} coordinates of player head
        player_t -- {'x':x, 'y':y} coordinates of player tail
        obstacles -- List of {'x':x, 'y':y} coordinates of obstacles
        ends -- List of {'x':x, 'y':y} coordinates of opponent ends (head, tail)
        foods -- List of {'x':x, 'y':y} coordinates of food
        '''
        # Initialize array to non-zero default value (1)
        self._position_grid = numpy.ones((width, height))
        self.dimensions = self._position_grid.shape
        # Initialize player head and tail
        self.head = kwargs.get('player_h', {'x':0, 'y':0})
        self.tail = kwargs.get('player_t', {'x':0, 'y':0})
        # Mark positions of food
        self.foods = kwargs.get('foods', [])
        for food in self.foods:
            self._position_grid[food['x']][food['y']] = FOOD
        # Mark obstacles (certain death zones)
        obstacles = kwargs.get('obstacles', [])
        for obs in obstacles:
            self._position_grid[obs['x']][obs['y']] = DEATH
        # Mark danger zones around opponent heads and tails
        ends = kwargs.get('ends', [])
        for hd, tl in ends:
            # Squares around head are dangerous
            hx = hd['x']
            hy = hd['y']
            self._position_grid[hx][hy] = HILLTOP
            # Pretty sure danger zone stuff is unnecessary now but deleting is scary
            # That's why we comment out instead :)
            # danger_zone = [
            #     (hx-1,hy),
            #     (hx+1,hy),
            #     (hx,hy-1),
            #     (hx,hy+1)
            # ]
            # for x, y in danger_zone:
            #     if self._position_grid[x][y] < DANGER:
            #         self._position_grid[x][y] = DANGER
            # Tail could grow if head is in reach of any food
            # Should tail be treated like head?
            # NO, tail is unlike a head (cannot change directions), should not be hilltop
            # tx = tl['x']
            # ty = tl['y']
            # self._position_grid[tx][ty] = HILLTOP

            if ([coord for coord in self.foods if coord in danger_zone]
                and self._position_grid[tx][ty] < DANGER):
                self._position_grid[tx][ty] = DANGER

            self.find_hills_wells()

    def find_hills_wells(self):
        '''
        Find points to centre hills and wells at then calls propogate hills and wells accordingly
        '''
        # Iterate over arena
        x_len, y_len = self.dimensions
        for x in range(x_len):
            for y in range(y_len):
                # If current grid point is hilltop set it to death and create hill centred on it
                if self._position_grid[x][y] == HILLTOP:
                    self._position_grid[x][y] = DEATH
                    self.propagate_hills(x, y)
                # If current point is well then propagate well on that point.
                elif self._position_grid[x][y] == FOOD:
                    self.propagate_wells(x, y)

    def propagate_hills(self, hillx, hilly):
        '''
        Add to danger value of each point based on distance from hilltop
        hillx - the x coordinate of the hilltop
        hilly - the y coordinate of the hilltop
        '''
        x_len, y_len = self.dimensions
        for x in range(x_len):
            for y in range(y_len):
                # calculate current point's distance from hilltop
                # note that the Pythagorean Theorem still holds
                # even if one of the legs of the triangle is zero length ;)
                distance = math.sqrt((hillx - x)**2 + (hilly - y)**2)
                self._position_grid[x][y] += self.decay_function(distance)
    
   
    def propagate_wells(self, wellx, welly):
        # There may be a good way to combine the propogate functions
        # I think keeping them separate is important philosophically, though
        '''
        Subtract from danger value of each point based on distance from well.
        wellx - x coordinate of well centre
        welly - y coordinate of well centre
        '''
        x_len, y_len = self.dimensions
        for x in range(x_len):
            for y in range(y_len):
                # need to round to nearest integer to use the FOODMAPVALS array
                # note that this performs a flooring operation. If you want to round,
                # use the 'round' function
                distance = int(round(math.sqrt((wellx - x)**2 + (welly - y)**2)))
                self._position_grid[x][y] -= FOODMAPVALS[distance]


    def decay_function(self, x):
        # Exponential decay f(x) = (1-a)^x
        return DEATH*(1-DECAYFACTOR)**x

    def check_move(self, move):
        '''Checks if move is legal (not certain death)

        Parameters:
        move -- one of 'up', 'down', 'left', 'right'
        '''
        dx = MOVE_DICT[move][0]
        dy = MOVE_DICT[move][1]
        hx = self.head['x']
        hy = self.head['y']
        new_pos = (hx+dx, hy+dy)
        # Prevent running into walls
        width = self._position_grid.shape[0]
        height = self._position_grid.shape[1]
        if new_pos[0] < 0 or new_pos[1] < 0 or new_pos[0] >= width or new_pos[1] >= height:
            return False
        # If moving toward food, mark tail as certain death
        if new_pos in self.foods:
            self._position_grid[self.tail['x']][self.tail['y']] = DEATH
        return self._position_grid[new_pos[0]][new_pos[1]] < DEATH

    # Hey, this still works in the new paradigm! FORWARD THINKING
    def rank_moves(self):
        '''Returns a ranked list of all legal moves in order of safety rating
        
        Returns: [(<safety>, <move string>), ...]
        '''
        legal_moves = []
        hx = self.head['x']
        hy = self.head['y']
        for move, (dx, dy) in MOVE_DICT.items():
            new_pos = (hx+dx, hy+dy)
            if self.check_move(move):
                legal_moves.append((
                    self._position_grid[new_pos[0]][new_pos[1]],
                    move
                ))
        legal_moves.sort()
        return legal_moves

    def print_arena():
        '''Debugging function that generates a plaintext representation of the current arena state'''
        # LMAO numpy already has a function for this
        print numpy.array_str(self._position_grid)
