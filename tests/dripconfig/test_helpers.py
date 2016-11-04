import logging
from logging import LogRecord
import mock
import os
import sys
from unittest import TestCase

from dripconfig.helpers import (
    SysLogHandler,
    StatsdHandler,
    StatsdErrorFilter,
)


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
        with mock.patch('logging.handlers.SysLogHandler.emit') as emit:
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


class TestStatsdErrors(TestCase):

    def setUp(self):
        self.whitelist = [
            ['dummy_name', 'ERROR', 'not_used_func'],
            ['name', 'ERROR', 'func_name']
        ]

        self.record = LogRecord(
            'name',
            logging.ERROR,
            '/foo/bar.py',
            42,
            'Something Happened!',
            [],
            None,
            'func_name'
        )

    def test_StatdsHandler_sends_expected_message(self):
        with mock.patch('logging.handlers.DatagramHandler.send') as send:
            handler = StatsdHandler('foo', 'bar')
            handler.emit(self.record)

            self.assertEquals(send.call_count, 1)
            self.assertIn(
                'errors.name.ERROR.func_name', send.call_args_list[0][0][0])

    def test_StatdsErrorFilter_returns_False_if_error_not_in_WHITELIST(self):
        a_filter = StatsdErrorFilter([])  # pass in empty whitelist
        result = a_filter.filter(self.record)
        self.assertFalse(result)

    def test_StatdsErrorFilter_returns_True_if_error_in_WHITELIST(self):
        a_filter = StatsdErrorFilter(self.whitelist)
        result = a_filter.filter(self.record)
        self.assertTrue(result)
