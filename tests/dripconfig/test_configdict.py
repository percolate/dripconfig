import os
import textwrap
import mock
from tempfile import NamedTemporaryFile
from configparser import ConfigParser
from unittest import TestCase

from dripconfig.configdict import ConfigDict
from dripconfig.interfaces import ConfigurationTrigger
from dripconfig.helpers import SchemaTrigger
from dripconfig import sources
from voluptuous import (
    All, Coerce, MultipleInvalid, Optional, Range, Required, Schema)


class ConfigDictTestCase(TestCase):

    def test_attribute_access(self):
        """access ConfigDict keys as attributes"""
        cd = ConfigDict()

        cd['x'] = 1
        self.assertEquals(cd.x, 1)

        cd.y = 2
        self.assertEquals(cd['y'], 2)

    def test_from_dict(self):
        """create ConfigDict from dict"""
        cd = ConfigDict.from_dict({
            'x': 1,
            'y': {
                'z': 2,
                'w': [1,2, {'v': 22}]
            }
        })

        self.assertEquals(cd.x, 1)
        self.assertEquals(cd['x'], 1)
        self.assertEquals(cd.y.z, 2)
        self.assertEquals(cd['y']['z'], 2)
        self.assertEquals(cd.y.w[2].v, 22)
        self.assertEquals(cd['y']['w'][2]['v'], 22)


    def test_merge_dict(self):
        """merge configuration from dict"""
        cd = ConfigDict.from_dict({
            'a': 1,
            'b': {
                'c': 2,
                'd': 3,
                'e': {'h': 4},
                'f': [5,6],
                'g': [7,8]
            }
        })

        cd.merge_dict({
            'a': 11,
            'z': 99,
            'b': {
                'c': 22,
                'e': {'y': 999},
                'g': [77,88],
            }
        })

        self.assertEquals(cd.a,11)
        self.assertEquals(cd.b.c, 22)
        self.assertEquals(cd.b.d, 3)
        self.assertEquals(cd.b.e.h, 4)
        self.assertEquals(cd.b.e.y, 999)
        self.assertEquals(cd.b.f, [5,6])
        self.assertEquals(cd.b.g, [77, 88])
        self.assertEquals(cd.z,99)

    def test_merge_json(self):
        """merge configuration from json"""
        cd = ConfigDict.from_dict({
            'a': 1,
            'b': {
                'c': 2,
                'd': 3,
                'e': {'h': 4},
                'f': [5,6],
                'g': [7,8]
            }
        })

        cd.merge_json("""{
            "a": 11,
            "z": 99, /* here is a comment */
            "b": {
                "c": 22,
                "e": {"y": 999},
                // another sort of comment
                "g": [77,88]
            }
            /*
            this might be a rather long
            type of comment that spans several lines...
            */
        }""")

        self.assertEquals(cd.a,11)
        self.assertEquals(cd.b.c, 22)
        self.assertEquals(cd.b.d, 3)
        self.assertEquals(cd.b.e.h, 4)
        self.assertEquals(cd.b.e.y, 999)
        self.assertEquals(cd.b.f, [5,6])
        self.assertEquals(cd.b.g, [77, 88])
        self.assertEquals(cd.z,99)

    def test_merge_configparser(self):
        """merge configuration from ini"""
        cd = ConfigDict.from_dict({
            'a': 1,
            'b': {
                'c': 2,
                'd': 3,
            }
        })

        schema = Schema({
            'a': Coerce(int),
            'z': basestring,
            'b': {
                'c': Coerce(int)
            }
        }, extra=True)
        cd.register_trigger(
            SchemaTrigger(schema)
        )

        cfg = ConfigParser()
        cfg.read_string(u"""
        [main]
        a = 11
        z = 99

        [b]
        c = 22
        """)

        cd.merge_configparser(cfg)
        cd.configure()

        self.assertEquals(cd.a,11)
        self.assertEquals(cd.z, '99')
        self.assertEquals(cd.b.c, 22)
        self.assertEquals(cd.b.d, 3)

    def test_schema(self):
        """test/merge a schema to loaded configuration"""

        # schema for what the 'some_service' configuration
        # ought to look like.
        schema = Schema({
            'some_service': {
                'host': basestring,
                'port': Coerce(int),
                Required(
                    'pool_size', default=5):
                    All(Coerce(int), Range(min=1, max=20)),
                'credentials': {
                    'username': basestring,
                    'password': basestring
                }
            }
        })

        cd = ConfigDict()
        cd.register_trigger(
            SchemaTrigger(schema)
        )

        cd.merge_dict({
            'some_service': {
                'host': 'xyz',
                'port': 123,
                'credentials': {'username': 'foo', 'password': 'bar'}
            }
        })
        cd.configure()

        self.assertEquals(cd.some_service.host, 'xyz')
        self.assertEquals(cd.some_service.port, 123)
        self.assertEquals(cd.some_service.pool_size, 5)
        self.assertEquals(cd.some_service.credentials.username, 'foo')
        self.assertEquals(cd.some_service.credentials.password, 'bar')

        # integer coersion should take care of '123' instead of 123
        cd = ConfigDict()
        cd.register_trigger(
            SchemaTrigger(schema)
        )
        cd.merge_dict({
            'some_service': {
                'host': 'xyz',
                'port': '123',
                'credentials': {'username': 'foo', 'password': 'bar'}
            }
        })
        cd.configure()

        self.assertEquals(cd.some_service.host, 'xyz')
        self.assertEquals(cd.some_service.port, 123)
        self.assertEquals(cd.some_service.pool_size, 5)
        self.assertEquals(cd.some_service.credentials.username, 'foo')
        self.assertEquals(cd.some_service.credentials.password, 'bar')

        cd = ConfigDict()
        cd.register_trigger(
            SchemaTrigger(schema)
        )
        cd.merge_dict({
            'some_service': {
                'host': 'xyz',
                'port': 123,
                'pool_size': 21,
                'credentials': {'username': 'foo', 'password': 'bar'}
            }
        })

        # not valid -- pool_size out of range
        with self.assertRaises(MultipleInvalid):
            cd.configure()


class TestMergeFrom(TestCase):

    def setUp(self):
        self.cd = ConfigDict()
        self.conf_file1 = NamedTemporaryFile(suffix='.ini')
        self.conf_filename1 = self.conf_file1.name

        self.conf_file2 = NamedTemporaryFile(suffix='.ini')
        self.conf_filename2 = self.conf_file2.name

        self.conf_file1.write(textwrap.dedent(
            """
            [whoa]
            foo = bar

            """
        ))

        self.conf_file2.write(textwrap.dedent(
            """
            [whoa]
            foo = BAZ!

            """
        ))

        self.conf_file1.flush()
        self.conf_file2.flush()

    def tearDown(self):
        self.conf_file1.close()
        self.conf_file2.close()

    def test_argv(self):
        with mock.patch('sys.argv', ['yo', 'foo', self.conf_filename1]):
            self.cd.merge_from(
                sources.Argv(2),
            )

        print self.cd
        with open(self.conf_filename1, 'r') as f:
            print f.read()

        assert self.cd.whoa.foo == 'bar'

    def test_envvar(self):
        os.environ['DIS_ENVVAR'] = self.conf_filename1

        self.cd.merge_from(
            sources.EnvVar('DIS_ENVVAR'),
        )

        assert self.cd.whoa.foo == 'bar'

    def test_filename(self):
        self.cd.merge_from(
            sources.Filename(self.conf_filename1),
        )

        assert self.cd.whoa.foo == 'bar'

    def test_precedence(self):
        os.environ['DIS_ENVVAR'] = self.conf_filename1

        self.cd.merge_from(
            sources.Argv(2),  # bad source
            sources.Filename(self.conf_filename2),
            sources.EnvVar('DIS_ENVVAR'),  # should not get here
        )

        assert self.cd.whoa.foo == 'BAZ!'


