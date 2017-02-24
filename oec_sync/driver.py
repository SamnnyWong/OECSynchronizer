#!/usr/bin/python
"""
Driver

Functions supported
    #1. A the maintainer of the OEC, I want the application to fetch data
        from NASA
    #2. As the maintainer of the OEC, I want the application to produce a list
        of changes between the systems in OEC and NASA
"""
import logging.config
import os
import tempfile
from subprocess import call

from argparse import ArgumentParser
from synchronizer import Synchronizer
from update_request import UpdateRequest
from cmdutil import *
import gui.oec_main as sync_gui


LOG_CONFIG = {
    'version': 1,
    'formatters': {
        'verbose': {
            'format': '[%(asctime)s] %(levelname)s %(module)s:%(message)s'
        },
        'simple': {
            'format': '%(levelname)s: %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        }
    },
    'root': {
        # 'level': 'DEBUG',     # use this if you want to see more logs
        'level': 'INFO',
        # 'level': 'ERROR',       # display only errors
        'handlers': ['console'],
    },
}

USAGE = '''
NAME
      driver - keep OEC up-to-date with NASA and exoplanet.eu
SYNOPSIS
      driver [-h] [--cli] [--auto MAX] CONFIG_FILE
DESCRIPTION
      Fetches data from NASA, list differences between the systems
      in OEC and NASA using a configuration from CONFIG_FILE
OPTIONS
      --help    display this help and exit
      --cli     start without graphical-user interface
      --auto N  automatically synchronize and submit at most N requests,
                then exit immediately
AUTHOR
      Sam Wong, Steven Xia, Melissa Tam, Audrey Cheng, Kc Udonsi
REPORTING BUGS
      https://github.com/CSCC01-Fall2016/team09-Project/issues
COPYRIGHT
      (c) 2016 Team MASK
OpenExoplanetCatalogue                December 2016                  sync(1)'''


def get_progress_callback():
    current_tag = ['']

    def callback(current: int, total: int, tag: str=None) -> None:
        """Prints progress bar"""
        if tag is not None and current_tag[0] != tag:
            print("\n"+tag)
            current_tag[0] = tag

        total_blocks = 40
        current = max(0, min(current, total))
        filled_blocks = total_blocks * current // total
        bar = '[' + \
              '█' * filled_blocks + \
              '-' * (total_blocks-filled_blocks) + \
              ']'
        print("\r\tProgress: %s %d%%" % (bar, 100 * current // total), end='')
    return callback


def usage():
    """
    Prints usage for this tool
    :return:
    """


EDITOR = os.environ.get('EDITOR', 'vim') \
    if os.name == 'posix' \
    else ''


def select_request(syncr: Synchronizer,
                   all_requests: List[UpdateRequest]) -> None:
    """
    The subroutine to select an update request
    :param syncr: The synchronizer object.
    :param all_requests: List of all update requests.
    """
    def content_editor(content: str) -> str:
        tf_name = ""
        with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as tf:
            tf_name = tf.name
            tf.write(content.encode('utf-8'))

        if Cli.confirm("Edit the file before submission? "
                       "This will launch the default editor '%s'" % EDITOR):
            while True:
                if os.name == 'posix':
                    call([EDITOR, tf_name])
                else:
                    call(['cmd.exe', '/c', tf_name])

                if Cli.confirm("Finished editing and submit?"):
                    break

        with open(tf_name, 'r', encoding='utf-8') as f:
            new_content = f.read()
            return new_content

    def edit_request(r: UpdateRequest):
        r.title = Cli.input_str("Title", r.title)
        r.message = Cli.input_str("Message", r.message)
        r.reference = Cli.input_str("Reference", r.reference)

    while True:
        req_index = Cli.input_int("Select an update request",
                                  0,
                                  len(all_requests) - 1)
        req = all_requests[req_index]

        # preview the changes in the request
        StyledPrint.update_request(req, req_index)

        options = [
            (
                "Edit & submit",
                lambda: (
                    edit_request(req),
                    syncr.submit(req, editor=content_editor),
                    print("Created Github Pull Request #%d (%s)" %
                          (req.pullreq_num, req.pullreq_url)),
                    all_requests.pop(req_index)
                ),
                CliAction.back
            ),
            (
                "Reject",
                lambda: (
                    syncr.reject(req),
                    print("Created and closed Github Pull Request #%d "
                          "(%s)" % (req.pullreq_num, req.pullreq_url)),
                    all_requests.pop(req_index)
                ),
                CliAction.back
            ),
            ("Re-select", None, CliAction.back),
            ("Back", None, CliAction.exit)
        ]

        if not Cli.menu("", options):
            return


def sync(config_file: str, max_auto_requests: int=0):
    """
    Synchronize between OEC and NASA
    """
    local_requests = []

    def sync_callback(request: UpdateRequest):
        """Collects and display an update request"""
        local_requests.append(request)

    sync_object = Synchronizer(config_file)

    # automatic mode
    if max_auto_requests > 0:
        print("Starting auto-sync...")
        sync_object.sync(sync_callback, get_progress_callback())
        req_to_send = local_requests[:max_auto_requests]
        for req_idx, req in enumerate(req_to_send):
            try:
                print("\nSubmitting request %d...\t\t" % req_idx, end="")
                sync_object.submit(req)
                print("PR #%d (%s)" %
                      (req.pullreq_num, req.pullreq_url))
            except Exception as ex:
                logging.exception(ex)
        return

    # interactive mode
    while True:
        # start the menu
        options = [
            (
                "Discard changes and exit the program",
                None,
                CliAction.exit
            ),
            (
                "Synchronize",
                lambda: (
                    local_requests.clear(),
                    sync_object.sync(sync_callback, get_progress_callback())
                ),
                CliAction.back      # need to regenerate menu text
            ),
        ]
        if len(local_requests) > 0:
            options += [
                (
                    "List local update requests",
                    lambda: frozenset(map(
                        lambda tup: StyledPrint.update_request(tup[1], tup[0]),
                        enumerate(local_requests))
                    ),
                    CliAction.stay
                ),
                (
                    "Select a local update request",
                    lambda: select_request(sync_object, local_requests),
                    CliAction.back
                ),
            ]

        title = "\n" \
                "+======================================================+\n" \
                "|                OEC-SYNC - MAIN MENU                  |\n" \
                "+======================================================+\n"
        title = Style.apply(title, Style.HEADER, Style.BOLD) + \
            "OEC repository:  %s\n" \
            "Current user:    %s\n" \
            "Remote requests: %d\n" \
            "Local requests:  %d\n" \
            % (sync_object.db.repo.html_url,
                sync_object.db.user.login,
                len(sync_object.db.requests),
                len(local_requests))

        try:
            if not Cli.menu(title, options):
                break
        except EOFError:
            return


def main():
    """
    Runs the application
    """
    logging.config.dictConfig(LOG_CONFIG)

    parser = ArgumentParser(add_help=False)
    parser.add_argument('-h', '--help', action='store_true', default=False)
    parser.add_argument('--cli', action='store_true', default=False)
    parser.add_argument('--auto', metavar='MAX', type=int, default=0)

    parser.add_argument('CONFIG_FILE', action='store',
                        help="path to configuration", nargs='?')
    args = parser.parse_args()

    if args.help or args.CONFIG_FILE is None:
        print(USAGE)
        exit(1)
    elif args.cli:
        sync(args.CONFIG_FILE, max_auto_requests=args.auto)
    else:
        sync_gui.launch(args.CONFIG_FILE)
    exit(0)

if __name__ == '__main__':
    main()
