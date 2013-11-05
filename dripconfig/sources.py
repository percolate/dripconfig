"""
Objects that indicate the different sources that can provide the location
of configuration data.

"""

import abc
import os
import sys


__all__ = (
    'Filename',
    'Argv',
    'EnvVar',
)


class ConfigSource(object):
    """
    Indicates the location of some configuration and whether it exists or not.

    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractproperty
    def is_usable(self):
        """
        Returns:
            bool. True if the configuration pointed to by this object is a
            candidate for use.

        """

    @abc.abstractproperty
    def filename(self):
        """
        Returns:
            str. the filename where the config data lives.

        """


class Filename(ConfigSource):
    """
    A raw filename.

    """
    def __init__(self, fname):
        self._filename = fname

    @property
    def is_usable(self):
        try:
            return os.path.exists(self.filename)
        except TypeError:
            return False

    @property
    def filename(self):
        return self._filename


class EnvVar(Filename):

    def __init__(self, env_var_name):
        """
        Args:
            env_var_name (str): the name of the environment variable pointing
                to a file.

        """
        self.env_var_name = env_var_name
        self._filename = os.environ.get(env_var_name)


class Argv(Filename):

    def __init__(self, argv_index):
        """
        Args:
            argv_index (int): the 0-based index from which to pull a filename
                from.

        """
        self.argv_index = argv_index

        try:
            self._filename = sys.argv[argv_index]
        except IndexError:
            self._filename = None

