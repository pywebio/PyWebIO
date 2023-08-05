import time
from pywebio import start_server, config
from pywebio.output import *
from pywebio.session import run_js, local as session_local

TODAY_WORD = 'PYWEBIO'  # need to be uppercase

MAX_TRY = 6
WORD_LEN = len(TODAY_WORD)


CSS = """
.pywebio {padding-top: 0} .markdown-body table {display:table; width:250px; margin:10px auto;}
.markdown-body table th, .markdown-body table td {font-weight:bold; padding:0; line-height:50px;}
th>div,td>div {width:50px; height:50px}.btn-light {background-color:#d3d6da;}
@media (max-width: 435px) {.btn{padding:0.375rem 0.5rem;}}
@media (max-width: 355px) {.btn{padding:0.375rem 0.4rem;}}
"""


# To check if a user's input word is actually a legit word
# We just implement a placeholder function in this example
# If a guess word is UNHAPPY, toast a message
def is_word(s):  
    return 'UNHAPPY' not in s


def on_key_press(char):
    if session_local.curr_row >= MAX_TRY or session_local.game_pass:
        return

    if char == '◀':
        session_local.curr_word = session_local.curr_word[:-1]
        return clear(f's-{session_local.curr_row}-{len(session_local.curr_word)}')

    # show the char in grid
    with use_scope(f's-{session_local.curr_row}-{len(session_local.curr_word)}', clear=True):
        put_text(char)

    session_local.curr_word += char
    if len(session_local.curr_word) == WORD_LEN:  # submit a word guess
        if not is_word(session_local.curr_word):
            toast('Not in word list!', color='error')
            session_local.curr_word = ''
            for i in range(WORD_LEN):
                clear(f's-{session_local.curr_row}-{i}')
        else:
            for idx, c in enumerate(session_local.curr_word):
                time.sleep(0.2)
                if TODAY_WORD[idx] == c:
                    session_local.green_chars.add(c)
                    run_js('$("button:contains(%s)").css({"background-color":"#6aaa64", "color":"white"})' % c)
                    text_bg = '#6aaa64'
                    session_local.game_result += '🟩'
                elif c in TODAY_WORD:
                    text_bg = '#c9b458'
                    session_local.game_result += '🟨'
                    if c not in session_local.green_chars:
                        run_js('$("button:contains(%s)").css({"background-color":"#c9b458", "color":"white"})' % c)
                else:
                    text_bg = '#787c7e'
                    session_local.game_result += '⬜'
                    run_js('$("button:contains(%s)").css({"background-color":"#787c7e", "color":"white"})' % c)

                with use_scope(f's-{session_local.curr_row}-{idx}', clear=True):
                    put_text(c).style(f'color:white;background:{text_bg}')

            session_local.game_result += '\n'
            if session_local.curr_word == TODAY_WORD:
                toast('Genius', color='success')
                session_local.game_pass = True

            session_local.curr_row += 1
            session_local.curr_word = ''

        if session_local.game_pass:
            message = f'Wordle {session_local.curr_row}/{MAX_TRY}\n' + session_local.game_result
            with popup("Game Result", size='small'):
                put_text(message).style('text-align: center')
                put_button('Share', color='success', onclick=lambda: toast('Copied to clipboard') or run_js("""navigator.clipboard.write([new ClipboardItem({"text/plain":new Blob([text],{type:"text/plain"})})]);""", text=message)).style('text-align: center')


@config(title="WORDLE with PyWebIO", description="A wordle-like game implemented with PyWebIO", css_style=CSS)
def main():
    put_markdown(
        '# WORDLE \n A pure python implementation of a [Wordle-like game](https://en.wikipedia.org/wiki/Wordle), using PyWebIO library. '
        '[Source code](https://github.com/pywebio/PyWebIO/blob/dev/demos/wordle.py)'
    ).style('text-align:center')

    grid = [
        [put_scope(f's-{x}-{y}', content=put_text(' ')) for y in range(WORD_LEN)]
        for x in range(MAX_TRY)
    ]
    put_table(grid).style('text-align: center')

    keyboard = [
        put_buttons([dict(label=c, value=c, color='light') for c in keys], on_key_press, serial_mode=True)
        for keys in ['QWERTYUIOP', 'ASDFGHJKL', 'ZXCVBNM◀']
    ]
    put_column(keyboard).style('text-align: center')

    session_local.curr_row = 0
    session_local.curr_word = ''
    session_local.green_chars = set()
    session_local.game_pass = False
    session_local.game_result = ''


if __name__ == '__main__':
    start_server(main, port=8080, cdn=False)
