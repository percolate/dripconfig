
# dripconfig

[![CircleCI](https://circleci.com/gh/percolate/dripconfig.svg?style=svg&circle-token=80b53a2510ca246c448fd7e65c900b2102cc4e4a)](https://circleci.com/gh/percolate/dripconfig)

A tool for doing configuration nicely -- sorta.

This package has helpers for loading configuration and performing common setup
tasks, e.g. for logging, stats, and datastore machinery. It provides a
django-like singleton to consolidate configured values. It also provides
utilities for implementing lightweight [dependency
injection](http://en.wikipedia.org/wiki/Dependency_injection).

Configuration can be loaded easily from  from a variety of sources in a
seamless, polymorphic way and is checked/cleaned by registered validation
extensions (usually by section). You can load from many different sources
(JSON, INI, dict, environment variable to name a few), as well as specifying
a prioritized preference for loading (load from sys.argv if available, then
from environment variable, then finally fall back to a certain file).

## Example

```python
from dripconfig import config, sources

if __name__ == '__main__':

    # wire up a RedisTrigger instance to configure redis based on info
    config.register_trigger(RedisTrigger())

    # load some config

    config.merge_from(
        # prefer a config loaded from filename passed as argument
        sources.Argv(1),
        # if we don't have an argv, load from a file
        sources.EnvVar("CONF_FILENAME"),
        # if the env var isn't set, fall back to a particular file
        sources.Filename("some_conf.json"),
    )

    # specific values can be loaded very easily from environment variables
    config['this']['that'] = os.environ.get('THIS_THAT_VAL', 'default_val')

    # validate, run any global configuration steps, and have the triggers act
    config.configure()

    # on with the show...
```

The `RedisTrigger` definition takes the loaded configuration info and renders
it into objects that let us use redis:

```python

class RedisTrigger(ConfigurationTrigger):
    """
    Require that redis connection information is specified.

    """
    # voluptuous Schema objects are a great way of validating config.
    SCHEMA = Schema({
        'redis': {
            Required('hostname'): basestring,
            Required('realtime_updates_ss_name',
                     default='melrose:realtalk'): basestring,
        },
    }, extra=True)

    def clean(self, configuration):
        """Make sure all the required values are here."""
        if 'redis' not in configuration:
            raise RuntimeError(
                "Redis not properly configured; "
                "see `melrose.config:RedisTrigger.schema`."
            )

        # make sure we match the schema we need
        return self.SCHEMA(configuration)

    def configure(self, configuration):
        """
        Instantiate a redis client and any reliant objects.

        """
        conf = configuration.redis
        some_module.redis_client = redis.Redis(conf.hostname)

```

Meanwhile in `some_submodule`, the module-level attribute `redis_client` is
declared to be injected by dripconfig. This allows the module to be
(blissfully) unaware of the configuration needed to instantiate its
dependencies.

```python
# some_module.py

redis_client = dripconfig.ToBeInjected(redis.Redis)
```

By the time `dripconfig.configure()` is called, `redis_client` will be an
object of type `redis.Redis`, and will be ready for use. Until that call is
made, though, any attempt to use that object will result in a RuntimeError.

## Note on INI logging configurations

Note: this does not support the python logging module 'ini' configuration
format although you can load ini files.  Use logging.fileConfig on that
directly if desired.

## Sources

The preferred format is JSON for nested data (logging configuration = yuck...),
but configuration can be merged together from a variety of sources including
ini files, yamls, dicts etc.  A consolidated attribute-accessible object is
presented for triggering further configuration actions.

```
from dripconfig import config


if __name__ == '__main__':
    config.register_trigger(...)

    # `merge` will automagically determine the type
    config.merge('thisconf.yaml')
    config.merge({'yo': 'bang!'})

    # or you can do it explicitly
    config.merge_dict({'some': 'default'})
    config.merge_ini_file("/usr/local/etc/common.ini")
    config.merge_json('{"foo": "bar"}')

    # done loading, normalize and apply
    config.configure()

    # great, now get to work!
    serve(port=config.port)
```

## Validation and Global Configuration

ConfigurationTrigger objects are tasked with validating/cleaning relevent
portions of the configuration in the clean() method.  After cleaning the values
in the configuration are expected to be of the correct type, consumers should
not worry about type checking the configuration.  This is mainly a concern when
loading .ini files.

The suggested method is to declare a Voluptuous Schema and use Corece() on
numerical values and anything that may require additional interpretation.

ConfigurationTriggers can also apply portions of the configuration in a global
fashion if necesary via the configure() method.  Stats and logging are often
configured by this method.

## Note on INI Files

The best thing is that they're simple. The worst thing is they sort of stink
for the same reason and no magic to support nesting is done.  Anything in the
[main] section is considered top-level, everything else is nested under a key
with the name of the section.

## Helpers and other Tidbits

For logging configurations that use syslog, a slightly improved handler is
provided that logs the process name with outgoing messages when used
with an appropriate formatter.  The variable `ident` is provided, which
can be used as the prefix to the logging format to identify the process
to syslog eg `%(ident)s %(message)`.

An example configuration might include a handler such as the following in the
logging.dictConfig format:

```
{
    "logging": {
        "formatters": {
            ...
            "syslog": {
                "format": "%(ident)s [%(levelname)s %(asctime)s %(module)s] %(message)s"
            }
        },
        ...
        "handlers": {
            "syslog":{
                "class":"dripconfig.SysLogHandler",
                "level":"INFO",
                "formatter": "syslog",
                "address": "/dev/log"
            },
        },
        ...
    }
}
```

## TODO

* arg parse example or helper for specifying config files to load?
* some way to do email based logging without django?
* json with comments is shady, works but can't give good line-number errors,
  which stinks
