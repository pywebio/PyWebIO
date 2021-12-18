import time

import pywebio
from pywebio.output import *
from pywebio import session

goboard_size = 15
# -1 -> none, 0 -> black, 1 -> white
goboard = [
    [-1] * goboard_size
    for _ in range(goboard_size)
]


def winner():  # return winner piece, return None if no winner
    for x in range(2, goboard_size - 2):
        for y in range(2, goboard_size - 2):
            # check if (x,y) is the win center
            if goboard[x][y] != -1 and any([
                all(goboard[x][y] == goboard[m][n] for m, n in [(x - 2, y), (x - 1, y), (x + 1, y), (x + 2, y)]),
                all(goboard[x][y] == goboard[m][n] for m, n in [(x, y - 2), (x, y - 1), (x, y + 1), (x, y + 2)]),
                all(goboard[x][y] == goboard[m][n] for m, n in [(x - 2, y - 2), (x - 1, y - 1), (x + 1, y + 1), (x + 2, y + 2)]),
                all(goboard[x][y] == goboard[m][n] for m, n in [(x - 2, y + 2), (x - 1, y + 1), (x + 1, y - 1), (x + 2, y - 2)]),
            ]):
                return ['⚫', '⚪'][goboard[x][y]]


session_id = 0          # auto incremented id for each session
current_turn = 0        # 0 for black, 1 for white
player_count = [0, 0]   # count of player for two roles


def main():
    """Online Shared Gomoku Game

    A web based Gomoku (AKA GoBang, Five in a Row) game made with PyWebIO under 100 lines of Python code."""
    global session_id, current_turn, goboard
    if winner():  # The current game is over, reset game
        goboard = [[-1] * goboard_size for _ in range(goboard_size)]
        current_turn = 0

    my_turn = session_id % 2
    my_chess = ['⚫', '⚪'][my_turn]
    session_id += 1
    player_count[my_turn] += 1

    @session.defer_call
    def player_exit():
        player_count[my_turn] -= 1

    session.set_env(output_animation=False)
    put_html("""<style> table th, table td { padding: 0px !important;} button {padding: .75rem!important; margin:0!important} </style>""")  # Custom styles to make the board more beautiful

    put_markdown(f"""# Online Shared Gomoku Game
    All online players are assigned to two groups (black and white) and share this game. You can open this page in multiple tabs of your browser to simulate multiple users. This application uses less than 100 lines of code, the source code is [here](https://github.com/wang0618/PyWebIO/blob/dev/demos/gomoku_game.py)
    Currently online player: {player_count[0]} for ⚫, {player_count[1]} for ⚪. Your role is {my_chess}.
    """)

    def set_stone(pos):
        global current_turn
        if current_turn != my_turn:
            toast("It's not your turn!!", color='error')
            return
        x, y = pos
        goboard[x][y] = my_turn
        current_turn = (current_turn + 1) % 2

    @use_scope('goboard', clear=True)
    def show_goboard():
        table = [
            [
                put_buttons([dict(label=' ', value=(x, y), color='light')], onclick=set_stone) if cell == -1 else [' ⚫', ' ⚪'][cell]
                for y, cell in enumerate(row)
            ]
            for x, row in enumerate(goboard)
        ]
        put_table(table)

    show_goboard()
    while not winner():
        with use_scope('msg', clear=True):
            current_turn_copy = current_turn
            if current_turn_copy == my_turn:
                put_text("It's your turn!")
            else:
                put_row([put_text("Your opponent's turn, waiting... "), put_loading().style('width:1.5em; height:1.5em')], size='auto 1fr')
            while current_turn == current_turn_copy and not session.get_current_session().closed():  # wait for next move
                time.sleep(0.2)
            show_goboard()
    with use_scope('msg', clear=True):
        put_text('Game over. The winner is %s!\nRefresh page to start a new round.' % winner())


if __name__ == '__main__':
    pywebio.start_server(main, debug=True, port=8080)
