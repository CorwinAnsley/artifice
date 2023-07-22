import PySimpleGUI as sg
import traceback
import re
import docker
import multiprocessing
import threading
import queue
import os.path
import sys
from webbrowser import open_new_tab

from artifice_core.language import translator
import artifice_core.start_rampart
import artifice_core.consts as consts
import artifice_core.select_protocol_window
import artifice_core.piranha_options_window
import artifice_core.window_functions as window_functions
from artifice_core.start_piranha import launch_piranha
from artifice_core.update_log import log_event, update_log
from artifice_core.window_functions import print_container_log, check_stop_on_close, get_pre_log, setup_check_container, error_popup
from artifice_core.alt_button import AltButton

def setup_panel(config):
    sg.theme("PANEL")

    is_piranhaGUI = True

    rampart_running, rampart_button_text, rampart_status, got_rampart_image = setup_check_container('RAMPART')
    rampart_button_text = translator(rampart_button_text)
    rampart_status = translator(rampart_status)
    piranha_running, piranha_button_text, piranha_status, got_piranha_image = setup_check_container('Analysis')
    piranha_button_text = translator(piranha_button_text)
    piranha_status = translator(piranha_status)


    SHOW_RAMPART = config['SHOW_RAMPART']
    if SHOW_RAMPART == False:
        got_rampart_image = False
        rampart_running = False

    #button_size=(220,36)
    rampart_tab_title = translator('RAMPART OUTPUT')
    piranha_tab_title = translator('PIRANHA OUTPUT')
    selected_protocol_text = translator('Selected Protocol') + ": " + str(config["PROTOCOL"])

    rampart_tab = [
    [sg.Multiline(write_only=True, font=consts.CONSOLE_FONT, expand_x=True, expand_y=True, key='-RAMPART OUTPUT-'),],
    ]

    piranha_tab = [
    [sg.Multiline(write_only=True, font=consts.CONSOLE_FONT, expand_x=True, expand_y=True, key='-PIRANHA OUTPUT-'),],
    ]

    output_tabs = []
    if is_piranhaGUI:
        output_tabs.insert(0, sg.Tab(piranha_tab_title,piranha_tab,visible=is_piranhaGUI,key='-PIRANHA TAB-'))
    if SHOW_RAMPART:
        output_tabs.insert(0, sg.Tab(rampart_tab_title,rampart_tab,visible=False,key='-RAMPART TAB-'))

    layout = [
    [AltButton(button_text=translator('Edit run'),key='-EDIT-'),],
    [sg.Text(rampart_status, visible=SHOW_RAMPART, key='-RAMPART STATUS-',),sg.Push(),
    sg.Text(selected_protocol_text, visible=got_rampart_image, key='-PROTOCOL STATUS-'),
    AltButton(button_text=translator('Select Another Protocol'), visible=got_rampart_image, key='-SELECT PROTOCOL-')],
    [
    AltButton(button_text=rampart_button_text, visible=got_rampart_image,key='-START/STOP RAMPART-'),
    AltButton(button_text=translator('Display RAMPART'),visible=rampart_running,key='-VIEW RAMPART-'),
    ],
    [sg.Text(piranha_status,visible=is_piranhaGUI, key='-PIRANHA STATUS-'),],
    [
    AltButton(button_text=piranha_button_text, visible=got_piranha_image, key='-START/STOP PIRANHA-'),
    AltButton(button_text=translator('Analysis Options'),visible=got_piranha_image,key='-PIRANHA OPTIONS-'),
    AltButton(button_text=translator('Open Report'), visible=False, key='-VIEW PIRANHA-'),
    ],
    [sg.TabGroup([output_tabs],expand_x=True, expand_y=True)],
    ]

    panel = sg.Frame("", layout, border_width=0, relief="solid", pad=(0,16), expand_x=True, expand_y=True)

    return panel, rampart_running, piranha_running

def create_main_window(version = 'ARTIFICE', window = None):
    update_log('creating main window')

    config = artifice_core.consts.retrieve_config()
  
    panel, rampart_running, piranha_running = setup_panel(config)

    content = window_functions.setup_content(panel)

    layout = window_functions.setup_header_footer(content)


    new_window = sg.Window(version, layout, resizable=True, enable_close_attempted_event=True, finalize=True,
                           font=consts.DEFAULT_FONT,icon=consts.ICON, margins=(0,0), element_padding=(0,0))
    #new_window.TKroot.minsize(1024,640)
    #new_window.TKroot.minsize(640,480)
    new_window.set_min_size(size=(800,600))
    new_window.set_title(artifice_core.consts.VERSION)

    if window != None:
        window.close()

    AltButton.intialise_buttons(new_window)

    return new_window, rampart_running, piranha_running

def run_main_window(window, run_info, version = 'ARTIFICE', rampart_running = False, piranha_running = False):
    config = artifice_core.consts.retrieve_config()
   
    rampart_protocol = config['PROTOCOL']

    docker_client = docker.from_env()
    rampart_container = None
    rampart_log_queue = queue.Queue()
    piranha_container = None
    piranha_log_queue = queue.Queue()

    if rampart_running:
        container = get_pre_log(docker_client, rampart_log_queue, 'rampart')

    if piranha_running:
        container = get_pre_log(docker_client, piranha_log_queue, 'piranha')


    while True:
        event, values = window.read(timeout=500)

        if event != '__TIMEOUT__':
            log_event(f'{event} [main window]')


        if piranha_running:
            try:
                piranha_finished = print_container_log(piranha_log_queue, window, '-PIRANHA OUTPUT-', config['PIRANHA_LOGFILE'])
                if piranha_finished:
                    piranha_running = False
                    artifice_core.start_rampart.stop_docker(client=docker_client, container=piranha_container)
                    window['-START/STOP PIRANHA-'].update(text=translator('Start Analysis'))
                    window['-PIRANHA STATUS-'].update(translator('Analysis is not running'))
                    window['-VIEW PIRANHA-'].update(visible=True)
                    try:
                        output_path = run_info['outputPath']
                        output_file = f'{output_path}/report.html'
                        if os.path.isfile(output_file):
                            open_new_tab(output_file)
                    except:
                        pass

            except Exception as err:
                error_popup(err)

        if rampart_running:
            rampart_finished = print_container_log(rampart_log_queue, window, '-RAMPART OUTPUT-', config['RAMPART_LOGFILE'])
            if rampart_finished:
                rampart_running = False
                artifice_core.start_rampart.stop_docker(client=docker_client, container=rampart_container)
                window['-VIEW RAMPART-'].update(visible=False)
                window['-START/STOP RAMPART-'].update(text=translator('Start RAMPART'))
                window['-RAMPART STATUS-'].update(translator('RAMPART is not running'))

        if event == 'Exit' or event == sg.WINDOW_CLOSE_ATTEMPTED_EVENT:
            running_tools = []

            if rampart_running:
                running_tools.append('RAMPART')
            if piranha_running:
                running_tools.append('PIRANHA')
            try:
                check_stop_on_close(running_tools, window, docker_client, rampart_container)
            except Exception as err:
                error_popup(err)


            break

        elif event == '-START/STOP RAMPART-':
            try:
                if rampart_running:
                    rampart_running = False
                    artifice_core.start_rampart.stop_docker(client=docker_client, container=rampart_container)
                    print_container_log(rampart_log_queue, window, '-RAMPART OUTPUT-', config['RAMPART_LOGFILE'])
                    window['-VIEW RAMPART-'].update(visible=False)
                    window['-START/STOP RAMPART-'].update(text=translator('Start RAMPART'))
                    window['-RAMPART STATUS-'].update(translator('RAMPART is not running'))
                else:
                    art_protocol_path = config['PROTOCOLS_DIR'] / rampart_protocol
                    protocol_path = artifice_core.select_protocol_window.get_protocol_dir(art_protocol_path)
                    rampart_container = artifice_core.start_rampart.launch_rampart(
                            run_info, docker_client,
                            firstPort=config['RAMPART_PORT_1'], secondPort=config['RAMPART_PORT_2'],
                            container=rampart_container,
                            protocol_path=protocol_path
                            )
                    rampart_running = True
                    window['-VIEW RAMPART-'].update(visible=True)
                    window['-START/STOP RAMPART-'].update(text=translator('Stop RAMPART'))
                    window['-RAMPART STATUS-'].update(translator('RAMPART is running'))

                    rampart_log = rampart_container.logs(stream=True)
                    rampart_log_thread = threading.Thread(target=artifice_core.start_rampart.queue_log, args=(rampart_log, rampart_log_queue), daemon=True)
                    rampart_log_thread.start()

                    update_log('',filename=config['RAMPART_LOGFILE'],overwrite=True)

                    window['-RAMPART TAB-'].select() 

            except Exception as err:
                error_popup(err)

        elif event == '-START/STOP PIRANHA-':
            try:
                if piranha_running:
                    piranha_running = False
                    artifice_core.start_rampart.stop_docker(client=docker_client, container_name='piranha', container=piranha_container)
                    print_container_log(piranha_log_queue, window, '-PIRANHA OUTPUT-', config['PIRANHA_LOGFILE'])
                    window['-START/STOP PIRANHA-'].update(text=translator('Start Analysis'))
                    window['-PIRANHA STATUS-'].update(translator('Analysis is not running'))

                else:
                    piranha_container = launch_piranha(run_info, docker_client)
                    piranha_running = True
                    window['-START/STOP PIRANHA-'].update(text=translator('Stop Analysis'))
                    window['-PIRANHA STATUS-'].update(translator('Analysis is running'))

                    piranha_log = piranha_container.logs(stream=True)
                    piranha_log_thread = threading.Thread(target=artifice_core.start_rampart.queue_log, args=(piranha_log, piranha_log_queue), daemon=True)
                    piranha_log_thread.start()

                    update_log('',filename=config['PIRANHA_LOGFILE'],overwrite=True)

                    window['-PIRANHA TAB-'].select()

            except Exception as err:
                error_popup(err)

        elif event == '-VIEW RAMPART-':
            address = 'http://localhost:'+str(config['RAMPART_PORT_1'])
            update_log(f'opening address: "{address}" in browser to view RAMPART')

            try:
                open_new_tab(address)
            except Exception as err:
                error_popup(err)

        elif event == '-VIEW PIRANHA-':
            try:
                output_path = run_info['outputPath']
                """
                if sys.platform.startswith("darwin"):
                    open_new_tab(f'file:///{output_path}/piranha_output/report.html')
                else:
                    open_new_tab(f'{output_path}/piranha_output/report.html')
                """
                open_new_tab(f'file:///{output_path}/piranha_output/report.html')
            except Exception as err:
                error_popup(err)

        elif event == '-SELECT PROTOCOL-':
            try:
                protocol_window = artifice_core.select_protocol_window.create_protocol_window(version=version)
                rampart_protocol = artifice_core.select_protocol_window.run_protocol_window(protocol_window, version=version)
                if rampart_protocol != None:
                    window['-PROTOCOL STATUS-'].update(f'Selected Protocol: {rampart_protocol}')

            except Exception as err:
                error_popup(err)

        elif event == '-PIRANHA OPTIONS-':
            try:
                piranha_options_window = artifice_core.piranha_options_window.create_piranha_options_window(version=version)
                run_info = artifice_core.piranha_options_window.run_piranha_options_window(piranha_options_window, run_info, version=version)
  
            except Exception as err:
                error_popup(err)

        elif event == '-EDIT-':
            #rampart_log_queue.task_done()
            #piranha_log_queue.task_done()
            window.close()
            return True



    window.close()

if __name__ == '__main__':
    window, rampart_running = create_main_window()
    run_main_window(window, rampart_running=rampart_running)

    window.close()
