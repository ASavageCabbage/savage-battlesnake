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
TURN_TO_DIRECTION = {
    (UP, CCW): LT,
    (LT, CCW): DN,
    (DN, CCW): RT,
    (RT, CCW): UP,
    (UP, CW): RT,
    (RT, CW): DN,
    (DN, CW): LT,
    (LT, CW): UP
}


# tweakable parameters
DEFAULT = 1.0
DEATH = 50.0
HILLTOP = -DEATH # Value for all points from which to propagate hills
DANGER = 10.0
FOOD = -5.0 # Value for all points from which to propogate wells
FORCED_DECISION = -20.0 # For when you really want the snake to choose a particular direction
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
        # Prevent running into walls
        if self.run_into_wall(move):
            return False
        # If moving toward food, mark tail as certain death
        dx, dy = MOVE_DICT[move]
        hx, hy = self.body[0]
        nx = hx+dx
        ny = hy+dy
        if (nx, ny) in self.foods:
            tx, ty = self.body[-1]
            self._position_grid[tx][ty] = DEATH
        
        return self._position_grid[nx][ny] < DEATH

    
    def check_self_loop(self):
        '''
        Checks if snake is about to loop in on itself
        For now, encourages turning away from self-loops with FORCED_DECISION
        '''
        curr_dir = self.check_direction()
        hx, hy = self.body[0]
        fx, fy = MOVE_DICT[curr_dir]
        # Check three blocks perpendicular to head
        if fx == 0:
            # Direction is up/down
            # Check for empty squares left/right
            lt_clear = (hx-1, hy) not in self.body
            rt_clear = (hx+1, hy) not in self.body
            ahead = [(hx, hy+fy)]
            # Extend danger zone left/right if potential loop
            if lt_clear:
                ahead.append((hx-1, hy+fy))
            if rt_clear:
                ahead.append((hx+1, hy+fy))
        else:
            # Direction is left/right
            # Check for empty squares up/down
            up_clear = (hx, hy-1) not in self.body
            dn_clear = (hx, hy+1) not in self.body
            ahead = [(hx+fx, hy)]
            if up_clear:
                ahead.append((hx+fx, hy-1))
            if dn_clear:
                ahead.append((hx+fx, hy+1))
        ahead_segs = [pos for pos in self.body if pos in ahead]
        # In the case of a self-loop...
        if ahead_segs:
            print "Potential self-loop detected!"
            # Use segment closest to head as marker
            ahead_seg = ahead_segs[0]
            # Calculate chirality of loop
            turn_state = self.turn_state(ahead_seg)
            turn_away = CW if turn_state > 0 else CCW
            dx, dy = MOVE_DICT[TURN_TO_DIRECTION[(curr_dir, turn_away)]]
            # If outward turn is legal, reward outward turn
            nx = hx+dx
            ny = hy+dy
            if self.within_bounds((nx, ny)):
                next_pos_value = self._position_grid[nx][ny]
                if next_pos_value < DEATH:
                    self._position_grid[nx][ny] = FORCED_DECISION


    def check_direction(self):
        '''Checks current direction snake is travelling'''
        hx, hy = self.body[0]
        try:
            px, py = [seg for seg in self.body if seg != (hx, hy)][0]
            return DIR_DICT[(hx-px, hy-py)]
        except IndexError:
            print "Snake body is all in one place, default to 'up' direction"
            return UP


    def turn_state(self, stop):
        '''Check degree of turns from head to specified body segment

        Parameters:
        stop -- (x, y) coordinates of body segment at which to end calculation
        '''
        directions = []
        prev = self.body[0]
        for seg in self.body:
            if seg == prev:
                continue
            x, y = seg
            px, py = prev
            dx = x - px
            dy = y - py
            # Insert at front of list for proper order
            directions.insert(0, DIR_DICT[(dx, dy)])
            if seg == stop:
                break
            prev = seg
        # Transform direction list from [a, b, c, ...]
        # to turns corresponding to [(a, b), (b, c), ...]
        turns = []
        prev = directions[0]
        for direction in directions:
            if direction == prev:
                continue
            turns.append(TURN_DICT[(prev, direction)])
            prev = direction
        return sum(turns)


    def within_bounds(self, coords):
        '''Checks if coordinates are within arena boundaries

        Parameters:
        coords: (x, y) coordinates of position of interest
        '''
        x, y = coords
        x_lim, y_lim = self.dimensions
        return (x >= 0 and x < x_lim and y >= 0 and y < y_lim)


    def run_into_wall(self, move):
        '''Checks if move will result in collision with arena boundaries

        Parameters:
        move -- one of UP, DN, LT, RT
        '''
        dx, dy = MOVE_DICT[move]
        hx, hy = self.body[0]
        nx = hx+dx
        ny = hy+dy
        width, height = self.dimensions
        return (nx < 0 or ny < 0 or nx >= width or ny >= height)

    
    def on_walls(self, segment):
        '''Checks how many arena boundaries body segment is adjacent to

        Parameters:
        segment -- (x, y) coordinates of body segment
        '''
        x, y = segment
        x_lim, y_lim = self.dimensions
        walls = 0
        if x == 1: walls += 1
        if x == x_lim-1: walls += 1
        if y == 1: walls += 1
        if y == y_lim-1: walls += 1
        return walls


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