import logging
import queue
import unittest
from contextlib import contextmanager, ExitStack
from unittest.mock import patch

from coalib.bearlib.abstractions.LinterClass import LinterClass
from coalib.testing.BearTestHelper import generate_skip_decorator
from coalib.bears.LocalBear import LocalBear
from coala_utils.Comparable import Comparable
from coala_utils.ContextManagers import prepare_file
from coalib.settings.Section import Section
from coalib.settings.Setting import Setting


@contextmanager
def execute_bear(bear, *args, **kwargs):
    try:
        console_output = []

        # For linters provide additional information, such as
        # stdout and stderr.
        with ExitStack() as stack:
            if isinstance(bear, LinterClass):
                old_process_output = bear.process_output
                old_create_arguments = bear.create_arguments

                def new_create_arguments(filename, file, config_file,
                                         *args, **kwargs):
                    arguments = old_create_arguments(filename, file,
                                                     config_file, *args,
                                                     **kwargs)
                    console_output.append(
                        'Program arguments:\n' + repr(arguments))

                    return arguments

                def new_process_output(output, filename=None, file=None,
                                       **process_output_kwargs):

                    console_output.append('The program yielded '
                                          'the following output:\n')
                    if isinstance(output, tuple):
                        stdout, stderr = output
                        console_output.append('Stdout:\n' + stdout)
                        console_output.append('Stderr:\n' + stderr)
                    else:
                        console_output.append(output)
                    return old_process_output(output, filename, file,
                                              **process_output_kwargs)

                stack.enter_context(patch.object(
                    bear, 'process_output', wraps=new_process_output))

                stack.enter_context(patch.object(
                    bear, 'create_arguments', wraps=new_create_arguments))

            bear_output_generator = bear.execute(*args, **kwargs)

        assert bear_output_generator is not None, (
            'Bear returned None on execution\n')
        yield bear_output_generator
    except Exception as err:
        msg = []
        while not bear.message_queue.empty():
            msg.append(bear.message_queue.get().message)
        msg += console_output
        raise AssertionError(str(err) + ''.join('\n' + m for m in msg))


def get_results(local_bear,
                lines,
                filename=None,
                force_linebreaks=True,
                create_tempfile=True,
                tempfile_kwargs={},
                settings={},
                aspects=None,
                ):
    if local_bear.BEAR_DEPS:
        # Get results of bear's dependencies first
        deps_results = dict()
        for bear in local_bear.BEAR_DEPS:
            uut = bear(local_bear.section, queue.Queue())
            deps_results[bear.name] = get_results(uut,
                                                  lines,
                                                  filename,
                                                  force_linebreaks,
                                                  create_tempfile,
                                                  tempfile_kwargs,
                                                  settings,
                                                  aspects,
                                                  )
    else:
        deps_results = None

    with prepare_file(lines, filename,
                      force_linebreaks=force_linebreaks,
                      create_tempfile=create_tempfile,
                      tempfile_kwargs=tempfile_kwargs) as (file, fname):
        with execute_bear(local_bear, fname, file,
                          dependency_results=deps_results,
                          **local_bear.get_metadata().filter_parameters(
                              settings)) as bear_output:
            return bear_output


class LocalBearTestHelper(unittest.TestCase):
    """
    This is a helper class for simplification of testing of local bears.

    Please note that all abstraction will prepare the lines so you don't need
    to do that if you use them.

    If you miss some methods, get in contact with us, we'll be happy to help!
    """

    def assertComparableObjectsEqual(self, observed_result, expected_result):
        if len(observed_result) == len(expected_result):
            messages = ''
            for observed, expected in zip(observed_result, expected_result):
                if (isinstance(observed, Comparable)
                    and isinstance(expected, Comparable)) and (
                            type(observed) is type(expected)):
                    for attribute in type(observed).__compare_fields__:
                        try:
                            self.assertEqual(
                                getattr(observed, attribute),
                                getattr(expected, attribute),
                                msg=f'{attribute} mismatch.')
                        except AssertionError as ex:
                            messages += (str(ex) + '\n\n')
                else:
                    self.assertEqual(observed_result, expected_result)
            if messages:
                raise AssertionError(messages)
        else:
            self.assertEqual(observed_result, expected_result)

    def check_validity(self,
                       local_bear,
                       lines,
                       filename=None,
                       valid=True,
                       force_linebreaks=True,
                       create_tempfile=True,
                       tempfile_kwargs={},
                       settings={},
                       aspects=None,
                       ):
        """
        Asserts that a check of the given lines with the given local bear
        either yields or does not yield any results.

        :param local_bear:       The local bear to check with.
        :param lines:            The lines to check. (List of strings)
        :param filename:         The filename, if it matters.
        :param valid:            Whether the lines are valid or not.
        :param force_linebreaks: Whether to append newlines at each line
                                 if needed. (Bears expect a \\n for every line)
        :param create_tempfile:  Whether to save lines in tempfile if needed.
        :param tempfile_kwargs:  Kwargs passed to tempfile.mkstemp().
        :param aspects:          A list of aspect objects along with the name
                                 and value of their respective tastes.
        """
        if valid:
            self.check_results(local_bear, lines,
                               results=[], filename=filename,
                               check_order=True,
                               force_linebreaks=force_linebreaks,
                               create_tempfile=create_tempfile,
                               tempfile_kwargs=tempfile_kwargs,
                               settings=settings,
                               aspects=aspects,
                               )
        else:
            return self.check_invalidity(local_bear, lines,
                                         filename=filename,
                                         force_linebreaks=force_linebreaks,
                                         create_tempfile=create_tempfile,
                                         tempfile_kwargs=tempfile_kwargs,
                                         settings=settings,
                                         aspects=aspects,
                                         )

    def check_invalidity(self,
                         local_bear,
                         lines,
                         filename=None,
                         force_linebreaks=True,
                         create_tempfile=True,
                         tempfile_kwargs={},
                         settings={},
                         aspects=None,
                         ):
        """
        Asserts that a check of the given lines with the given local bear
        yields results.

        :param local_bear:       The local bear to check with.
        :param lines:            The lines to check. (List of strings)
        :param filename:         The filename, if it matters.
        :param force_linebreaks: Whether to append newlines at each line
                                 if needed. (Bears expect a \\n for every line)
        :param create_tempfile:  Whether to save lines in tempfile if needed.
        :param tempfile_kwargs:  Kwargs passed to tempfile.mkstemp().
        :param aspects:          A list of aspect objects along with the name
                                 and value of their respective tastes.
        """
        assert isinstance(self, unittest.TestCase)
        self.assertIsInstance(local_bear,
                              LocalBear,
                              msg='The given bear is not a local bear.')
        self.assertIsInstance(lines,
                              (list, tuple),
                              msg='The given lines are not a list.')

        bear_output = get_results(local_bear, lines,
                                  filename=filename,
                                  force_linebreaks=force_linebreaks,
                                  create_tempfile=create_tempfile,
                                  tempfile_kwargs=tempfile_kwargs,
                                  settings=settings,
                                  aspects=aspects,
                                  )
        msg = (f"The local bear '{local_bear.__class__.__name__}'"
               'yields no result although it '
               'should.')
        self.assertNotEqual(len(bear_output), 0, msg=msg)
        return bear_output

    def check_results(self,
                      local_bear,
                      lines,
                      results,
                      filename=None,
                      check_order=False,
                      force_linebreaks=True,
                      create_tempfile=True,
                      tempfile_kwargs={},
                      settings={},
                      aspects=None,
                      ):
        """
        Asserts that a check of the given lines with the given local bear does
        yield exactly the given results.

        :param local_bear:       The local bear to check with.
        :param lines:            The lines to check. (List of strings)
        :param results:          The expected list of results.
        :param filename:         The filename, if it matters.
        :param check_order:      Whether to check that the elements of
                                 ``results`` and that of the actual list
                                 generated are in the same order or not.
        :param force_linebreaks: Whether to append newlines at each line
                                 if needed. (Bears expect a \\n for every line)
        :param create_tempfile:  Whether to save lines in tempfile if needed.
        :param tempfile_kwargs:  Kwargs passed to tempfile.mkstemp().
        :param settings:         A dictionary of keys and values (both strings)
                                 from which settings will be created that will
                                 be made available for the tested bear.
        :param aspects:          A list of aspect objects along with the name
                                 and value of their respective tastes.
        """
        assert isinstance(self, unittest.TestCase)
        self.assertIsInstance(local_bear,
                              LocalBear,
                              msg='The given bear is not a local bear.')
        self.assertIsInstance(lines,
                              (list, tuple),
                              msg='The given lines are not a list.')
        self.assertIsInstance(results,
                              list,
                              msg='The given results are not a list.')

        bear_output = get_results(local_bear, lines,
                                  filename=filename,
                                  force_linebreaks=force_linebreaks,
                                  create_tempfile=create_tempfile,
                                  tempfile_kwargs=tempfile_kwargs,
                                  settings=settings,
                                  aspects=aspects,
                                  )
        if not check_order:
            self.assertComparableObjectsEqual(
                sorted(bear_output), sorted(results))
        else:
            self.assertComparableObjectsEqual(bear_output, results)

        return bear_output

    def check_line_result_count(self,
                                local_bear,
                                lines,
                                results_num,
                                filename=None,
                                force_linebreaks=True,
                                create_tempfile=True,
                                tempfile_kwargs={},
                                settings={},
                                aspects=None,
                                ):
        """
        Check many results for each line.

        :param local_bear:       The local bear to check with.
        :param lines:            The lines to check. (List of strings)
        :param results_num:      The expected list of many results each line.
        :param filename:         The filename, if it matters.
        :param force_linebreaks: Whether to append newlines at each line
                                 if needed. (Bears expect a \\n for every line)
        :param create_tempfile:  Whether to save lines in tempfile if needed.
        :param tempfile_kwargs:  Kwargs passed to tempfile.mkstemp().
        :param settings:         A dictionary of keys and values (both strings)
                                 from which settings will be created that will
                                 be made available for the tested bear.
        :param aspects:          A list of aspect objects along with the name
                                 and value of their respective tastes.
        """

        modified_lines = []
        for line in lines:
            stripped_line = line.strip()
            if stripped_line == '' or stripped_line.startswith('#'):
                continue
            modified_lines.append(line)

        for line, num in zip(modified_lines, results_num):
            bear_output = get_results(local_bear, [line],
                                      filename=filename,
                                      force_linebreaks=force_linebreaks,
                                      create_tempfile=create_tempfile,
                                      tempfile_kwargs=tempfile_kwargs,
                                      settings=settings,
                                      aspects=aspects,
                                      )
            self.assertEqual(num, len(bear_output))


def verify_local_bear(bear,
                      valid_files,
                      invalid_files,
                      filename=None,
                      settings={},
                      aspects=None,
                      force_linebreaks=True,
                      create_tempfile=True,
                      timeout=None,
                      tempfile_kwargs={}):
    """
    Generates a test for a local bear by checking the given valid and invalid
    file contents. Simply use it on your module level like:

    YourTestName = verify_local_bear(YourBear, (['valid line'],),
                                     (['invalid line'],))

    :param bear:             The Bear class to test.
    :param valid_files:      An iterable of files as a string list that won't
                             yield results.
    :param invalid_files:    An iterable of files as a string list that must
                             yield results.
    :param filename:         The filename to use for valid and invalid files.
    :param settings:         A dictionary of keys and values (both string) from
                             which settings will be created that will be made
                             available for the tested bear.
    :param aspects:          A list of aspect objects along with the name
                             and value of their respective tastes.
    :param force_linebreaks: Whether to append newlines at each line
                             if needed. (Bears expect a \\n for every line)
    :param create_tempfile:  Whether to save lines in tempfile if needed.
    :param timeout:          Unused.  Use pytest-timeout or similar.
    :param tempfile_kwargs:  Kwargs passed to tempfile.mkstemp() if tempfile
                             needs to be created.
    :return:                 A unittest.TestCase object.
    """
    if timeout:
        logging.warning('timeout is ignored as the timeout set in the repo '
                        'configuration will be sufficient. Use pytest-timeout '
                        'or similar to achieve same result.')

    @generate_skip_decorator(bear)
    class LocalBearTest(LocalBearTestHelper):

        def setUp(self):
            self.section = Section('name')
            self.uut = bear(self.section,
                            queue.Queue())
            for name, value in settings.items():
                self.section.append(Setting(name, value))
            if aspects:
                self.section.aspects = aspects

        def test_valid_files(self):
            self.assertIsInstance(valid_files, (list, tuple))
            for file in valid_files:
                self.check_validity(self.uut,
                                    file.splitlines(keepends=True),
                                    filename,
                                    valid=True,
                                    force_linebreaks=force_linebreaks,
                                    create_tempfile=create_tempfile,
                                    tempfile_kwargs=tempfile_kwargs)

        def test_invalid_files(self):
            self.assertIsInstance(invalid_files, (list, tuple))
            for file in invalid_files:
                self.check_validity(self.uut,
                                    file.splitlines(keepends=True),
                                    filename,
                                    valid=False,
                                    force_linebreaks=force_linebreaks,
                                    create_tempfile=create_tempfile,
                                    tempfile_kwargs=tempfile_kwargs)

    return LocalBearTest
