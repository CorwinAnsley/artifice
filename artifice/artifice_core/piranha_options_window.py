import PySimpleGUI as sg

import artifice_core.consts
from artifice_core.alt_button import AltButton, AltFolderBrowse
from artifice_core.update_log import log_event, update_log
from artifice_core.window_functions import error_popup, translate_text, get_translate_scheme, scale_image
from artifice_core.manage_runs import save_run, save_changes, load_run

def make_theme():
    Artifice_Theme = {'BACKGROUND': "#072429",
               'TEXT': '#f7eacd',
               'INPUT': '#1e5b67',
               'TEXT_INPUT': '#f7eacd',
               'SCROLL': '#707070',
               'BUTTON': ('#f7eacd', '#d97168'),
               'PROGRESS': ('#000000', '#000000'),
               'BORDER': 1,
               'SLIDER_DEPTH': 0,
               'PROGRESS_DEPTH': 0}

    sg.theme_add_new('Artifice', Artifice_Theme)

def setup_layout(theme='Dark', font = None):
    sg.theme(theme)
    config = artifice_core.consts.retrieve_config()
    translate_scheme = get_translate_scheme()
    try:
        language = config['LANGUAGE']
    except:
        language = 'English'

    button_size=(120,36)

    input_options_tab = [
        [
        sg.Text(translate_text('Reference Sequences:',language,translate_scheme),size=(14,1)),
        sg.In(size=(25,1), enable_events=True,expand_y=False, key='-REFERENCE SEQUENCES-',),
        AltFolderBrowse(button_text=translate_text('Browse',language,translate_scheme),tooltip=translate_text('Custom reference sequences file.',language,translate_scheme),font=font,size=button_size),
        ],

        [
        sg.Text(translate_text('Positive Control:',language,translate_scheme),size=(14,1)),
        sg.In(size=(25,1), enable_events=True,expand_y=False,tooltip=translate_text('Sample name of positive control. Default: `positive`',language,translate_scheme), key='-POSITIVE CONTROL-',),
        ],
        [
        sg.Text(translate_text('Negative Control:',language,translate_scheme),size=(14,1)),
        sg.In(size=(25,1), enable_events=True,expand_y=False,tooltip=translate_text('Sample name of negative control. Default: `negative`',language,translate_scheme), key='-NEGATIVE CONTROL-',),
        ],
    ]

    analysis_options_tab = [
        [
        sg.Text(translate_text('Sample Type:',language,translate_scheme),size=(14,1)),
        sg.In(size=(25,1), enable_events=True,expand_y=False,tooltip=translate_text('Specify sample type. Options: `stool`, `environmental`. Default: `stool`',language,translate_scheme), key='-SAMPLE TYPE-',),
        ],
        [
        sg.Text(translate_text('Analysis Mode:',language,translate_scheme),size=(14,1)),
        sg.In(size=(25,1), enable_events=True,expand_y=False,tooltip=translate_text('Specify analysis mode to run. Options: `vp1`. Default: `vp1`',language,translate_scheme), key='-ANALYSIS MODE-',),
        ],
        [
        sg.Text(translate_text('Medaka Model',language,translate_scheme),size=(14,1)),
        sg.In(size=(25,1), enable_events=True,expand_y=False,tooltip=translate_text('Medaka model to run analysis using. Default: r941_min_hac_variant_g507',language,translate_scheme), key='-MEDAKA MODEL-',),
        ],
        [
        sg.Text(translate_text('Minimum Mapping Quality',language,translate_scheme),size=(14,1)),
        sg.In(size=(25,1), enable_events=True,expand_y=False,tooltip=translate_text('Minimum mapping quality. Default: 50',language,translate_scheme), key='-MIN MAP QUALITY-',),
        ],
        [
        sg.Text(translate_text('Minimum Read Length',language,translate_scheme),size=(14,1)),
        sg.In(size=(25,1), enable_events=True,expand_y=False,tooltip=translate_text('Minimum read length. Default: 1000',language,translate_scheme), key='-MIN READ LENGTH-',),
        ],
        [
        sg.Text(translate_text('Maximum Read Length',language,translate_scheme),size=(14,1)),
        sg.In(size=(25,1), enable_events=True,expand_y=False,tooltip=translate_text('Maximum read length. Default: 1300',language,translate_scheme), key='-MAX READ LENGTH-',),
        ],
        [
        sg.Text(translate_text('Minimum Read Depth',language,translate_scheme),size=(14,1)),
        sg.In(size=(25,1), enable_events=True,expand_y=False,tooltip=translate_text('Minimum read depth required for consensus generation. Default: 50',language,translate_scheme), key='-MIN READ DEPTH-',),
        ],
        [
        sg.Text(translate_text('Minimum Read Percentage',language,translate_scheme),size=(14,1)),
        sg.In(size=(25,1), enable_events=True,expand_y=False,tooltip=translate_text('Minimum percentage of sample required for consensus generation. Default: 10',language,translate_scheme), key='-MIN READ PCENT-',),
        ],
        [
        sg.Text(translate_text('Primer Length',language,translate_scheme),size=(14,1)),
        sg.In(size=(25,1), enable_events=True,expand_y=False,tooltip=translate_text('Length of primer sequences to trim off start and end of reads. Default: 30',language,translate_scheme), key='-PRIMER LENGTH-',),
        ],
    ]
    

    output_options_tab = [
        [
        sg.Text(translate_text('Publish Directory',language,translate_scheme),size=(14,1)),
        sg.In(size=(25,1), enable_events=True,expand_y=False,tooltip=translate_text('Output publish directory. Default: `analysis-2022-XX-YY`',language,translate_scheme), key='-PUBLISH DIR-',),
        ],
        [
        sg.Text(translate_text('Output Prefix',language,translate_scheme),size=(14,1)),
        sg.In(size=(25,1), enable_events=True,expand_y=False,tooltip=translate_text(' Prefix of output directory & report name: Default: `analysis`',language,translate_scheme), key='-OUTPUT PREFIX-',),
        ],
        [sg.Checkbox(translate_text('no-temp',language,translate_scheme), default=False, tooltip=translate_text('Output all intermediate files. For development/ debugging purposes',language,translate_scheme), key='-NO TEMP-')],
        [sg.Checkbox(translate_text('all metadata to header',language,translate_scheme), default=False, tooltip=translate_text('Parse all fields from input barcode.csv file and include in the output fasta headers. Be aware spaces in metadata will disrupt the record id, so avoid these.',language,translate_scheme), key='-ALL META-')],
        
    ]

    """
  --datestamp DATESTAMP
                        Append datestamp to directory name when using <-o/--outdir>. Default: <-o/--outdir> without a datestamp
  --overwrite           Overwrite output directory. Default: append an incrementing number if <-o/--outdir> already exists
  -temp TEMPDIR, --tempdir TEMPDIR
                        Specify where you want the temp stuff to go. Default: `$TMPDIR`

  Misc options:
  --runname RUNNAME     Run name to appear in report. Default: Nanopore sequencing
  --username USERNAME   Username to appear in report. Default: no user name
  --institute INSTITUTE
                        Institute name to appear in report. Default: no institute name
  --orientation ORIENTATION
                        Orientation of barcodes in wells on a 96-well plate. If `well` is supplied as a column in the barcode.csv, this default orientation will be overwritten. Default: `horizontal`. Options: `horizontal` or `vertical`.
  -t THREADS, --threads THREADS
                        Number of threads. Default: 1
  --verbose             Print lots of stuff to screen
  -v, --version         show program's version number and exit
  -h, --help

                        """

    misc_options_tab = [
        [
        sg.Text(translate_text('Run Name',language,translate_scheme),size=(14,1)),
        sg.In(size=(25,1), enable_events=True,expand_y=False,tooltip=translate_text('Run name to appear in report. Default: Nanopore sequencing',language,translate_scheme), key='-RUN NAME-',),
        ],
        [sg.Checkbox('verbose', default=False, tooltip='test', key='-VERBOSE-')],
    ]

    layout = [
    [sg.TabGroup([[
        sg.Tab(translate_text('Input Options',language,translate_scheme),input_options_tab,key='-INPUT OPTIONS TAB-'),
        sg.Tab(translate_text('Analysis Options',language,translate_scheme),analysis_options_tab,key='-ANALYSIS OPTIONS TAB-'),
        sg.Tab(translate_text('Output Options',language,translate_scheme),output_options_tab,key='-OUTPUT OPTIONS TAB-'),
        sg.Tab(translate_text('Misc Options',language,translate_scheme),misc_options_tab,key='-MISC OPTIONS TAB-')
    ]])],

    [AltButton(button_text=translate_text('Confirm',language,translate_scheme),size=button_size,font=font,key='-CONFIRM-'),],
    ]

    return layout

def create_piranha_options_window(theme = 'Artifice', version = 'ARTIFICE', font = None, window = None, scale = 1):
    update_log('creating add protocol window')
    make_theme()
    layout = setup_layout(theme=theme, font=font)
    piranha_scaled = scale_image('piranha.png',scale,(64,64))
    new_window = sg.Window(version, layout, font=font, resizable=False, enable_close_attempted_event=True, finalize=True,icon=piranha_scaled)

    if window != None:
        window.close()

    AltButton.intialise_buttons(new_window)

    return new_window

def run_piranha_options_window(window, run_info, font = None, version = 'ARTIFICE'):
    config = artifice_core.consts.retrieve_config()
    selected_run_title = run_info['title']

    element_dict = {'-VERBOSE-':'--verbose'}
    run_info = load_run(window, selected_run_title, element_dict, runs_dir = config['RUNS_DIR'], update_archive_button=False)
    
    
    while True:
        event, values = window.read()

        if event != None:
            log_event(f'{event} [ window]')

        if event == 'Exit' or event == sg.WINDOW_CLOSE_ATTEMPTED_EVENT:
            window.close()
            return run_info
       
        elif event == '-CONFIRM-':
            try:
                run_info = save_changes(values, run_info, window, element_dict=element_dict, update_list = False)
                window.close()
                return run_info
            except Exception as err:
                error_popup(err, font)

    window.close()