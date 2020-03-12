import math
import logging

import numpy


logger = logging.getLogger(__name__)

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
DEATH = 1000.0
LEGAL_THRESHOLD = DEATH * 0.9
HILLTOP = -50 # Value for all points from which to propagate hills
DANGER = 10.0
FOOD = -5.0 # Value for all points from which to propogate wells
FORCED_DECISION = -100.0 # For when you really want the snake to choose a particular direction
DECAYFACTOR_A = 1.0
DECAYFACTOR_B = 0.4


def decay_function(a, b, x):
    '''Exponential decay f(x) = a(1-b)^x'''
    return a*(1-b)**x


def get_coord_direction(start, end):
    '''Given two points, find the coordinate direction from start to end

    Params:
    start -- (x, y) coordinates of start point
    end -- (x, y) coordinates of end point

    Returns: One of (0,1), (1,0), (0,-1), (-1,0)
    '''
    ex, ey = end
    px, py = start
    dx = ex - px
    dir_x = 0
    if dx != 0:
        dir_x = 1 if dx > 0 else -1
    dy = ey - py
    dir_y = 0
    if dy != 0:
        dir_y = 1 if dy > 0 else -1
    direction = (dir_x, dir_y)
    if direction not in DIR_DICT:
        logger.warning(
            "Calculated non-cardinal direction between coordinates %s and %s", start, end)
    return direction


def next_coord_in_direction(start, direction):
    '''Given a starting point, output coordinates after moving in direction'''
    x, y = start
    dx, dy = MOVE_DICT[direction]
    return (x+dx, y+dy)


def enclosed_area(loop):
    '''Calculates area enclosed by a loop defined by a list of coordinates

    Given a boundary (x1, y1), (x2, y2), ..., (xn, yn)
    area = |(x1*y2 - x2*y1) + (x2*y3 - x3*y2) + ... + (xn*y1 - x1*yn)| / 2

    Parameters:
    loop -- list of (x, y) coordinates defining boundary of loop
    '''
    px, py = loop[0]
    area = 0
    for x, y in loop[1:]:
        area += (px*y - x*py)
        px = x
        py = y
    hx, hy = loop[0]
    area += (x*hy - hx*y)
    return math.ceil(abs(area / 2))


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
        self.logger = logging.getLogger(type(self).__name__)
        self.dimensions = (width, height)
        self._position_grid = numpy.full(self.dimensions, DEFAULT)


    def update_attributes(self, **kwargs):
        '''Set arbitrary attributes with this function
        
        Known attributes:
        body -- List of (x, y) coordinates of player body segments (head to tail)
        snakes -- List of (x, y) coordinates of opponent snakes
        foods -- List of (x, y) coordinates of food
        '''
        REQUIRED = ['body', 'snakes', 'foods']
        missing = [key for key in REQUIRED if key not in kwargs]
        if missing:
            self.logger.warning("Calling update_attributes without required attributes: %s", missing)
        for key in kwargs:
            setattr(self, key, kwargs[key])


    def update_heatmap(self):
        '''Update heatmap of risks/rewards'''
        # Reset array to non-zero default value
        self._position_grid = numpy.full(self.dimensions, DEFAULT)
        # Mark positions of food
        for x, y in self.foods:
            self._position_grid[x][y] = FOOD
        # Propogate hilltops
        self.hilltops = [snake[0] for snake in self.snakes]
        for x, y in self.hilltops:
            self._position_grid[x][y] = HILLTOP
        # Propogate hills and wells
        self._find_hills_wells()


    def update_obstacles(self):
        # Mark snake bodies as obstacles (tails are special)
        obstacles = self.body[:-1]
        for snake in self.snakes:
            obstacles.extend(snake[:-1])
        for x, y in obstacles:
            self._position_grid[x][y] = DEATH
        for snake in self.snakes:
            # Enemy snake tails are dangerous if enemy snake head is in proximity of food
            hx, hy = snake[0]
            danger_zone = [
                (hx-1,hy),
                (hx+1,hy),
                (hx,hy-1),
                (hx,hy+1)
            ]
            tx, ty = snake[-1]
            if ([coord for coord in self.foods if coord in danger_zone]
                and self._position_grid[tx][ty] < DANGER):
                self._position_grid[tx][ty] = DANGER


    def _find_hills_wells(self):
        '''
        Find points to centre hills and wells at then calls propogate hills and wells accordingly
        '''
        # propogate wells
        for x, y in self.foods:
            self._propagate_wells(x, y)
        # propogate hills last to "override" food
        for x, y in self.hilltops:
            self._propagate_hills(x, y)
        # Invert hilltops
        self._invert_hilltops()


    def _propagate_hills(self, hillx, hilly):
        '''
        Add to danger value of each point based on distance from hilltop
        hillx - the x coordinate of the hilltop
        hilly - the y coordinate of the hilltop
        '''
        x_len, y_len = self.dimensions
        for x in range(x_len):
            for y in range(y_len):
                distance = math.sqrt((hillx - x)**2 + (hilly - y)**2)
                self._position_grid[x][y] += decay_function(abs(HILLTOP), DECAYFACTOR_B, distance)

   
    def _propagate_wells(self, wellx, welly):
        '''
        Subtract from danger value of each point based on distance from well.

        Parameters:
        wellx -- x coordinate of well centre
        welly -- y coordinate of well centre
        '''
        x_len, y_len = self.dimensions
        for x in range(x_len):
            for y in range(y_len):
                distance = math.sqrt((wellx - x)**2 + (welly - y)**2)
                self._position_grid[x][y] -= decay_function(abs(FOOD), DECAYFACTOR_B, distance)


    def _invert_hilltops(self):
        '''Flip values of all HILLTOPS from negative to positive'''
        for x, y in self.hilltops:
            self._position_grid[x][y] = abs(self._position_grid[x][y])
        

    def rank_moves(self):
        '''Returns a ranked list of all legal moves in order of safety rating'''
        legal_moves = []
        hx, hy = self.body[0]
        for move, (dx, dy) in MOVE_DICT.items():
            if self.move_is_legal(move):
                legal_moves.append((
                    self._position_grid[hx+dx][hy+dy],
                    move
                ))
        legal_moves.sort()
        self.logger.debug("Legal moves (in order of preference): %s", legal_moves)
        return [move for _, move in legal_moves]


    def arena_to_str(self):
        '''Debugging function that generates a plaintext representation of the current arena state'''
        x_len, y_len = self.dimensions
        grid_str = ''
        for y in range(y_len):
            for x in range(x_len):
                grid_str += "{} ".format(str(self._position_grid[x][y])[:4].ljust(4,' '))
                if x == x_len - 1:
                    grid_str += '\n\n'
        return grid_str


    def move_is_legal(self, move):
        '''Checks if move is legal (not certain death)

        Parameters:
        move -- one of UP, DN, LT, RT
        '''
        # Prevent running into walls
        if self._run_into_wall(move):
            return False
        # If moving toward food, mark tail as certain death
        dx, dy = MOVE_DICT[move]
        hx, hy = self.body[0]
        nx = hx+dx
        ny = hy+dy
        if (nx, ny) in self.foods:
            tx, ty = self.body[-1]
            self._position_grid[tx][ty] = DEATH
        
        return self._position_grid[nx][ny] < LEGAL_THRESHOLD


    def get_head_direction(self):
        '''Checks current direction snake is travelling'''
        hx, hy = self.body[0]
        try:
            px, py = [seg for seg in self.body if seg != (hx, hy)][0]
            return DIR_DICT[(hx-px, hy-py)]
        except IndexError:
            self.logger.debug("Snake body is all in one place, default to 'up' direction")
            return UP


    def _run_into_wall(self, move):
        '''Checks if move will result in collision with arena boundaries

        Parameters:
        move -- one of UP, DN, LT, RT
        '''
        dx, dy = MOVE_DICT[move]
        hx, hy = self.body[0]
        nx = hx+dx
        ny = hy+dy
        return (not self._within_bounds((nx, ny)))


    def _within_bounds(self, coords):
        '''Checks if coordinates are within arena boundaries

        Parameters:
        coords: (x, y) coordinates of position of interest
        '''
        x, y = coords
        x_lim, y_lim = self.dimensions
        return (x >= 0 and x < x_lim and y >= 0 and y < y_lim)

    
    def _on_walls(self, segment):
        '''Checks how many arena boundaries body segment is adjacent to

        Parameters:
        segment -- (x, y) coordinates of body segment
        '''
        x, y = segment
        x_lim, y_lim = self.dimensions
        walls = 0
        if x == 0: walls += 1
        if x == x_lim-1: walls += 1
        if y == 0: walls += 1
        if y == y_lim-1: walls += 1
        return walls


    def handle_area_choices(self):
        '''Performs search algorithm in each legal direction to check if
        there is enough area to fit the snake in each direction'''
        area_direction = []
        for direction in self.rank_moves():
            area = self._reachable_area(direction)
            area_direction.append((area, direction))
        self.logger.debug("Areas in directions: %s", area_direction)
        area_direction.sort(reverse=True)
        for i, (area, direction) in enumerate(area_direction):
            if area < len(self.body):
                x, y = next_coord_in_direction(self.body[0], direction)
                self._position_grid[x][y] = DANGER + 2*i


    def _reachable_area(self, direction):
        '''Finds reachable play area in direction of head

        Parameters:
        direction -- one of UP DN LT RT
        '''
        reached = numpy.full(self.dimensions, False)
        head = self.body[0]
        hx, hy = head
        reached[hx][hy] = True
        next_pos = next_coord_in_direction(head, direction)
        return self._reachable_area_helper(next_pos, reached, 1)


    def _reachable_area_helper(self, here, reached, step):
        '''Finds reachable play area starting from here

        Parameters:
        here -- (x, y) coordinates of landing point
        reached -- numpy array of already reached points on arena
        step -- moves in the future it will take to reach here
        '''
        # Out of bounds, stop
        if not self._within_bounds(here):
            return 0
        # Location seen before, stop
        x, y = here
        seen = reached[x][y]
        if seen:
            return 0
        # Mark location as seen
        reached[x][y] = True
        # Reached definite obstacle, stop
        step += 1
        if not self._predict_future(step)[x][y] < LEGAL_THRESHOLD:
            return 0
        # Otherwise, increment area and search
        area = 1
        for dx, dy in MOVE_DICT.values():
            next_pos = (x+dx, y+dy)
            area += self._reachable_area_helper(next_pos, reached, step)
        return area


    def _predict_future(self, step):
        '''Returns copy of position_grid with danger zones
        removed from snake bodies for steps into the future'''
        now_safe = self.body[-step:]
        for snake in self.snakes:
            now_safe.extend(snake[-step:])
        new_grid = numpy.copy(self._position_grid)
        for x, y in now_safe:
            new_grid[x][y] = DEFAULT
        return new_grid
