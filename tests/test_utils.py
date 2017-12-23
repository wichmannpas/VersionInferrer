from datetime import date
from unittest import TestCase

from backends.software_version import SoftwareVersion
from base.utils import join_paths, join_url, most_recent_version


class TestJoinPaths(TestCase):
    def test_regular_paths(self):
        self.assertEqual(
            join_paths('/asdf', 'foo'),
            '/asdf/foo')
        self.assertEqual(
            join_paths('asdf', 'foo'),
            'asdf/foo')

    def test_leading_slashes(self):
        self.assertEqual(
            join_paths('asdf', '/foo'),
            'asdf/foo')
        self.assertEqual(
            join_paths('asdf', '/foo', '/bar'),
            'asdf/foo/bar')
        self.assertEqual(
            join_paths('asdf', 'foo', '/bar'),
            'asdf/foo/bar')
        self.assertEqual(
            join_paths('foo', 'foo', 'bar/', '/baz'),
            'foo/foo/bar/baz')

    def test_trailing_slashes(self):
        self.assertEqual(
            join_paths('asdf', '/foo/'),
            'asdf/foo/')
        self.assertEqual(
            join_paths('asdf', 'foo/', '/bar'),
            'asdf/foo/bar')
        self.assertEqual(
            join_paths('asdf', '/foo/', '/bar'),
            'asdf/foo/bar')


class TestJoinUrl(TestCase):
    def test_absolute_urls(self):
        self.assertEqual(
            join_url('https://foo/', 'https://bar'),
            'https://bar/')
        self.assertEqual(
            join_url('https://foo/', 'https://bar', 'baz'),
            'https://bar/baz')
        self.assertEqual(
            join_url('https://foo/bar', '/baz'),
            'https://foo/baz')

    def test_leading_slash_stripping_within(self):
        self.assertEqual(
            join_url('https://foo/', '/bar', 'baz'),
            'https://foo/bar/baz')
        self.assertEqual(
            join_url('https://foo/', '/bar', '/baz'),
            'https://foo/bar/baz')

    def test_relative_paths(self):
        self.assertEqual(
            join_url('https://foo/', 'bar', '..', 'baz'),
            'https://foo/baz')
        self.assertEqual(
            join_url('https://foo/', 'bar/../baz'),
            'https://foo/baz')

    def test_trailing_slash_stripping_within(self):
        self.assertEqual(
            join_url('https://foo'),
            'https://foo/')
        self.assertEqual(
            join_url('https://foo/'),
            'https://foo/')
        self.assertEqual(
            join_url('https://foo/', 'bar/', '/baz'),
            'https://foo/bar/baz')


class TestMostRecentVersion(TestCase):
    def setUp(self):
        self.version1 = SoftwareVersion(
            None,
            'foobar',
            'foobar',
            date(2000, 1, 1))
        self.version2 = SoftwareVersion(
            None,
            'qux',
            'quxa',
            date(2001, 1, 1))
        self.version3 = SoftwareVersion(
            None,
            'baz',
            'baz',
            date(2001, 5, 2))

    def test_list(self):
        self.assertEqual(
            most_recent_version([
                self.version1,
            ]),
            self.version1)
        self.assertEqual(
            most_recent_version([
                self.version1,
                self.version3,
            ]),
            self.version3)
        self.assertEqual(
            most_recent_version([
                self.version1,
                self.version2,
                self.version3,
            ]),
            self.version3)
        self.assertEqual(
            most_recent_version([
                self.version2,
                self.version1,
            ]),
            self.version2)

    def test_set(self):
        self.assertEqual(
            most_recent_version({
                self.version1,
            }),
            self.version1)
        self.assertEqual(
            most_recent_version({
                self.version1,
                self.version3,
            }),
            self.version3)
        self.assertEqual(
            most_recent_version({
                self.version1,
                self.version2,
                self.version3,
            }),
            self.version3)
        self.assertEqual(
            most_recent_version({
                self.version2,
                self.version1,
            }),
            self.version2)
