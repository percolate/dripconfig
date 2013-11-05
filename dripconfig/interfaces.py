from abc import ABCMeta, abstractmethod


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


class ToBeInjected(object):
    """
    One pattern of use for dripconfig is to inject objects into submodules from
    within a particular `ConfigurationTrigger.configure` definition; this
    allows the submodules to be unawawre of how configuration is obtained
    and processed.

    An instance of this class indicates that an object that will be injected by
    a `ConfigurationTrigger`. It raises hell if use of it is attempted.

    """
    def __init__(self, expected_cls=None):
        """
        Args:
            expected_cls (type): if passed, declare that we expect an object
                of type `expected_cls` to be injected. Doesn't do anything,
                just for human convenience.

        """
        self.expected_cls = expected_cls

    def __call__(self):
        self.__getattribute__(None)

    def __getattribute__(self, _):
        obj_type_str = "A non-degenerate object"

        if self.expected_cls:
            obj_type_str = "A %s instance" % obj_type_str

        raise NotImplementedError(
            "This object is a placeholder. %s was "
            "supposed to be injected by a `dripconfig.ConfigurationTrigger`."
            % obj_type_str
        )

