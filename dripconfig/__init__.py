"""
the default 'global' configuration if desired.
"""

from .configdict import ConfigDict
from .sources import *
from interfaces import ConfigurationTrigger, ToBeInjected

config = ConfigDict()

__version__ = '0.1.dev0'

