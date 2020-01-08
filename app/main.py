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
    data = bottle.request.json

    """
    TODO: If you intend to have a stateful snake AI,
            initialize your snake state here using the
            request's data if necessary.
    """
    print(json.dumps(data))

    color = "#993333"
    head = "sand-worm"
    tail = "pixel"

    return start_response(color, head, tail)


@bottle.post('/move')
def move():
    data = bottle.request.json

    """
    TODO: Using the data from the endpoint request object, your
            snake AI must choose a direction to move in.
    """
    # Unpack game data
    #print(json.dumps(data))
    game_id = data["game"]["id"]
    turn = data["turn"]

    b_width = data["board"]["width"]
    b_height = data["board"]["height"]
    foods = data["board"]["food"]
    snakes = data["board"]["snakes"]
    ends = [(snake[0], snake[-1]) for snake in snakes]
    
    health = data["you"]["health"]
    body = data["you"]["body"]
    head = body[0]
    tail = body[-1]
    obstacles = []
    for snake in snakes:
        obstacles.extend(snake[:-1])

    # Initialize/update arena
    arena = Arena(
        b_width,
        b_height,
        player_h=head,
        player_t=tail,
        obstacles=obstacles,
        ends=ends,
        foods=foods
        )    
    # Pick a random best direction
    directions = arena.rank_moves()
    if directions:
        bests = [move for rank, move in directions if rank == directions[0][0]]
        direction = random.choice(bests)
    # If no legal moves... time to die
    else:
        direction = 'up'

    return move_response(direction)


@bottle.post('/end')
def end():
    data = bottle.request.json

    """
    TODO: If your snake AI was stateful,
        clean up any stateful objects here.
    """
    print(json.dumps(data))

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
