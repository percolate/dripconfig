"""
dumped some common stuff in here for now.
"""

from logging.config import dictConfig

from voluptuous import Schema, Coerce, Required, Optional, Boolean, All, Range

from dripconfig.interfaces import SchemaBasedTrigger


class LoggingConfig(SchemaBasedTrigger):
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
        },
    }

    """
    partial_schema = Schema({
        'logging': dict,
    })

    def configure(self, configuration):
        if 'logging' in configuration:
            dictConfig(configuration.logging)


class SentryConfig(SchemaBasedTrigger):
    """
    Configure a raven client to send exceptions to a sentry server.

    {
        "sentry": {
            "dsn": "http://asdf:adsf@sentry.whatever.com/",
        }
    }

    """
    partial_schema = Schema({
        'sentry': {
            Required('dsn'): basestring,
        },
    })

    def configure(self, configuration):
        if 'sentry' in configuration:
            from raven.handlers.logging import SentryHandler
            from raven.conf import setup_logging
            setup_logging(SentryHandler(configuration.sentry.dsn))


class StatsdConfig(SchemaBasedTrigger):
    """
    Statsd configuration handler

    sets up statsd whenever there is
    a section in the configuration of the
    form:

    {
        "statsd":
        {
            "port": 8129,
            "host": "graphite.server.net",
            "sample_rate": 1,
            "disabled": False
        }
    }

    """
    partial_schema = Schema({
        'statsd': {
            Required('host', default='localhost'): basestring,
            Required('port', default=8125): Coerce(int),
            Optional('sample_rate'): All(Coerce(float), Range(min=0, max=1)),
            Optional('disabled'): Boolean(basestring),
        },
    })

    def configure(self, configuration):
        import statsd
        stats_config = configuration.get('statsd', {})
        statsd.Connection.set_defaults(
            host=stats_config.get('host', 'localhost'),
            port=stats_config.get('port', 8125),
            sample_rate=stats_config.get('sample_rate', 1),
            disabled=stats_config.get('disabled', False)
        )


def register_all(config):
    for Trigger in [LoggingConfig, StatsdConfig]:
        config.register_trigger(Trigger())
