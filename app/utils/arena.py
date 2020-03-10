import math
import logging

import matplotlib.path as mplPath
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


def turn_state(segments):
    '''Check overall degree of turns in a section of snake body

    Parameters:
    segments -- list of (x, y) coordinates starting at head
    '''
    if len(segments) < 3:
        return 0
    directions = []
    prev = segments[0]
    for seg in segments[1:]:
        x, y = seg
        px, py = prev
        dx = x - px
        dy = y - py
        # Insert at front of list for proper order
        directions.insert(0, DIR_DICT[(dx, dy)])
        prev = seg
    # Transform direction list from [a, b, c, ...]
    # to turns corresponding to [(a, b), (b, c), ...]
    turns = []
    prev = directions[0]
    for direction in directions[1:]:
        turns.append(TURN_DICT[(prev, direction)])
        prev = direction
    return sum(turns)


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
        self._find_hills_wells()
        # Mark snake bodies as obstacles (tails are special)
        obstacles = body[:-1]
        for snake in snakes:
            obstacles.extend(snake[:-1])
        for x, y in obstacles:
            self._position_grid[x][y] = DEATH
        self.logger.debug("head is at {}".format(self.body[0]))


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
            if self.check_move(move):
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


    def check_move(self, move):
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


    def check_direction(self):
        '''Checks current direction snake is travelling'''
        hx, hy = self.body[0]
        try:
            px, py = [seg for seg in self.body if seg != (hx, hy)][0]
            return DIR_DICT[(hx-px, hy-py)]
        except IndexError:
            self.logger.debug("Snake body is all in one place, default to 'up' direction")
            return UP


    def within_bounds(self, coords):
        '''Checks if coordinates are within arena boundaries

        Parameters:
        coords: (x, y) coordinates of position of interest
        '''
        x, y = coords
        x_lim, y_lim = self.dimensions
        return (x >= 0 and x < x_lim and y >= 0 and y < y_lim)

    
    def handle_self_loop(self):
        '''Checks if snake is about to loop in on itself
        and takes appropriate action
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
            self.logger.debug("Potential self-loop detected!")
            # Use segment closest to head as marker
            ahead_seg = ahead_segs[0]
            end_idx = self.body.index(ahead_seg)
            body_loop = ahead_seg[:(end_idx + 1)]
            # Make decision based on loop areas
            self._handle_loop_decision(body_loop)


    def handle_wall_loop(self):
        '''
        Checks if snake is about to form a loop with a wall
        and takes appropriate action
        '''
        # NOTE: The smallest possible loop (1 square in corner) requires 3 body segments
        self.logger.debug("{}".format(self.dimensions))
        width, height = self.dimensions
        curr_dir = self.check_direction()
        is_on_wall = [bool(self._on_walls(seg)) for seg in self.body]
        if self._run_into_wall(curr_dir) and any(is_on_wall[2:])):
            self.logger.debug("Wall Loop Detected!")
            # Get section of body forming loop with wall
            # May need to stop after first body segment touching wall. Otherwise if snake forms multiple wall loops there are big issues.
            for i in range(len(is_on_wall))[2:]:
                if is_on_wall[i]:
                    body_loop = self.body[:(i+1)]
                    break
            self.logger.debug("body_loop: {}".format(body_loop))
            body_wall_loop = self._gen_wall_perimeter(body_loop)
            self.logger.debug("body_wall_loop: {}".format(body_wall_loop))
            self._handle_loop_decision(body_wall_loop)


    def _handle_loop_decision(self, loop):
        '''Given an enclosing loop starting at head,
        encourages turning toward area with larger available space with FORCED_DECISION

        Parameters:
        loop -- list of (x, y) coordinates starting at head defining an enclosed region
        '''
        hx, hy = loop[0]
        curr_dir = self.check_direction()
        # Compare inner and outer areas
        in_loop_area, out_loop_area = self._compare_areas(loop)
        # Calculate chirality of loop
        turn_state = turn_state(loop)
        turn_inward = (in_loop_area > out_loop_area)
        # CW case
        if turn_state < 0:
            next_turn = CW if turn_inward else CCW
        # CCW case, or snake is bisecting play area
        # (turn_state 0; "inward" defined as left/ccw)
        else:
            next_turn = CCW if turn_inward else CW
        next_dir = TURN_TO_DIRECTION[(curr_dir, next_turn)]
        dx, dy = MOVE_DICT[next_dir]
        # Reward turning toward larger play area if legal
        nx = hx+dx
        ny = hy+dy
        if self.within_bounds((nx, ny)):
            next_pos_value = self._position_grid[nx][ny]
            if next_pos_value < LEGAL_THRESHOLD:
                self._position_grid[nx][ny] = FORCED_DECISION
        self.logger.debug("Turn State: %s", turn_state)
        self.logger.debug("The outside has an area of %s", out_loop_area)
        self.logger.debug("The inside has an area of %s", in_loop_area)
        self.logger.debug("I'm going to turn to the %s", next_dir)


    def _run_into_wall(self, move):
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


    def _compare_areas(self, loop):
        '''Function to calculate effective play areas inside and outside a defined loop

        Parameters:
        loop -- list of (x,y) coordinates defining an enclosed polygonal area
        '''
        inner_area = 0
        outer_area = 0
        width, height = self.dimensions
        head = self.body[0]
        bounding_path = mplPath.Path(numpy.array(loop))
        for y in range(height):
            for x in range(width):
                value = self._position_grid[x][y]
                incr = 1 if (value < LEGAL_THRESHOLD and (x,y) != head) else 0
                if bounding_path.contains_point(point):
                    inner_area += incr
                else:
                    outer_area += incr
        return inner_area, outer_area

    
    def _gen_wall_perimeter(self, body_loop):
        '''Appends wall vertices to the coordinate array body_loop such that the vertices all form the perimeter of the loop.

        Parameters:
        body_loop -- an array of the coordinates of the body of the snake which form a loop with the wall.
        '''
        self.logger.debug("find wall perimeter")
        width, height = self.dimensions
        direction = self.check_direction()
        dx, dy = MOVE_DICT[direction]
        self.logger.debug("direction: {}".format((dx, dy)))
        hx, hy = body_loop[0]
        tx, ty = body_loop[-1]
        hdx = 0
        hdy = 0
        tdx = 0
        tdy = 0
        loop = body_loop
        if direction == RT:
            hdx = width
            tdx = -1
        elif direction == LT:
            hdx = -1
            tdx = width
        elif direction == UP:
            hdy = -1
            tdy = height
        else:
            hdy = height
            tdy = -1
        #There are two corners enclosed
        if (width -1 in [hx, tx] and 0 in [hx, tx]) or (height -1 in [hy, ty] and 0 in [hy, ty]):
            self.logger.debug("There are two corners enclosed")
            #Always get the area LEFT of the snake head (from the snake's perspective)
            if direction == RT:
                loop.extend([(tdx, ty), (-1, -1), (width + 1, -1), (hdx, hy)])
            elif direction == LT:
                loop.extend([(tdx, ty), (-1, height), (width, height), (hdx, hy)])
            elif direction == UP:
                loop.extend([(tx, tdy), (-1, -1), (-1, height),  (hx, hdy)])
            else:
                loop.extend([(tx, tdy), (width, height),  (width, -1), (hx, hdy)])
        #There are no corners enclosed
        elif (hx == tx or hy == ty):
            self.logger.debug("There are no corners enclosed")
            # The loop is against either the right or left wall
            if (direction in [RT, LT]):
                loop.extend([(hdx, ty), (hdx, hy)])
            # The loop is against either the top or bottom wall
            else:
                loop.extend([(tx, hdy), (hx, hdy)])
        #There is one corner enclosed
        else:
            self.logger.debug("There is one corner enclosed")
            if (direction in [RT, LT]):
                #top corner
                if ty == 0:
                    loop.append((tx, -1))
                    # top right
                    if direction == RT:
                        loop.append((width, -1))
                    #top left
                    else:
                         loop.append((-1, -1))
                #bottom corner
                else:
                    loop.append((tx, height))
                    #bottom right
                    if direction == RT:
                        loop.append((width, height))
                    #bottom left
                    else:
                         loop.append((-1, height))
                loop.append((hdx, hy))
            else:
                #head is at either top or bottom.
                #left corner
                if tx == 0:
                    loop.append((-1, ty))
                    # top left
                    if direction == UP:
                        loop.append((-1, -1))
                    #bottom left
                    if direction == DN:
                        loop.append((-1, height))
                #right corner
                else:
                    loop.append((width, ty))
                    # top right
                    if direction == UP:
                        loop.append((width, -1))
                    #bottom right
                    if direction == DN:
                        loop.append((width, height))
                loop.append((hx, hdy))
        return loop
