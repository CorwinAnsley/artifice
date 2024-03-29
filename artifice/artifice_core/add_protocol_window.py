import PySimpleGUI as sg

import artifice_core.consts as consts
import artifice_core.window_functions as window_functions
from artifice_core.language import translator, setup_translator
from artifice_core.alt_button import AltButton, AltFolderBrowse
from artifice_core.update_log import log_event, update_log
from artifice_core.window_functions import error_popup

def setup_panel():
    sg.theme("PANEL")
    translator = setup_translator()

    button_size=(120,36)
    layout = [
    [sg.Text(translator('Select the protocol directory:'),),],
    [
    sg.In(size=(25,1), enable_events=True,expand_y=False, key='-PROTOCOL DIR-',),
    AltFolderBrowse(button_text=translator('Browse'),size=button_size),
    ]]

    panel = sg.Frame("", layout, border_width=0, relief="solid", pad=(0,16))

    return panel

def create_add_protocol_window(title=consts.WINDOW_TITLE, window = None):
    update_log('creating add protocol window')

    panel = setup_panel()

    content = window_functions.setup_content(panel, title=title, small=True, button_text='Confirm', button_key='-CONFIRM-')

    layout = window_functions.setup_header_footer(content, small=True)

    new_window = sg.Window(title, layout, resizable=False, enable_close_attempted_event=True, 
                           finalize=True,icon=consts.ICON, font=consts.DEFAULT_FONT, margins=(0,0), element_padding=(0,0))

    if window != None:
        window.close()

    AltButton.intialise_buttons(new_window)

    return new_window

def run_add_protocol_window(window):
    
    while True:
        event, values = window.read()

        if event != None:
            log_event(f'{event} [add protocol window]')

        if event == 'Exit' or event == sg.WINDOW_CLOSE_ATTEMPTED_EVENT:
            window.close()
            return

       
        elif event == '-CONFIRM-':
            try:
                window.close()
                return values['-PROTOCOL DIR-']
            except Exception as err:
                error_popup(err)

    window.close()