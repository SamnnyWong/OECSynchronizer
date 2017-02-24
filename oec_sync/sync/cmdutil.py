from typing import *
from update_request import UpdateRequest
from enum import Enum


class Style:
    """
    Adds style and color to strings.
    https://svn.blender.org/svnroot/bf-blender/trunk/blender/build_files/scons/
tools/bcolors.py
    """
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

    def __call__(self, text: str, *styles: List[str]) -> str:
        """
        Return a string with the given ANSI style.
        :param text: original text.
        :param styles: ANSI escape sequences.
        :return: styled string.
        """
        return Style.apply(text, *styles)

    @staticmethod
    def apply(text: str, *styles: List[str]):
        """
        Return a string with the given ANSI style.
        :param text: original text.
        :param styles: ANSI escape sequences.
        :return: styled string.
        """
        return ''.join(styles) + text + Style.ENDC

    @staticmethod
    def print(text: Any, *styles: List[str], **kwargs):
        """
        print() with text style.
        :param text: text to print
        :param styles: see Style
        """
        print(Style.apply(str(text), *styles), **kwargs)


class StyledPrint:
    """
    Pretty-printing of objects.
    """

    @staticmethod
    def update_request(req: UpdateRequest, idx: int):
        """
        Prints an update request.
        :param req: the update request object.
        :param idx: the corresponding id in the all req list
        """
        # system name
        Style.print("%-5s [%s]:" % ("%d:" % idx, req.updates.name),
                    Style.OKGREEN, Style.BOLD)
        # planets
        for planet_update in req.updates.planets:
            tag_new = ' (new planet)' if planet_update.new else ''
            Style.print("\t<%s>%s:" % (planet_update.name, tag_new),
                        Style.OKGREEN)
            # fields
            for field, value in planet_update.fields.items():
                Style.print("\t\t%-20s: " % field, Style.OKBLUE, end='')
                print(repr(value))


class CliAction(Enum):
    """
    Indicates the basic cli action to perform.
    """
    exit = 0
    stay = 1
    back = 2


class Cli:

    """
    Command line interface utilities.
    """
    @staticmethod
    def __input(msg: str):
        return input(Style.apply(msg, Style.HEADER))

    @staticmethod
    def __print(msg: str, *args, **kwargs):
        return print(Style.apply(msg, Style.HEADER), *args, **kwargs)

    @staticmethod
    def confirm(msg: str) -> bool:
        """Get a confirmation from the user."""
        while True:
            response = Cli.__input(msg + " (y/n): ").lower()
            if response == 'y':
                return True
            elif response == 'n':
                return False

    @staticmethod
    def input_int(msg: str,
                  min_val: int,
                  max_val: int,
                  on_out_of_range: Callable[[], None]=None) -> int:
        """Prompt user for an integer."""
        msg += " (%d ~ %d): " % (min_val, max_val)
        while True:
            try:
                result = int(Cli.__input(msg))
                if min_val <= result <= max_val:
                    return result
                elif on_out_of_range:
                        on_out_of_range()
            except ValueError:
                print("Please enter a valid number")
                continue

    @staticmethod
    def input_str(msg: str,
                  default: str) -> str:
        """Prompt user for a string."""
        msg += " (%s): " % default
        result = Cli.__input(msg)
        return result or default

    @staticmethod
    def menu(msg: str, opts: List[Tuple[str, Callable[[], None], CliAction]]) \
            -> bool:
        """
        Start a interactive menu.
        :param msg: Message to display above the list of options.
        :param opts: List of tuples of
            option: description of the option
            action: to perform
            state: what the Cli should do after the action
        :return: whether the session should continue
        """
        st = Style()

        def print_options():
            """Prints available options."""
            if msg:
                print(msg)
            for i in range(len(opts)):
                Cli.__print("%2d)" % i, opts[i][0])

        while True:
            print_options()
            choice = Cli.input_int("Choose an action",
                                   0,
                                   len(opts) - 1,
                                   print_options)
            desc, action, state = opts[choice]

            # perform the action
            if action is not None:
                action()

            # check state post-action
            if state == CliAction.stay:
                pass
            elif state == CliAction.back:
                return True
            elif state == CliAction.exit:
                return False
