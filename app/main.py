import json
import os
import random
import bottle

from api import ping_response, start_response, move_response, end_response
from utils.arena import Arena

@bottle.route('/')
def index():
    return '''
    Battlesnake documentation can be found at
       <a href="https://docs.battlesnake.com">https://docs.battlesnake.com</a>.
    '''


@bottle.route('/static/<path:path>')
def static(path):
    """
    Given a path, return the static file located relative
    to the static folder.

    This can be used to return the snake head URL in an API response.
    """
    return bottle.static_file(path, root='static/')


@bottle.post('/ping')
def ping():
    """
    A keep-alive endpoint used to prevent cloud application platforms,
    such as Heroku, from sleeping the application instance.
    """
    return ping_response()


@bottle.post('/start')
def start():
    """
    TODO: If you intend to have a stateful snake AI,
            initialize your snake state here using the
            request's data if necessary.
    """
    color = "#993333"
    head = "sand-worm"
    tail = "pixel"
    welcome = [
        '--',
        'Welcome, contestant.',
        '=== TA\'AURIC, ASPECT OF WAR ===',
        '',
        '<STYLE>',
        'color: {}'.format(color),
        'head: {}'.format(head),
        'tail: {}'.format(tail)
    ]
    print '\n'.join(welcome)
    # Initialize global arena instance (keeps state)
    global ARENA
    data = bottle.request.json
    b_width = data["board"]["width"]
    b_height = data["board"]["height"]
    ARENA = Arena(b_width, b_height)

    return start_response(color, head, tail)


@bottle.post('/move')
def move():
    """Choose a direction to move!"""
    global ARENA
    # Unpack game data
    data = bottle.request.json
    game_id = data["game"]["id"]
    turn = data["turn"]
    name = data["you"]["name"]
    health = data["you"]["health"]
    print "\n===== ({}) TURN {} =====".format(name, turn)

    # Format data for Arena
    body = [(seg['x'], seg['y']) for seg in data["you"]["body"]]
    snakes = [[(s['x'], s['y']) for s in sn["body"]] for sn in data["board"]["snakes"] if sn["name"] != name]
    foods = [(fd['x'], fd['y']) for fd in data["board"]["food"]]

    # Update arena
    ARENA.update_heatmap(body, snakes, foods)
    ARENA.print_arena()
    # Check for self-loops
    ARENA.check_self_loop()
    # Pick best move from newly created heatmap
    directions = ARENA.rank_moves()
    if directions:
        direction = directions[0]
    else:
        direction = 'up'
        print "GUESS I'LL DIE LMAO"
    print "Moving {}".format(direction)
    return move_response(direction)


@bottle.post('/end')
def end():
    data = bottle.request.json

    """
    TODO: If your snake AI was stateful,
        clean up any stateful objects here.
    """
    #print(json.dumps(data))

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
