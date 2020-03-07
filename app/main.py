import json
import logging
import os
import bottle

from sys import argv
from api import ping_response, start_response, move_response, end_response
from utils.arena import Arena

# Set log level
if len(argv) > 1:
    LOG_LEVEL = argv[1]
else:
    LOG_LEVEL = 'DEBUG'
logger = logging.getLogger()
logger.setLevel(LOG_LEVEL)

# Constants
COLOR = '#993333'
HEAD = 'sand-worm'
TAIL = 'pixel'

WELCOME = '''--
Welcome, contestant.
=== TA\'AURIC, ASPECT OF WAR ===
'''


@bottle.route('/')
def index():
    return '''
    Battlesnake documentation can be found at
       <a href="https://docs.battlesnake.com">https://docs.battlesnake.com</a>.
    '''


@bottle.route('/static/<path:path>')
def static(path):
    '''
    Given a path, return the static file located relative
    to the static folder.

    This can be used to return the snake head URL in an API response.
    '''
    return bottle.static_file(path, root='static/')


@bottle.post('/ping')
def ping():
    '''
    A keep-alive endpoint used to prevent cloud application platforms,
    such as Heroku, from sleeping the application instance.
    '''
    return ping_response()


@bottle.post('/start')
def start():
    '''Initialize stateful data'''
    logger.info(WELCOME)
    logger.info(
        "Initializing snake with\ncolour: %s\nhead: %s\ntail: %s",
        COLOR, HEAD, TAIL)
    # Initialize global arena instance (keeps state)
    global ARENA
    data = bottle.request.json
    b_width = data['board']['width']
    b_height = data['board']['height']
    ARENA = Arena(b_width, b_height)

    return start_response(COLOR, HEAD, TAIL)


@bottle.post('/move')
def move():
    '''Choose a direction to move!'''
    global ARENA
    # Unpack game data
    data = bottle.request.json
    game_id = data['game']['id']
    turn = data['turn']
    name = data['you']['name']
    health = data['you']['health']
    logger.debug("\n===== ({}) TURN {} =====".format(name, turn))

    # Format data for Arena
    body = [(seg['x'], seg['y']) for seg in data['you']['body']]
    snakes = [[(s['x'], s['y']) for s in sn['body']]
              for sn in data['board']['snakes'] if sn['name'] != name]
    foods = [(fd['x'], fd['y']) for fd in data['board']['food']]

    # Update arena
    ARENA.update_heatmap(body, snakes, foods)
    logger.debug("ARENA HEATMAP:\n%s", ARENA.arena_to_str())
    # Check for self-loops
    ARENA.check_self_loop()
    # Pick best move from newly created heatmap
    directions = ARENA.rank_moves()
    if directions:
        direction = directions[0]
    else:
        direction = 'up'
        logger.debug("GUESS I'LL DIE LMAO")
    logger.debug("Moving {}".format(direction))
    return move_response(direction)


@bottle.post('/end')
def end():
    '''Clean up any stateful objects'''
    return end_response()


# Expose WSGI app (so gunicorn can find it)
application = bottle.default_app()

if __name__ == '__main__':
    bottle.run(
        application,
        host=os.getenv('IP', '0.0.0.0'),
        port=os.getenv('PORT', '8080'),
        debug=os.getenv('DEBUG', True)
    )
