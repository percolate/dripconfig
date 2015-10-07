"""
dumped some common stuff in here for now.
"""

from logging.config import dictConfig

from voluptuous import Schema, Coerce, Required, Optional

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
            Required('host'): basestring,
            Required('port', default=8125): Coerce(int),
            Optional('sample_rate', default=1): Coerce(int),
            Optional('disabled', default=False): bool,
        },
    })

    def configure(self, configuration):
        """
        If statsd is missing from the config, the emission of
        data will be disabled by default. Otherwise, use the provided defaults,
        or use the values specified in the config.
        """
        import statsd

        statsd_in_conf = 'statsd' in configuration
        defaults = {
            'host': 'localhost',
            'port': 8125,
            'sample_rate': 1,
            'disabled': not statsd_in_conf
        }

        if statsd_in_conf:
            for key in defaults.keys():
                if hasattr(configuration.statsd, key):
                    defaults[key] = getattr(configuration.statsd, key)

        statsd.Connection.set_defaults(**defaults)


def register_all(config):
    for Trigger in [LoggingConfig, StatsdConfig]:
        config.register_trigger(Trigger())
