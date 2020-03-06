import numpy
import math

# Should probably move these into a separate config file
# or make them static class attributes
DEATH = 50
HILLTOP = -DEATH # Value for all points from which to propagate hills
DANGER = 10
FOOD = -5 # Value for all points from which to propogate wells
DECAYFACTOR_A = 1
DECAYFACTOR_B = 0.4
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

        # ====== SET TOPS OF HILLS AND WELLS =====
        # Mark positions of food
        self.foods = [(food['x'], food['y']) for food in kwargs.get('foods', [])]
        for fx, fy in self.foods:
            self._position_grid[fx][fy] = FOOD
        # Mark danger zones around opponent heads and tails
        ends = kwargs.get('ends', [])
        self.hilltops = []
        for hd, tl in ends:
            hx = hd['x']
            hy = hd['y']
            self._position_grid[hx][hy] = HILLTOP
            self.hilltops.append((hx, hy))
            tx = tl['x']
            ty = tl['y']
            danger_zone = [
                (hx-1,hy),
                (hx+1,hy),
                (hx,hy-1),
                (hx,hy+1)
            ]
            # Enemy snake tails are dangerous if enemy snake in proximity of food
            if ([coord for coord in self.foods if coord in danger_zone]
                and self._position_grid[tx][ty] < DANGER):
                self._position_grid[tx][ty] = DANGER
        self.find_hills_wells()
        # Mark obstacles (certain death zones)
        obstacles = kwargs.get('obstacles', [])
        for obs in obstacles:
            self._position_grid[obs['x']][obs['y']] = DEATH


    def find_hills_wells(self):
        '''
        Find points to centre hills and wells at then calls propogate hills and wells accordingly
        '''
        # Iterate over arena
        x_len, y_len = self.dimensions
        # propogate wells
        for x, y in self.foods:
            self.propagate_wells(x, y)
        # propogate hills last to "override" food
        for x, y in self.hilltops:
            self.propagate_hills(x, y)
        # Invert hilltops
        self.invert_hilltops()


    def propagate_hills(self, hillx, hilly):
        '''
        Add to danger value of each point based on distance from hilltop
        hillx - the x coordinate of the hilltop
        hilly - the y coordinate of the hilltop
        '''
        x_len, y_len = self.dimensions
        for x in range(x_len):
            for y in range(y_len):
                value = self._position_grid[x][y]
                if value == HILLTOP:
                    continue
                distance = math.sqrt((hillx - x)**2 + (hilly - y)**2)
                self._position_grid[x][y] += self.decay_function(abs(HILLTOP), DECAYFACTOR_B, distance)

   
    def propagate_wells(self, wellx, welly):
        '''
        Subtract from danger value of each point based on distance from well.
        wellx - x coordinate of well centre
        welly - y coordinate of well centre
        '''
        x_len, y_len = self.dimensions
        for x in range(x_len):
            for y in range(y_len):
                value = self._position_grid[x][y]
                if value in [HILLTOP, FOOD]:
                    continue
                distance = math.sqrt((wellx - x)**2 + (welly - y)**2)
                self._position_grid[x][y] -= self.decay_function(abs(FOOD), DECAYFACTOR_B, distance)


    def invert_hilltops(self):
        '''Flip values of all HILLTOPS from negative to positive'''
        for x, y in self.hilltops:
            self._position_grid[x][y] = abs(self._position_grid[x][y])


    def decay_function(self, a, b, x):
        # Exponential decay f(x) = a(1-b)^x
        return a*(1-b)**x


    def check_move(self, move):
        '''Checks if move is legal (not certain death)

        Parameters:
        move -- one of 'up', 'down', 'left', 'right'
        '''
        dx, dy = MOVE_DICT[move]
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
        print legal_moves
        return [move for _, move in legal_moves]


    def print_arena(self):
        '''Debugging function that generates a plaintext representation of the current arena state'''
        x_len, y_len = self.dimensions
        grid_str = ""
        for y in range(y_len):
            for x in range(x_len):
                grid_str += "{}, ".format(str(self._position_grid[x][y])[:4].ljust(4,' '))
                if x == x_len - 1:
                    grid_str += '\n'
        print grid_str