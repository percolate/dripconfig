"""
dumped some common stuff in here for now.
"""

from logging.config import dictConfig

from voluptuous import Schema, Coerce, Required

from dripconfig.interfaces import ConfigurationTrigger


class LoggingConfig(ConfigurationTrigger):
    """
    just applies logging configuration via
    logging.dictconfig if it exists.

    This does not support fileConfig ini
    format.

    expects something of the form:

    {
        "logging": {
            ... as described in python docs for
            logging.config.dictConfig
        }
    }
    """

    SCHEMA = Schema({
        'logging': dict
    }, extra=True)

    def clean(self, configuration):
        return self.SCHEMA(configuration)

    def configure(self, configuration):
        if 'logging' in configuration:
            dictConfig(configuration.logging)


class StatsdConfig(ConfigurationTrigger):
    """
    Statsd configuration handler

    sets up statsd whenever there is
    a section in the configuration of the
    form:


    {
        "statsd":
        {
            "port": 8129,
            "host": "graphite.server.net"
        }
    }

    """

    # optional statsd section
    SCHEMA = Schema({
        'statsd': {
            Required('host'): basestring,
            Required('port', default=8125): Coerce(int),
        },
    }, extra=True)

    def clean(self, configuration):
        return self.SCHEMA(configuration)

    def configure(self, configuration):
        import statsd

        if 'statsd' in configuration:
            statsd.Connection.set_defaults(
                host=configuration.statsd.host,
                port=configuration.statsd.port)


def register_all(config):
    for Trigger in [LoggingConfig, StatsdConfig]:
        config.register_trigger(Trigger())

