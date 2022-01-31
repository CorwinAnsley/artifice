import consts

#update the log with a new line
def update_log(line, filename = consts.LOGFILE, overwrite = False):
    if overwrite:
        mode = 'w'
    else:
        mode = 'a'

    filepath = str(consts.get_datadir() / filename)

    #limits the length of the line to 200 characters :- DISUSED
    #if len(line) > 200:
    #    line = f'{line[0:148]}...{line[-50:]}'

    with open(filepath, mode) as f:
        f.write(line+'\n')

def log_event(input, filename = consts.LOGFILE):
    update_log(f'\nEVENT: {input}', filename)
