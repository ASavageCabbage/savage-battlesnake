import math
import numpy


# CONSTANTS
UP = 'up'
DN = 'down'
LT = 'left'
RT = 'right'

MOVE_DICT = {
    UP: (0, -1),
    DN: (0, 1),
    LT: (-1, 0),
    RT: (1, 0)
}
DIR_DICT = {val: key for key, val in MOVE_DICT.items()}

CCW = 1
CW = -1
TURN_DICT = {
    (UP, UP): 0,
    (DN, DN): 0,
    (LT, LT): 0,
    (RT, RT): 0,
    (UP, LT): CCW,
    (LT, DN): CCW,
    (DN, RT): CCW,
    (RT, UP): CCW,
    (UP, RT): CW,
    (RT, DN): CW,
    (DN, LT): CW,
    (LT, UP): CW
}


# tweakable parameters
DEFAULT = 1.0
DEATH = 50.0
HILLTOP = -DEATH # Value for all points from which to propagate hills
DANGER = 10.0
FOOD = -5.0 # Value for all points from which to propogate wells
DECAYFACTOR_A = 1.0
DECAYFACTOR_B = 0.4


class Arena(object):
    '''
    Definition of play arena
    '''
    def __init__(self, width, height):
        '''Boot 'er up!

        Parameters:
        width -- width of arena (positive integer)
        height -- height of arena (positive integer)
        '''
        self.dimensions = (width, height)
        self.turn_state = 0
        self.directions = []
    

    def update_turn(self, body):
        '''Update turn state and direction of snake

        Parameters:
        body -- List of (x, y) coordinates of player body segments (head to tail)
        '''
        head, prev = body[0:2]
        diff = (head[0]-prev[0], head[1]-prev[1])
        self.directions.append(DIR_DICT[diff])
        turn = tuple(self.directions[-2:])
        self.turn_state += TURN_DICT[turn]


    def update_heatmap(self, body, snakes, foods):
        '''Update heatmap of risks/rewards

        Parameters:
        body -- List of (x, y) coordinates of player body segments (head to tail)
        snakes -- List of (x, y) coordinates of opponent snakes
        foods -- List of (x, y) coordinates of food
        '''
        # Initialize array to non-zero default value (1)
        self._position_grid = numpy.full(self.dimensions, DEFAULT)
        # Initialize player body
        self.body = body
        # Mark positions of food
        self.foods = foods
        for x, y in self.foods:
            self._position_grid[x][y] = FOOD
        # Mark danger zones around opponent heads and tails
        ends = [(snake[0], snake[-1]) for snake in snakes]
        self.hilltops = []
        for hd, tl in ends:
            hx, hy = hd
            self._position_grid[hx][hy] = HILLTOP
            self.hilltops.append((hx, hy))
            danger_zone = [
                (hx-1,hy),
                (hx+1,hy),
                (hx,hy-1),
                (hx,hy+1)
            ]
            # Enemy snake tails are dangerous if enemy snake in proximity of food
            tx, ty = tl
            if ([coord for coord in self.foods if coord in danger_zone]
                and self._position_grid[tx][ty] < DANGER):
                self._position_grid[tx][ty] = DANGER
        # Propogate hills and wells
        self.find_hills_wells()
        # Mark snake bodies as obstacles (tails are special)
        obstacles = body[:-1]
        for snake in snakes:
            obstacles.extend(snake[:-1])
        for x, y in obstacles:
            self._position_grid[x][y] = DEATH


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
        move -- one of UP, DN, LT, RT
        '''
        dx, dy = MOVE_DICT[move]
        hx, hy = self.body[0]
        nx = hx+dx
        ny = hy+dy
        # Prevent running into walls
        width = self._position_grid.shape[0]
        height = self._position_grid.shape[1]
        if nx < 0 or ny < 0 or nx >= width or ny >= height:
            return False
        # If moving toward food, mark tail as certain death
        if (nx, ny) in self.foods:
            tx, ty = self.body[-1]
            self._position_grid[tx][ty] = DEATH
        return self._position_grid[nx][ny] < DEATH


    def rank_moves(self):
        '''Returns a ranked list of all legal moves in order of safety rating'''
        legal_moves = []
        hx, hy = self.body[0]
        for move, (dx, dy) in MOVE_DICT.items():
            if self.check_move(move):
                legal_moves.append((
                    self._position_grid[hx+dx][hy+dy],
                    move
                ))
        legal_moves.sort()
        print "Legal moves (in order of preference): {}".format(legal_moves)
        return [move for _, move in legal_moves]


    def print_arena(self):
        '''Debugging function that generates a plaintext representation of the current arena state'''
        x_len, y_len = self.dimensions
        grid_str = "ARENA HEATMAP:\n"
        for y in range(y_len):
            for x in range(x_len):
                grid_str += "{} ".format(str(self._position_grid[x][y])[:4].ljust(4,' '))
                if x == x_len - 1:
                    grid_str += '\n\n'
        print grid_str