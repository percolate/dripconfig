from logging.handlers import SysLogHandler as _SysLogHandler
from logging.handlers import DatagramHandler
from logging import Filter

from dripconfig.interfaces import ConfigurationTrigger
import os
import sys


class SchemaTrigger(ConfigurationTrigger):
    """
    Simple ConfigurationTrigger that just applies
    a Schema when clean() is called.
    """

    def __init__(self, schema):
        self.schema = schema

    def clean(self, config):
        return self.schema(config)

    def configure(self, config):
        pass


class SysLogHandler(_SysLogHandler):
    """
    A logging.handlers.SyslogHandler that
    uses the process name as the 'ident'
    field for messages emitted to syslog (as
    is common for processes to do...)

    By default, messages logged
    using logging.handlers.SyslogHandler do not
    have an ident set leading to some difficultly
    determining the originating process.
    """

    def emit(self, record):
        record.ident = os.path.basename(sys.argv[0])
        super(SysLogHandler, self).emit(record)


class StatsdHandler(DatagramHandler):

    def __init__(self, host, port):
        super(StatsdHandler, self).__init__(host, port)

    def _metric(self, record):
        return 'errors.{}.{}.{}'.format(
            record.name, record.levelname, record.funcName
        )

    def _prepare_increment(self, metric):
        return '{}:1|c'.format(metric)

    def emit(self, record):
        """
        Increment a statsd counter for the error that occurred.
        """
        try:
            s = self._prepare_increment(self._metric(record))
            self.send(s)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)


class StatsdErrorFilter(Filter):
    """
    This filter ensures that only specific errors are reported to Graphite.

    :param list list strings: inject whitelisted error signatures
    """

    def __init__(self, whitelist):
        for idx, item in enumerate(whitelist):
            whitelist[idx] = tuple(item)
        self.WHITELIST = whitelist
        super(StatsdErrorFilter, self).__init__()

    def filter(self, record):
        if (record.name, record.levelname, record.funcName) in self.WHITELIST:
            return True
        return False
