import json
from dripconfig.interfaces import ConfigurationTrigger

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