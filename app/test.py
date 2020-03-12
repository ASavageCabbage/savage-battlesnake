import logging
import sys
from traceback import format_exception

from utils.arena import *

# Set log level
LOG_LEVEL = 'DEBUG'
if len(sys.argv) > 1 and hasattr(logging, sys.argv[1]):
    LOG_LEVEL = sys.argv[1]
logging.basicConfig(level=getattr(logging, LOG_LEVEL))
logger = logging.getLogger()


def arena_decision(width, height, body, snakes=[], foods=[]):
    '''
    Generates an Arena instance and tests decision-making
    '''
    logger.debug("Beginning test...")
    arena = Arena(width, height)
    arena.update_attributes(
        body=body,
        snakes=snakes,
        foods=foods
    )
    arena.update_heatmap()
    arena.update_obstacles()
    arena.handle_area_choices()
    logger.debug("ARENA STATE:\n%s", arena.arena_to_str())
    directions = arena.rank_moves()
    if directions:
        direction = directions[0]
    else:
        direction = 'up'
        logger.debug("GUESS I'LL DIE LMAO")
    return direction


WIDTH = 7
HEIGHT = 7

# Make sure things don't explode on startup
STARTING_BODY = [(3,3),(3,3),(3,3)]
try:
    arena_decision(WIDTH, HEIGHT, STARTING_BODY)
except Exception:
    exc_type, exc_value, exc_tb = sys.exc_info()
    stack_trace = ''.join(format_exception(exc_type, exc_value, exc_tb))
    logger.warning("Startup test failed with exception:\n%s", stack_trace)

# ==== Test basic rules ====
WALL_AVOIDANCE_BODIES = {
    UP: [(3,0),(3,1),(3,2)],
    DN: [(3,HEIGHT-1),(3,HEIGHT-2),(3,HEIGHT-3)],
    LT: [(0,3),(1,3),(2,3)],
    RT: [(WIDTH-1,3),(WIDTH-2,3),(WIDTH-3,3)]
}
assert arena_decision(WIDTH, HEIGHT, WALL_AVOIDANCE_BODIES[UP]) != UP
assert arena_decision(WIDTH, HEIGHT, WALL_AVOIDANCE_BODIES[DN]) != DN
assert arena_decision(WIDTH, HEIGHT, WALL_AVOIDANCE_BODIES[LT]) != LT
assert arena_decision(WIDTH, HEIGHT, WALL_AVOIDANCE_BODIES[RT]) != RT
logger.info("Basic wall avoidance tests passed!")

# Correct answer is right
FOUR_TOP_LEFT_CORNER = [(0,0),(1,0),(0,1),(1,1)]
SELF_AVOIDANCE_BODY = [(3,3),(3,2),(3,1),(2,1),(2,2),(2,3),(2,4),(3,4),(4,4)]
assert arena_decision(WIDTH, HEIGHT, SELF_AVOIDANCE_BODY) == RT
assert arena_decision(WIDTH, HEIGHT, SELF_AVOIDANCE_BODY, foods=FOUR_TOP_LEFT_CORNER) == RT
logger.info("Basic self avoidance tests passed!")

# Correct answer is right
ENEMY_AVOIDANCE_BODY = [(3,3),(3,2),(3,1)]
ENEMY_AVOIDANCE_ENEMY = [(2,2),(2,3),(2,4),(3,4),(4,4)]
assert arena_decision(WIDTH, HEIGHT, ENEMY_AVOIDANCE_BODY, snakes=[ENEMY_AVOIDANCE_ENEMY]) == RT
assert arena_decision(WIDTH, HEIGHT, ENEMY_AVOIDANCE_BODY, snakes=[ENEMY_AVOIDANCE_ENEMY], foods=FOUR_TOP_LEFT_CORNER) == RT
logger.info("Basic enemy avoidance tests passed!")

# ==== Test self-loop avoidance ====
# Horizontal orientation
ONE_SQUARE_LOOP = [(2,3),(2,4),(2,5),(3,5),(4,5),(4,4),(4,3),(4,2),(3,2),(2,2),(1,2),(0,2)]
assert arena_decision(WIDTH, HEIGHT, ONE_SQUARE_LOOP, foods=[(3,4)]) == LT
ONE_SQUARE_LOOP_DIVET = [(2,3),(2,4),(2,5),(3,5),(4,5),(4,4),(4,3),(4,2),(3,2),(3,1),(2,1),(1,1),(1,2),(0,2)]
assert arena_decision(WIDTH, HEIGHT, ONE_SQUARE_LOOP_DIVET, foods=[(3,4)]) == LT
ONE_SQUARE_LOOP_LT_EDGE = [(2,3),(2,4),(2,5),(3,5),(4,5),(4,4),(4,3),(4,2),(3,2),(3,1),(2,1),(1,1),(0,1),(0,2)]
assert arena_decision(WIDTH, HEIGHT, ONE_SQUARE_LOOP_LT_EDGE, foods=[(3,4)]) == LT
ONE_SQUARE_LOOP_RT_EDGE = [(2,3),(2,4),(2,5),(3,5),(4,5),(4,4),(4,3),(4,2),(4,1),(3,1),(2,1),(1,1),(1,2),(0,2)]
assert arena_decision(WIDTH, HEIGHT, ONE_SQUARE_LOOP_LT_EDGE, foods=[(3,4)]) == LT
# Vertical orientation
ONE_SQUARE_LOOP_V = [(y,x) for x,y in ONE_SQUARE_LOOP]
assert arena_decision(WIDTH, HEIGHT, ONE_SQUARE_LOOP_V, foods=[(4,3)]) == UP
ONE_SQUARE_LOOP_DIVET_V = [(y,x) for x,y in ONE_SQUARE_LOOP_DIVET]
assert arena_decision(WIDTH, HEIGHT, ONE_SQUARE_LOOP_DIVET_V, foods=[(4,3)]) == UP
ONE_SQUARE_LOOP_UP_EDGE = [(y,x) for x,y in ONE_SQUARE_LOOP_LT_EDGE]
assert arena_decision(WIDTH, HEIGHT, ONE_SQUARE_LOOP_UP_EDGE, foods=[(4,3)]) == UP
ONE_SQUARE_LOOP_DN_EDGE = [(y,x) for x,y in ONE_SQUARE_LOOP_RT_EDGE]
assert arena_decision(WIDTH, HEIGHT, ONE_SQUARE_LOOP_DN_EDGE, foods=[(4,3)]) == UP
logging.info("Basic self-loop avoidance tests passed!")

# ==== Test wall-loop avoidance ====
# 0 corner cases
NO_CORNER_LOOP_LT = [(0,2),(1,2),(2,2),(2,3),(2,4),(2,5),(1,5),(0,5),(0,6)]
assert arena_decision(WIDTH, HEIGHT, NO_CORNER_LOOP_LT, foods=[(0,3)]) == UP
NO_CORNER_LOOP_RT = [(WIDTH-1-x, y) for x,y in NO_CORNER_LOOP_LT]
assert arena_decision(WIDTH, HEIGHT, NO_CORNER_LOOP_RT, foods=[(WIDTH-1,3)]) == UP
NO_CORNER_LOOP_UP = [(y, x) for x,y in NO_CORNER_LOOP_LT]
assert arena_decision(WIDTH, HEIGHT, NO_CORNER_LOOP_UP, foods=[(3,0)]) == LT
NO_CORNER_LOOP_DN = [(x, HEIGHT-1-y) for x,y in NO_CORNER_LOOP_UP]
assert arena_decision(WIDTH, HEIGHT, NO_CORNER_LOOP_DN, foods=[(3,HEIGHT-1)]) == LT
logging.info("0 corner wall-loop tests passed!")
# 1 corner cases
ONE_CORNER_LOOP_UL = [(0,3),(1,3),(2,3),(2,2),(2,1),(2,0)]
assert arena_decision(WIDTH, HEIGHT, ONE_CORNER_LOOP_UL, foods=[(0,0)]) == DN
ONE_CORNER_LOOP_UR = [(WIDTH-1-x, y) for x,y in ONE_CORNER_LOOP_UL]
assert arena_decision(WIDTH, HEIGHT, ONE_CORNER_LOOP_UR, foods=[(WIDTH-1,0)]) == DN
ONE_CORNER_LOOP_LL = [(x, HEIGHT-1-y) for x,y in ONE_CORNER_LOOP_UR]
assert arena_decision(WIDTH, HEIGHT, ONE_CORNER_LOOP_LL, foods=[(0,HEIGHT-1)]) == UP
ONE_CORNER_LOOP_LR = [(WIDTH-1-x, y) for x,y in ONE_CORNER_LOOP_LL]
assert arena_decision(WIDTH, HEIGHT, ONE_CORNER_LOOP_LR, foods=[(WIDTH-1,HEIGHT-1)]) == UP
logging.info("1 corner wall-loop tests passed!")
# 2 corner cases
TWO_CORNER_DN = [(0,2),(1,2),(2,2),(3,2),(3,3),(4,3),(5,3),(5,2),(5,1),(6,1)]
assert arena_decision(WIDTH, HEIGHT, TWO_CORNER_DN, foods=[(0,0)]) == DN
TWO_CORNER_UP = TWO_CORNER_DN[::-1]
assert arena_decision(WIDTH, HEIGHT, TWO_CORNER_UP, foods=[(WIDTH-1,0)]) == DN
logging.info("2 corner wall-loop tests passed!")
