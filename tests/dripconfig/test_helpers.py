import logging
from logging import LogRecord
import mock
import os
import sys
from unittest import TestCase

from dripconfig.helpers import SysLogHandler


class TestSysLogHelper(TestCase):

    def test_ident(self):

        record = LogRecord(
            'foo.bar',
            logging.DEBUG,
            '/foo/bar.py',
            42,
            'Something Happened!',
            [],
            None,
            'quux'
        )
        with mock.patch("logging.handlers.SysLogHandler.emit") as emit:
            handler = SysLogHandler()
            handler.emit(record)

            self.assertEquals(emit.call_count, 1)
            call = emit.call_args_list[0]
            args = call[0]
            self.assertEquals(len(args), 1)
            self.assertEquals(args[0], record)
            self.assertEquals(
                args[0].ident,
                os.path.basename(sys.argv[0])
            )
