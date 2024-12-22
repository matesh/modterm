from modterm.components.window_base import WindowBase
import curses
from textwrap import wrap


def show_popup_message(screen, width: int, title: str, message: str):
    text_width = width - 4 if width < screen.getmaxyx()[1] else screen.getmaxyx()[1]-4
    message_rows = wrap(message, width=text_width)

    popup = WindowBase(screen=screen, height=len(message_rows) + 4, width=width, title=title)
    popup.draw_window()
    for idx, text in enumerate(message_rows, start=2):
        popup.window.addstr(idx, 2, text)
    popup.window.refresh()
    curses.napms(3000)
    curses.flushinp()
