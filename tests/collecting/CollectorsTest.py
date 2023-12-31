import logging
import os
import pkg_resources
import unittest

from functools import partial
from pyprint.ConsolePrinter import ConsolePrinter

from testfixtures import LogCapture

from coalib.bearlib.aspects import AspectList, get as get_aspect
from coalib.bears.BEAR_KIND import BEAR_KIND
from coalib.bears.Bear import Bear
from coalib.collecting.Collectors import (
    collect_all_bears_from_sections, collect_bears, collect_dirs, collect_files,
    collect_registered_bears_dirs, filter_section_bears_by_languages,
    get_all_bears, get_all_bears_names, collect_bears_by_aspects,
    get_all_languages,
    )
from coalib.output.printers.LogPrinter import LogPrinter
from coalib.output.printers.ListLogPrinter import ListLogPrinter
from coalib.settings.Section import Section
from tests.TestUtilities import (
    bear_test_module, TEST_BEAR_NAMES, LANGUAGE_NAMES,
    LANGUAGE_COUNT,
)


class CollectFilesTest(unittest.TestCase):

    def setUp(self):
        current_dir = os.path.split(__file__)[0]
        self.collectors_test_dir = os.path.join(current_dir,
                                                'collectors_test_dir')
        self.log_printer = ListLogPrinter()

    def test_file_empty(self):
        self.assertRaises(TypeError, collect_files)

    def test_file_invalid(self):
        with LogCapture() as capture:
            self.assertEqual(collect_files(file_paths=['invalid_path'],
                                           log_printer=self.log_printer,
                                           section_name='section'), [])
        capture.check(
            ('root', 'WARNING', 'No files matching \'invalid_path\' were '
                                'found. If this rule is not required, you can '
                                'remove it from section [section] in your '
                                '.coafile to deactivate this warning.')
        )

    def test_file_collection(self):
        self.assertEqual(collect_files([os.path.join(self.collectors_test_dir,
                                                     'others',
                                                     '*',
                                                     '*2.py')],
                                       self.log_printer),
                         [os.path.normcase(os.path.join(
                             self.collectors_test_dir,
                             'others',
                             'py_files',
                             'file2.py'))])

    def test_file_string_collection(self):
        self.assertEqual(collect_files(os.path.join(self.collectors_test_dir,
                                                    'others',
                                                    '*',
                                                    '*2.py'),
                                       self.log_printer),
                         [os.path.normcase(os.path.join(
                             self.collectors_test_dir,
                             'others',
                             'py_files',
                             'file2.py'))])

    def test_ignored(self):
        self.assertEqual(collect_files([os.path.join(self.collectors_test_dir,
                                                     'others',
                                                     '*',
                                                     '*2.py'),
                                        os.path.join(self.collectors_test_dir,
                                                     'others',
                                                     '*',
                                                     '*2.py')],
                                       self.log_printer,
                                       ignored_file_paths=[os.path.join(
                                           self.collectors_test_dir,
                                           'others',
                                           'py_files',
                                           'file2.py')]),
                         [])

    def test_ignored_dirs(self):
        def dir_base(*args):
            return os.path.normcase(os.path.join(self.collectors_test_dir,
                                                 'others', *args))

        files_to_check = [dir_base('*', '*2.py'),
                          dir_base('**', '*.pyc'),
                          dir_base('*', '*1.c')]
        ignore = dir_base('py_files', '')
        collect_files_partial = partial(collect_files,
                                        files_to_check)
        self.assertEqual(
            collect_files_partial(ignored_file_paths=[ignore]),
            [dir_base('c_files', 'file1.c')])
        self.assertEqual(
            collect_files_partial(ignored_file_paths=[ignore.rstrip(os.sep)]),
            [dir_base('c_files', 'file1.c')])
        self.assertEqual(
            collect_files_partial(
                ignored_file_paths=[dir_base('py_files', '**')]),
            [dir_base('c_files', 'file1.c')])
        self.assertEqual(
            collect_files_partial(
                ignored_file_paths=[dir_base('py_files', '*')]),
            [dir_base('c_files', 'file1.c')])

    def test_trailing_globstar(self):
        ignore_path1 = os.path.join(self.collectors_test_dir,
                                    'others',
                                    'c_files',
                                    '**')  # should generate warning
        ignore_path2 = os.path.join(self.collectors_test_dir,
                                    '**',
                                    'py_files',
                                    '**')  # no warning
        with LogCapture() as capture:
            collect_files(file_paths=[],
                          ignored_file_paths=[ignore_path1, ignore_path2],
                          log_printer=self.log_printer)
        capture.check(
            ('root', 'WARNING', 'Detected trailing globstar in ignore glob '
                                f'\'{ignore_path1}\'. '
                                'Please remove the unnecessary \'**\''
                                ' from its end.')
        )

    def test_limited(self):
        self.assertEqual(
            collect_files([os.path.join(self.collectors_test_dir,
                                        'others',
                                        '*',
                                        '*py')],
                          self.log_printer,
                          limit_file_paths=[os.path.join(
                                                self.collectors_test_dir,
                                                'others',
                                                '*',
                                                '*2.py')]),
            [os.path.normcase(os.path.join(self.collectors_test_dir,
                                           'others',
                                           'py_files',
                                           'file2.py'))])


class CollectDirsTest(unittest.TestCase):

    def setUp(self):
        current_dir = os.path.split(__file__)[0]
        self.collectors_test_dir = os.path.join(current_dir,
                                                'collectors_test_dir')

    def test_dir_empty(self):
        self.assertRaises(TypeError, collect_dirs)

    def test_dir_invalid(self):
        self.assertEqual(collect_dirs(['invalid_path']), [])

    def test_dir_collection(self):
        self.assertEqual(
            sorted(i for i in
                   collect_dirs([os.path.join(self.collectors_test_dir,
                                              '**')])
                   if '__pycache__' not in i),
            sorted([os.path.normcase(os.path.join(
                self.collectors_test_dir, 'bears')),
                os.path.normcase(os.path.join(self.collectors_test_dir,
                                              'bears_local_global')),
                os.path.normcase(os.path.join(self.collectors_test_dir,
                                              'others')),
                os.path.normcase(os.path.join(self.collectors_test_dir,
                                              'others',
                                              'c_files')),
                os.path.normcase(os.path.join(self.collectors_test_dir,
                                              'others',
                                              'py_files')),
                os.path.normcase(self.collectors_test_dir)]))

    def test_dir_string_collection(self):
        self.assertEqual(
            sorted(i for i in
                   collect_dirs(os.path.join(self.collectors_test_dir,
                                             '**'))
                   if '__pycache__' not in i),
            sorted([os.path.normcase(os.path.join(
                self.collectors_test_dir, 'bears')),
                os.path.normcase(os.path.join(self.collectors_test_dir,
                                              'bears_local_global')),
                os.path.normcase(os.path.join(self.collectors_test_dir,
                                              'others')),
                os.path.normcase(os.path.join(self.collectors_test_dir,
                                              'others',
                                              'c_files')),
                os.path.normcase(os.path.join(self.collectors_test_dir,
                                              'others',
                                              'py_files')),
                os.path.normcase(self.collectors_test_dir)]))

    def test_ignored(self):
        self.assertEqual(
            sorted(i for i in
                   collect_dirs([os.path.join(self.collectors_test_dir,
                                              '**')],
                                [os.path.normcase(os.path.join(
                                    self.collectors_test_dir,
                                    'others',
                                    'py_files'))])
                   if '__pycache__' not in i),

            sorted([os.path.normcase(os.path.join(
                self.collectors_test_dir, 'bears')),
                os.path.normcase(os.path.join(self.collectors_test_dir,
                                              'bears_local_global')),
                os.path.normcase(os.path.join(self.collectors_test_dir,
                                              'others')),
                os.path.normcase(os.path.join(self.collectors_test_dir,
                                              'others',
                                              'c_files')),
                os.path.normcase(self.collectors_test_dir)]))

    def test_collect_registered_bears_dirs(self):
        old_iter = pkg_resources.iter_entry_points

        def test_iter_entry_points(name):
            assert name == 'hello'

            class EntryPoint1:

                @staticmethod
                def load():
                    class PseudoPlugin:
                        __file__ = '/path1/file1'
                    return PseudoPlugin()

            class EntryPoint2:

                @staticmethod
                def load():
                    raise pkg_resources.DistributionNotFound

            return iter([EntryPoint1(), EntryPoint2()])

        pkg_resources.iter_entry_points = test_iter_entry_points
        output = sorted(collect_registered_bears_dirs('hello'))
        self.assertEqual(output, [os.path.abspath('/path1')])
        pkg_resources.iter_entry_points = old_iter


class CollectBearsTest(unittest.TestCase):

    def setUp(self):
        current_dir = os.path.split(__file__)[0]
        self.collectors_test_dir = os.path.join(current_dir,
                                                'collectors_test_dir')

        self.log_printer = ListLogPrinter()

    def test_bear_empty(self):
        self.assertRaises(TypeError, collect_bears)

    def test_bear_invalid(self):
        with LogCapture() as capture:
            self.assertEqual(collect_bears(['invalid_paths'],
                                           ['invalid_name'],
                                           ['invalid kind'],
                                           self.log_printer), ([],))
        capture.check(
            ('root', 'WARNING', 'No bears matching \'invalid_name\' were '
                                'found. Make sure you have coala-bears '
                                'installed or you have typed the name '
                                'correctly.')
        )
        self.assertEqual(collect_bears(['invalid_paths'],
                                       ['invalid_name'],
                                       ['invalid kind1', 'invalid kind2'],
                                       self.log_printer), ([], []))

    def test_simple_single(self):
        self.assertEqual(len(collect_bears(
            [os.path.join(self.collectors_test_dir, 'bears')],
            ['bear1'],
            ['kind'],
            self.log_printer)[0]), 1)

    def test_string_single(self):
        self.assertEqual(len(collect_bears(
            os.path.join(self.collectors_test_dir, 'bears'),
            ['bear1'],
            ['kind'],
            self.log_printer)[0]), 1)

    def test_reference_single(self):
        self.assertEqual(len(collect_bears(
            [os.path.join(self.collectors_test_dir, 'bears')],
            ['metabear'],
            ['kind'],
            self.log_printer)[0]), 1)

    def test_no_duplications(self):
        self.assertEqual(len(collect_bears(
            [os.path.join(self.collectors_test_dir, 'bears', '**')],
            ['*'],
            ['kind'],
            self.log_printer)[0]), 2)

    def test_wrong_kind(self):
        self.assertEqual(len(collect_bears(
            [os.path.join(self.collectors_test_dir, 'bears', '**')],
            ['*'],
            ['other_kind'],
            self.log_printer)[0]), 0)

    def test_bear_suffix(self):
        self.assertEqual(
            len(collect_bears(os.path.join(self.collectors_test_dir, 'bears'),
                              ['namebear'], ['kind'],
                              self.log_printer)[0]), 1)
        self.assertEqual(
            len(collect_bears(os.path.join(self.collectors_test_dir, 'bears'),
                              ['name'], ['kind'],
                              self.log_printer)[0]), 1)

    def test_all_bears_from_sections(self):
        test_section = Section('test_section')
        test_section.bear_dirs = lambda: os.path.join(self.collectors_test_dir,
                                                      'bears_local_global',
                                                      '**')
        local_bears, global_bears = collect_all_bears_from_sections(
            {'test_section': test_section},
            self.log_printer)

        self.assertEqual(len(local_bears['test_section']), 2)
        self.assertEqual(len(global_bears['test_section']), 2)

    def test_aspect_bear(self):
        with bear_test_module():
            aspects = AspectList([
                get_aspect('unusedglobalvariable')('py'),
                get_aspect('unusedlocalvariable')('py'),
            ])
            local_bears, global_bears = collect_bears_by_aspects(
                aspects,
                [BEAR_KIND.LOCAL, BEAR_KIND.GLOBAL])

        self.assertEqual(len(global_bears), 0)
        self.assertEqual(len(local_bears), 1)
        self.assertIs(local_bears[0].name, 'AspectTestBear')

    def test_collect_bears_unfulfilled_aspect(self):
        aspects = AspectList([
            get_aspect('unusedvariable')('py'),
        ])

        logger = logging.getLogger()
        with bear_test_module(), self.assertLogs(logger, 'WARNING') as log:
            local_bears, global_bears = collect_bears_by_aspects(
                aspects,
                [BEAR_KIND.LOCAL, BEAR_KIND.GLOBAL])
        self.assertRegex(log.output[0],
                         'coala cannot find bear that could analyze the '
                         r'following aspects: \['
                         r"'Root\.Redundancy\.UnusedVariable\.UnusedParameter'"
                         r'\]')

        self.assertEqual(global_bears, [])
        self.assertEqual(str(local_bears),
                         "[<class 'AspectTestBear.AspectTestBear'>]")


class CollectorsTests(unittest.TestCase):

    def setUp(self):
        current_dir = os.path.split(__file__)[0]
        self.collectors_test_dir = os.path.join(current_dir,
                                                'collectors_test_dir')
        self.log_printer = LogPrinter(ConsolePrinter())

    def test_filter_section_bears_by_languages(self):
        test_section = Section('test_section')
        test_section.bear_dirs = lambda: os.path.join(self.collectors_test_dir,
                                                      'bears_local_global',
                                                      '**')
        local_bears, global_bears = collect_all_bears_from_sections(
            {'test_section': test_section},
            self.log_printer)
        local_bears = filter_section_bears_by_languages(local_bears, ['C'])
        self.assertEqual(len(local_bears['test_section']), 1)
        self.assertEqual(str(local_bears['test_section'][0]),
                         "<class 'bears2.Test2LocalBear'>")

        global_bears = filter_section_bears_by_languages(global_bears, ['Java'])
        self.assertEqual(len(global_bears['test_section']), 1)
        self.assertEqual(str(global_bears['test_section'][0]),
                         "<class 'bears1.Test1GlobalBear'>")

    def test_get_all_bears(self):
        with bear_test_module():
            bears = get_all_bears()
            assert isinstance(bears, list)
            for bear in bears:
                assert issubclass(bear, Bear)
            self.assertSetEqual(
                {b.name for b in bears},
                set(TEST_BEAR_NAMES))

    def test_get_all_bears_names(self):
        with bear_test_module():
            names = get_all_bears_names()
            assert isinstance(names, list)
            self.assertSetEqual(
                set(names),
                set(TEST_BEAR_NAMES))

    def test_get_all_languages_without_unknown(self):
        with bear_test_module():
            languages = get_all_languages()
            assert isinstance(languages, tuple)
            self.assertEqual(len(languages), LANGUAGE_COUNT)
            self.assertSetEqual(
                {str(language) for language in languages},
                set(LANGUAGE_NAMES))

    def test_get_all_languages_with_unknown(self):
        with bear_test_module():
            languages = get_all_languages(include_unknown=True)
            language_names = LANGUAGE_NAMES.copy()
            language_names.append('Unknown')
            assert isinstance(languages, tuple)
            self.assertEqual(len(languages), LANGUAGE_COUNT + 1)
            self.assertSetEqual(
                {str(language) for language in languages},
                set(language_names))
