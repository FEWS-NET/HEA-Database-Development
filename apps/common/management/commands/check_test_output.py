import argparse
import re

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    r"""
    Clean unit test output looks like:

        Running tests...
        ----------------------------------------------------------------------
        .....................s.............................s..................
        ............s..............................s..........................
        ......................s...............................................
        ...........................................................s..........
        ----------------------------------------------------------------------
        Ran 1262 tests in 1895.420s

    If a successful unit test run always looks like this, without any additional output,
    then is it easier to pinpoint and debug test failures by looking at the output from
    the unit tests. Therefore, we have a requirement that successful tests do not generate
    any output using the normal logging configuration.

    Note that detailed test output also contains the name of each test and the duration:

        Running tests...
        ----------------------------------------------------------------------
        System check identified no issues (1 silenced).
          test_filter_access (apps.warehouse.tests.test_viewsets.DataPointViewSetTestCase) ... ok (3.777s)
          test_filter_access (apps.warehouse.tests.test_viewsets.DataSeriesViewSetTestCase) ... ok (1.683s)
          test_list_filter_by_used_for (apps.warehouse.tests.test_viewsets.DataDocumentViewSetTestCase) ... ok (2.088s)
          test_save_of_marketprice_triggers_refresh (apps.price.tests.test_models.MarketFactsCase) ... ok (22.536s)
          test_writing_unicode_in_update_file (apps.common.tests.test_resources.LoggingMixinTestCase) ... ok (0.020s)
        ----------------------------------------------------------------------
        Ran 1262 tests in 2012.205s
    """

    help = "Test that unit test output is clean"

    def add_arguments(self, parser):
        parser.add_argument("filename", type=argparse.FileType("r"))

    def handle(self, *args, **options):
        input_file = options.get("filename")
        content = input_file.read()

        # Find the test output by finding all text before the --- marker after the "Found x test(s)" header
        result = re.search(r"Found \d+ test\(s\)\.\n(.+)\n---+", content, re.DOTALL | re.MULTILINE)
        if not result:
            raise CommandError("Cannot find test output")
        test_output = result.groups()[0]

        # Prepare regex patterns for "acceptable" lines or output
        good_lines = [
            r"^Found \d+ test\(s\)\.$",
            r"^Using existing test database for alias 'default'...$",
            r"^System check identified no issues.*$",
            # Verbose output, e.g.  test_weekly_facts (apps.price.tests.test_models.MarketFactsCase) ... ok (32.194s):
            r"^  test_\w+ \([\w\.]+\) \.\.\..*?\([\d\.]+s\)$",
            # Simple output, e.g. .....................s.............................s..................
            r"^[\.s]+$",
            r"^.*Saving combined file.*$",
            r"^.*Saved combined results.*$",
            r"^$",
        ]
        good_lines = re.compile("|".join([f"({regex})" for regex in good_lines]))
        bad_lines = []
        for line_number, line in enumerate(test_output.split("\n")):
            if not good_lines.search(line):
                bad_lines.append((line_number, line))
        if bad_lines:
            self.stderr.write("Test output contains the following unexpected output:")
            for line_number, line in bad_lines:
                self.stderr.write(f"{line_number:4}: {line}")
            raise CommandError("Test output is not clean")
        self.stdout.write("Test output is clean")
