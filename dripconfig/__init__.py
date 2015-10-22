"""
the default 'global' configuration if desired.
"""

from .configdict import ConfigDict
from .sources import (
    Argv,
    EnvVar,
    Filename,
)
from .helpers import SysLogHandler
from .interfaces import ConfigurationTrigger, ToBeInjected

__all__ = [
    'Argv',
    'ConfigDict',
    'ConfigurationTrigger',
    'EnvVar',
    'Filename',
    'SysLogHandler',
    'ToBeInjected',
    'config'
]


config = ConfigDict()

__version__ = '0.2.3'
