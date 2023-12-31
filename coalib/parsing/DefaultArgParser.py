import argparse
import os

from coalib.misc import Constants
from coalib.parsing.filters import available_filters

# argcomplete is a delayed optional import
# This variable may be None, the module, or False
argcomplete = None


class CustomFormatter(argparse.RawDescriptionHelpFormatter):
    """
    A Custom Formatter that will keep the metavars in the usage but remove them
    in the more detailed arguments section.
    """

    def _format_action_invocation(self, action):
        if not action.option_strings:
            # For arguments that don't have options strings
            metavar, = self._metavar_formatter(action, action.dest)(1)
            return metavar
        else:
            # Option string arguments (like "-f, --files")
            parts = action.option_strings
            return ', '.join(parts)


class PathArg(str):
    """
    Uni(xi)fying OS-native directory separators in path arguments.

    Removing the pain from interactively using coala in a Windows cmdline,
    because backslashes are interpreted as escaping syntax and therefore
    removed when arguments are turned into coala settings

    >>> import os
    >>> PathArg(os.path.join('path', 'with', 'separators'))
    'path/with/separators'
    """

    def __new__(cls, path):
        return str.__new__(cls, path.replace(os.path.sep, '/'))


def default_arg_parser(formatter_class=None):
    """
    This function creates an ArgParser to parse command line arguments.

    :param formatter_class: Formatting the arg_parser output into a specific
                            form. For example: In the manpage format.
    """
    formatter_class = (CustomFormatter if formatter_class is None
                       else formatter_class)

    description = """
coala provides a common command-line interface for linting and fixing all your
code, regardless of the programming languages you use.

To find out what kind of analysis coala offers for the languages you use, visit
http://coala.io/languages, or run::

    $ coala --show-bears --filter-by language C Python

To perform code analysis, simply specify the analysis routines (bears) and the
files you want it to run on, for example:

    spaceBear::

            $ coala --bears SpaceConsistencyBear --files **.py

coala can also automatically fix your code:

    spacePatchBear::

            $ coala --bears SpaceConsistencyBear --files **.py --apply-patches

To run coala without user interaction, run the `coala --non-interactive`,
`coala --json` and `coala --format` commands.
"""

    arg_parser = argparse.ArgumentParser(
        formatter_class=formatter_class,
        prog='coala',
        description=description,
        # Use our own help so that we can put it in the group we want
        add_help=False)

    arg_parser.add_argument('TARGETS',
                            nargs='*',
                            help='sections to be executed exclusively')

    info_group = arg_parser.add_argument_group('Info')

    info_group.add_argument('-h',
                            '--help',
                            action='help',
                            help='show this help message and exit')

    info_group.add_argument('-v',
                            '--version',
                            action='version',
                            version=Constants.VERSION)

    mode_group = arg_parser.add_argument_group('Mode')

    mode_group.add_argument(
        '-C', '--non-interactive', const=True, action='store_const',
        help='run coala in non interactive mode')

    mode_group.add_argument(
        '--ci', action='store_const', dest='non_interactive', const=True,
        help='continuous integration run, alias for `--non-interactive`')

    mode_group.add_argument(
        '--json', const=True, action='store_const',
        help='mode in which coala will display output as json')

    mode_group.add_argument(
        '--format', const=True, nargs='?', metavar='STR',
        help='output results with a custom format string, e.g. '
             '"Message: {message}"; possible placeholders: '
             'id, origin, file, line, end_line, column, end_column, '
             'severity, severity_str, message, message_base, '
             'message_arguments, affected_code, source_lines')

    config_group = arg_parser.add_argument_group('Configuration')

    config_group.add_argument(
        '-c', '--config', type=PathArg, nargs=1, metavar='FILE',
        help=('configuration file to be used, defaults to '
              f'{Constants.local_coafile}'))

    config_group.add_argument(
        '-F', '--find-config', action='store_const', const=True,
        help=(f'find {Constants.local_coafile} '
              'in ancestors of the working directory'))

    config_group.add_argument(
        '-I', '--no-config', const=True, action='store_const',
        help='run without using any config file')

    config_group.add_argument(
        '-s', '--save', type=PathArg, nargs='?', const=True, metavar='FILE',
        help='save used arguments to a config file to a '
             f'{Constants.local_coafile}, the given path, '
             'or at the value of -c')

    config_group.add_argument(
        '--disable-caching', const=True, action='store_const',
        help='run on all files even if unchanged')
    config_group.add_argument(
        '--flush-cache', const=True, action='store_const',
        help='rebuild the file cache')
    config_group.add_argument(
        '--no-autoapply-warn', const=True, action='store_const',
        help='turn off warning about patches not being auto applicable')

    inputs_group = arg_parser.add_argument_group('Inputs')

    bears = inputs_group.add_argument(
        '-b', '--bears', nargs='+', metavar='NAME',
        help='names of bears to use')

    inputs_group.add_argument(
        '-f', '--files', type=PathArg, nargs='+', metavar='FILE',
        help='files that should be checked')

    inputs_group.add_argument(
        '-i', '--ignore', type=PathArg, nargs='+', metavar='FILE',
        help='files that should be ignored')

    inputs_group.add_argument(
        '--limit-files', type=PathArg, nargs='+', metavar='FILE',
        help="filter the `--files` argument's matches further")

    inputs_group.add_argument(
        '-d', '--bear-dirs', type=PathArg, nargs='+', metavar='DIR',
        help='additional directories which may contain bears')

    outputs_group = arg_parser.add_argument_group('Outputs')

    outputs_group.add_argument(
        '-V', '--verbose', action='store_const',
        dest='log_level', const='DEBUG',
        help='alias for `-L DEBUG`')

    outputs_group.add_argument(
        '-L', '--log-level', nargs=1,
        choices=['ERROR', 'INFO', 'WARNING', 'DEBUG'], metavar='ENUM',
        help='set log output level to DEBUG/INFO/WARNING/ERROR, '
             'defaults to INFO')

    outputs_group.add_argument(
        '-m', '--min-severity', nargs=1,
        choices=('INFO', 'NORMAL', 'MAJOR'), metavar='ENUM',
        help='set minimal result severity to INFO/NORMAL/MAJOR')

    outputs_group.add_argument(
        '-N', '--no-color', const=True, action='store_const',
        help='display output without coloring (excluding logs)')

    outputs_group.add_argument(
        '-B', '--show-bears', const=True, action='store_const',
        help='list all bears')

    outputs_group.add_argument(
        '-l', '--filter-by-language', nargs='+', metavar='LANG',
        help='filters `--show-bears` by the given languages')

    joined_available_filters = ', '.join(sorted(available_filters))
    outputs_group.add_argument(
        '--filter-by', action='append', nargs='+',
        metavar=('FILTER_NAME FILTER_ARG', 'FILTER_ARG'),
        help='filters `--show-bears` by the filter given as argument. '
             f'Available filters: {joined_available_filters}')

    outputs_group.add_argument(
        '-p', '--show-capabilities', nargs='+', metavar='LANG',
        help='show what coala can fix and detect for the given languages')

    outputs_group.add_argument(
        '-D', '--show-description', const=True, action='store_const',
        help='show bear descriptions for `--show-bears`')

    outputs_group.add_argument(
        '--show-settings', const=True, action='store_const',
        help='show bear settings for `--show-bears`')

    outputs_group.add_argument(
        '--show-details', const=True, action='store_const',
        help='show bear details for `--show-bears`')

    outputs_group.add_argument(
        '--log-json', const=True, action='store_const',
        help='output logs as json along with results'
             ' (must be called with --json)')

    outputs_group.add_argument(
        '-o', '--output', type=PathArg, nargs=1, metavar='FILE',
        help='write results to the given file (must be called with --json)')

    outputs_group.add_argument(
        '-r', '--relpath', nargs='?', const=True,
        help='return relative paths for files (must be called with --json)')

    devtool_exclusive_group = arg_parser.add_mutually_exclusive_group()

    devtool_exclusive_group.add_argument(
        '--debug-bears', nargs='?', const=True,
        help='Enable bear debugging with pdb, that can help to identify and'
        ' correct errors in bear code. Steps into bear code as soon as being'
        ' executed. To specify which bears to debug, supply bear names as'
        ' additional arguments. If used without arguments, all bears specified'
        ' with --bears will be debugged (even implicit dependency bears).')

    devtool_exclusive_group.add_argument(
        '--profile', nargs='?', const=True,
        help='Enable bear profiling with cProfile. To specify where to dump the'
        ' profiled files, supply the directory path. If specified directory'
        ' does not exist it will be created. If the specified path points to an'
        ' already existing file a error is raised. All bears (even'
        ' implicit dependency bears) in a section will be profiled. Profiled'
        ' data files will have a name format'
        ' ``{section.name}_{bear.name}.prof``.')

    misc_group = arg_parser.add_argument_group('Miscellaneous')

    misc_group.add_argument(
        '-S', '--settings', nargs='+', metavar='SETTING',
        help='arbitrary settings in the form of section.key=value')

    misc_group.add_argument(
        '-a', '--apply-patches', action='store_const',
        dest='default_actions', const='**: ApplyPatchAction',
        help='apply all patches automatically if possible')

    misc_group.add_argument(
        '-j', '--jobs', type=int,
        help='number of jobs to use in parallel')

    misc_group.add_argument(
        '-n', '--no-orig', const=True, action='store_const',
        help="don't create .orig backup files before patching")

    misc_group.add_argument(
        '-A', '--single-action', const=True, action='store_const',
        help='apply a single action for all results')

    misc_group.add_argument(
        '--debug', const=True, action='store_const',
        help='run coala in debug mode, starting ipdb, '
             'which must be separately installed, '
             'on unexpected internal exceptions '
             '(implies --verbose)')

    global argcomplete
    if argcomplete is None:
        try:
            # Auto completion should be optional, because of somewhat
            # complicated setup.
            import argcomplete
            argcomplete.autocomplete(arg_parser)
        except ImportError:
            argcomplete = False

        if argcomplete:
            try:
                from coalib.collecting.Collectors import (
                    _argcomplete_bears_names)
            except ImportError:
                pass
            else:
                bears.completer = _argcomplete_bears_names

    return arg_parser
