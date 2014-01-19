"""
Test utilities around dependency injection.

"""

import unittest

import dripconfig


class TestToBeInjected(unittest.TestCase):

    def setUp(self):
        TestToBeInjected.dependency = dripconfig.ToBeInjected(int)

        class TestTrigger(dripconfig.ConfigurationTrigger):

            def clean(_, conf):
                return conf

            def configure(_, conf):
                TestToBeInjected.dependency = 123

        dripconfig.config.register_trigger(TestTrigger())

    def test_before_configure(self):
        str(self.dependency)  # __repr__ should work

        with self.assertRaises(NotImplementedError):
            self.dependency.foo

    def test_after_configure(self):
        dripconfig.config.configure()

        self.assertEquals(self.dependency, 123)
