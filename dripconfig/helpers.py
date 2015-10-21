from logging.handlers import SysLogHandler as _SysLogHandler
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
