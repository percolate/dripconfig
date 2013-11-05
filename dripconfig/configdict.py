"""
"""
import copy
from collections import OrderedDict
import json
from types import (
    BooleanType, DictType, FloatType, IntType,
    ListType, LongType, StringType, TupleType, UnicodeType)
from UserDict import UserDict, DictMixin
from UserList import UserList

import configparser
from jsmin import jsmin


class ConfigDict(OrderedDict):
    """
    Class that hold the configuration information.

    * may be accessed as a dict or via attributes like
      django settings or javascript et al.

    * allows 'merging' additional configuration overlays
      via nested partial updates. (ie the union of keys in
      will result.  does not merge to lists) example:

      {'foo': 12, 'bar': {'quux': 3, 'baz': 4}}


    The ConfigDict is mainly meant to store 'plain old data'
    strings, numbers, lists, dicts.

    Notes:

        * any 'real' attributes on the config dict override those
          loaded by configuration

        * various `merge_` calls allow loading validated settings in a way
          that allows for nested attribute access and paritial updates
          to nested structures.  These are preferred over directly mutating
          the configuration whenever it is reasonable to do so.

        * direct attribute setting does not transform or validate
          the data set.

        * this is not magical, if you assign garbage or directly put
          other types into this nothing special will happen except
          confusion.

        * being a dict, presumably full of plain data, you are within
          rights to serialize this as json, yaml or whatever you feel like.
    """

    def __init__(self, *args, **kwargs):
        super(ConfigDict, self).__init__(*args, **kwargs)
        self._triggers = []

    @classmethod
    def from_dict(self, cfg):
        """
        create a nested ConfigDict from a plain dictionary.
        """
        return configify(cfg)

    def merge_from(self, *sources):
        """
        Merges configuration from the first source that actually contains
        usable data. Precedence is given in the order
        that the arguments are passed.

        Args:
            sources ([source.ConfigSource, ...]): ordered list of sources.
                First usable source will be used.

        Usage:

            >>> config.merge_from(
                    sources.Argv(1),
                    sources.EnvVar("MELROSE_CONF"),
                    sources.Filename("settings.ini"),
                )

        See also:
            `dripconfig.sources`

        """
        source_to_use = None

        for source in sources:
            if source.is_usable:
                source_to_use = source
                break

        if source_to_use:
            self.merge(source_to_use.filename)
        else:
            raise RuntimeError("No valid configuration sources found")

    def merge(self, thing):
        """
        Merge configuration based on dynamic detection.

        Args:
            thing (object): the thing to be merged.

        """
        if isinstance(thing, dict):
            return self.merge_dict(thing)
        elif isinstance(thing, configparser.ConfigParser):
            return self.merge_configparser(thing)
        elif isinstance(thing, basestring):
            if thing.endswith('ini'):
                return self.merge_ini_file(thing)
            elif thing.endswith('json'):
                return self.merge_json_file(thing)

            try:
                return self.merge_json(thing)
            except:
                pass

            try:
                return self.merge_yaml(thing)
            except:
                pass

        raise ValueError(
            "Couldn't merge %s of type %s" % (thing, type(thing))
        )

    def merge_dict(self, cfg):
        """
        Update configuration by setting values from the configuration
        dictionary given.  Nested dictionaries are *updated* not replaced.

        Args:
            cfg (dict): dictionary of configuration information to merge
        """
        self._merge_dict(cfg)

    def merge_configparser(self, cfg):
        """
        merge configuration from a configparser.ConfigParser
        object.

        Any options in the [main] section will be applied
        at the top level.  All others will be namespaced
        by section. eg:

        [main]
        x = y

        [foo]
        bar = quux

        would evaluate to:

        {'x': 'y',
         'foo': {
            'bar': 'quux'
        }}

        Args:
            cfg (configparser.ConfigParser): parsed configuration
                object.
        """

        # merge the main section directly
        if cfg.has_section('main'):
            cfg_dict = OrderedDict(cfg['main'])
        else:
            cfg_dict = {}

        # namespace all other sections
        for section in cfg.sections():
            if section == 'main':
                continue
            else:
                cfg_dict[section] = OrderedDict(cfg[section])

        self.merge_dict(cfg_dict)

    def merge_json(self, json_string):
        """
        merge configuration from a json string.

        The string may also contain javascript style comments.
        Although the json spec does not allow these, they are
        stripped before parsing.
        """
        cfg = json.loads(jsmin(json_string), object_hook=OrderedDict)
        self.merge_dict(cfg)

    def merge_json_file(self, json_filename):
        """
        Merge json configuration from a filename.

        """
        with open(json_filename, 'r') as f:
            return self.merge_json(f.read())

    def merge_yaml(self, yaml):
        """
        merge configuration from a yaml stream

        Args:
            yaml (str|stream): yaml string
        """
        cfg = yaml.load(yaml)
        self.merge_dict(cfg)

    def merge_ini_file(self, ini_filename):
        """
        merge configuration stored in a .ini file.
        see merge_configparser for more details.

        Args:
            ini_filename (str): path to ini file to load
        """
        cfg = configparser.ConfigParser()
        cfg.read(ini_filename)
        self.merge_configparser(cfg)

    # ... etc

    def _merge_dict(self, cfg):
        for k, v in cfg.items():
            # do partial updates where needed
            existing = self.get(k)
            if _is_dicty(v) and isinstance(existing, ConfigDict):
                existing._merge_dict(v)
            else:
                self[k] = configify(v)

    def register_trigger(self, trigger):
        """
        Args:
            trigger (interfaces.ConfigurationTrigger): something that
                configures something!
        """
        self._triggers.append(trigger)

    def configure(self, clean=True):
        """
        Run any configuration extentions.  By default,
        this runs all extensions installed in the environment.

        clean (bool): If true, run validation prior to
            configuration. defaults to True.
        """
        for ext in self._triggers:
            cleaned = ext.clean(self)
            self._merge_dict(cleaned)
            ext.configure(self)

    ## attribute access ##

    def __getattr__(self, key):
        """
        """
        try:
            return self.__dict__[key]
        except KeyError:
            pass

        if key.startswith('_'):
            raise AttributeError("object has no attribute '%s'" % key)

        try:
            return self.__getitem__(key)
        except:
            raise AttributeError("object has no attribute '%s'" % key)

    def __setattr__(self, key, value):
        if key.startswith('_'):
            self.__dict__[key] = value
        else:
            return self.__setitem__(key, value)


def configify(ob):
    """
    builds a copy of the object given
    replacing plain dicts with ConfigDicts to
    facilitate attribute access and application
    of configuration.

    unrecognized types will be deepcopied.
    """
    if ob is None:
        return None

    if _is_scalar(ob):
        return copy.copy(ob)
    elif _is_dicty(ob):
        return ConfigDict([
            (k, configify(v)) for k, v in ob.items()])
    elif _is_listy(ob):
        return [configify(x) for x in ob]
    else:
        return copy.deepcopy(ob)

# bool true, false, yes, no, on, off, 1, 0

#
# quack-tests for data types
#

_BUILTIN_SCALAR_TYPES = (
    UnicodeType, StringType, BooleanType,
    IntType, LongType, FloatType)


def _is_scalar(ob):
    return isinstance(ob, _BUILTIN_SCALAR_TYPES)


_DICT_TYPES = (DictType, UserDict, DictMixin)


def _is_dicty(ob):
    return isinstance(ob, _DICT_TYPES)


_LIST_TYPES = (ListType, TupleType, UserList)


def _is_listy(ob):
    if isinstance(ob, _LIST_TYPES):
        return True

