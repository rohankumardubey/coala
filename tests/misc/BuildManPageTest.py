import argparse
import datetime
import unittest
from distutils.errors import DistutilsOptionError

from setuptools.dist import Distribution

from coalib.misc.BuildManPage import BuildManPage, ManPageFormatter
from coala_utils.ContextManagers import make_temp

app_name = 'name'
app_description = ('short description ' * 2).strip()
app_long_description = ('long description ' * 80).strip()
section_name = 'sect'
section_text = ('section text ' * 5).strip()
sections = {section_name: section_text}


def test_arg_parser(formatter_class=argparse.RawDescriptionHelpFormatter):
    arg_parser = argparse.ArgumentParser(formatter_class=formatter_class,
                                         prog=app_name,
                                         description=app_description)
    arg_parser.add_argument('arg1')
    arg_parser.add_argument('-a')

    return arg_parser


class ManPageFormatterTest(unittest.TestCase):

    def test_format_functions(self):
        self.assertEqual(ManPageFormatter._markup('a-b'), 'a\\-b')
        self.assertEqual(ManPageFormatter._underline('test'), '\\fItest\\fR')
        self.assertEqual(ManPageFormatter._bold('test'), '\\fBtest\\fR')
        self.assertEqual(ManPageFormatter._bold('\\fBtest'), '\\fBtest\\fR')
        self.assertEqual(ManPageFormatter._bold('test\\fR'), '\\fBtest\\fR')

    def test_mk_title(self):
        uut = ManPageFormatter(app_name, parser=test_arg_parser())
        today = datetime.date.today().strftime('%Y\\-%m\\-%d')
        self.assertEqual(uut._mk_title(),
                         f'.TH {app_name} {1} {today}\n')

    def test_mk_name(self):
        uut = ManPageFormatter(app_name, parser=test_arg_parser())
        self.assertEqual(uut._mk_name(),
                         f'.SH NAME\n{app_name}\n')

    def test_mk_synopsis(self):
        uut = ManPageFormatter(app_name, parser=test_arg_parser())
        self.assertEqual(
            uut._mk_synopsis(),
            f'.SH SYNOPSIS\n \\fB{app_name}\\fR [-h] [-a A] arg1\n\n\n')

    def test_mk_description(self):
        uut = ManPageFormatter(app_name,
                               parser=test_arg_parser())
        self.assertEqual(uut._mk_description(), '')
        uut = ManPageFormatter(app_name,
                               parser=test_arg_parser(),
                               long_desc=app_long_description)
        self.assertEqual(uut._mk_description(),
                         f'.SH DESCRIPTION\n{app_long_description}\n')

    def test_mk_options(self):
        uut = ManPageFormatter(app_name, parser=test_arg_parser())
        self.assertEqual(uut._mk_options(),
                         '.SH OPTIONS\n'
                         '  arg1\n\n'
                         '  -h, --help  show this help message and exit\n'
                         '  -a A\n')

    def test_mk_footer(self):
        uut = ManPageFormatter(app_name, ext_sections=sections)
        self.assertEqual(uut._mk_footer(),
                         f'.SH {section_name.upper()}\n {section_text}')
        uut = ManPageFormatter(app_name, ext_sections=None)
        self.assertEqual(uut._mk_footer(), '')

    def test_formatter(self):
        parser = test_arg_parser(ManPageFormatter)
        self.assertEqual(
            parser.format_help(),
            f'usage: {app_name} [-h] [-a A] arg1\n\n{app_description}\n\n'
            'positional arguments:\n'
            '  arg1\n\n'
            'optional arguments:\n'
            '  \\fB-h\\fR, \\fB--help\\fR\n'
            '                        show this help message and exit\n'
            '  \\fB-a\\fR \\fIA\\fR\n')

        parser = ManPageFormatter(app_name,
                                  parser=argparse.ArgumentParser(
                                      prog=app_name))
        today = datetime.date.today().strftime('%Y\\-%m\\-%d')
        self.assertEqual(parser.format_man_page(),
                         f'.TH {app_name} 1 {today}\n'
                         '.SH NAME\n'
                         f'{app_name}\n'
                         '.SH SYNOPSIS\n'
                         ' \\fBname\\fR [-h]\n\n\n'
                         '.SH OPTIONS\n'
                         '  -h, --help  show this help message and exit\n')


class BuildManPageTest(unittest.TestCase):

    def test_finalize_options(self):
        dist = Distribution()
        uut = BuildManPage(dist)
        self.assertRaises(DistutilsOptionError, uut.finalize_options)
        with make_temp() as uut.output:
            self.assertRaises(DistutilsOptionError, uut.finalize_options)
            uut.parser = 'tests.misc.BuildManPageTest:test_arg_parser'

            uut.finalize_options()
            self.assertIsInstance(uut._parser, argparse.ArgumentParser)

            uut.run()
            with open(uut.output) as file:
                result = file.read(1000)

            today = datetime.date.today().strftime('%Y\\-%m\\-%d')
            self.assertEqual(result,
                             f""".TH {app_name} 1 {today}
.SH NAME
{app_name}
.SH SYNOPSIS
 \\fB{app_name}\\fR [-h] [-a A] arg1


.SH DESCRIPTION
UNKNOWN
.SH OPTIONS
  arg1

  \\fB-h\\fR, \\fB--help\\fR
                        show this help message and exit
  \\fB-a\\fR \\fIA\\fR
.SH LICENSE
 UNKNOWN
.SH MAINTAINER(S)
 UNKNOWN
.SH SEE ALSO
 Online documentation: UNKNOWN""")
