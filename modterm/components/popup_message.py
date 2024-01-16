from modterm.components.window_base import WindowBase
import curses


def show_popup_message(screen, width: int, title: str, message: str):
    text_width = width - 4 if width < screen.getmaxyx()[1] else screen.getmaxyx()[1]-4
    message_rows = []
    message_split = message.split(" ")
    line = message_split[0]
    for word in message_split[1:]:
        new_line = line + " " + word
        if len(new_line) < text_width:
            line = new_line
            continue
        message_rows.append(line)
        line = word
    if len(line) != 0:
        message_rows.append(line)

    popup = WindowBase(screen=screen, height=len(message_rows) + 4, width=width, title=title)
    popup.draw_window()
    for idx, text in enumerate(message_rows, start=2):
        popup.window.addstr(idx, 2, text)
    popup.window.refresh()
    curses.napms(3000)
