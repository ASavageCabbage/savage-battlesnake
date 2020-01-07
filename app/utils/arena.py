import numpy

DEATH = 2
DANGER = 1
MOVE_DICT = {
    'up': (1, 0),
    'down': (-1, 0),
    'left': (0, -1),
    'right': (0, 1)
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
        # Initialize array to represent arena
        self._position_grid = numpy.zeros((width, height))
        # Initialize player head and tail
        self.head = kwargs.get('player_h', {'x':0, 'y':0})
        self.tail = kwargs.get('player_t', {'x':0, 'y':0})
        # Mark positions of food
        self.foods = kwargs.get('foods', [])
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
            self._position_grid[hx][hy] = DEATH
            danger_zone = [
                (hx-1,hy),
                (hx+1,hy),
                (hx,hy-1),
                (hx,hy+1)
            ]
            for x, y in danger_zone:
                if self._position_grid[x][y] < DANGER:
                    self._position_grid[x][y] = DANGER
            # Tail could grow if head is in reach of any food
            tx = tl['x']
            ty = tl['y']
            if ([coord for coord in self.foods if coord in danger_zone]
                and self._position_grid[tx][ty] < DANGER):
                self._position_grid[tx][ty] = DANGER

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
        return legal_moves