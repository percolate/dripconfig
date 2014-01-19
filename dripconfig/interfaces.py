from abc import ABCMeta, abstractmethod, abstractproperty


class ConfigurationTrigger(object):
    """
    configuration plugins should conform to this interface.

    Represents something that needs to happen to
    either prepare or apply a given configuration.

    This may represent some normalization of values, or
    some global setup that needs to happen.
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def configure(self, configuation):
        """
        apply the configuration given.
        """

    @abstractmethod
    def clean(self, configuration):
        """
        validate / clean the configuration dictionary
        given.  This may alter definitions in the
        configuration.
        """


class SchemaBasedTrigger(ConfigurationTrigger):
    """
    A configuration trigger that is based on a voluptuous schema. Overrides
    clean to validate against the given schema. Assumes the schema given is
    partial; i.e. sets `extra = True`.

    """

    __metaclass__ = ABCMeta

    @abstractproperty
    def partial_schema(self):
        """
        The volutptuous schema used to validate the related config.

        """

    def clean(self, configuration):
        self.partial_schema.extra = True
        return self.partial_schema(configuration)


class ToBeInjected(object):
    """
    One pattern of use for dripconfig is to inject objects into submodules from
    within a particular `ConfigurationTrigger.configure` definition; this
    allows the submodules to be unawawre of how configuration is obtained
    and processed.

    An instance of this class indicates that an object that will be injected by
    a `ConfigurationTrigger`. It raises hell if use of it is attempted.

    """
    def __init__(self, expected_type=None):
        """
        Args:
            expected_type (type): if passed, declare that we expect an object
                of type `expected_type` to be injected. Doesn't do anything,
                just for human convenience.

        """
        self.expected_type = expected_type

    def __call__(self):
        self.__getattribute__(None)

    def __getattribute__(self, key):
        if key == 'expected_type':
            return super(ToBeInjected, self).__getattribute__(key)

        obj_type_str = "A non-degenerate object"

        if self.expected_type:
            obj_type_str = "A %s instance" % self.expected_type

        raise NotImplementedError(
            "This object is a placeholder. %s was "
            "supposed to be injected by a `dripconfig.ConfigurationTrigger`."
            % obj_type_str
        )

    def __repr__(self):
        return "ToBeInjected(%s)" % self.expected_type
