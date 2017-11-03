from tempfile import NamedTemporaryFile
from unittest import TestCase

from base.checksum import calculate_checksum, calculate_file_checksum


class TestChecksum(TestCase):
    def test_checksum(self):
        self.assertEqual(
            calculate_checksum(b'foobar123'),
            b'\x958v\x8a0\x82~\xd3z.\xc3\x80\xccm\xb5h')


class TestFileChecksum(TestCase):
    def test_file(self):
        with NamedTemporaryFile(mode='wb') as tmp:
            tmp.write(b'foobar123')
            tmp.flush()
            self.assertEqual(
                calculate_file_checksum(tmp.name),
                b'\x958v\x8a0\x82~\xd3z.\xc3\x80\xccm\xb5h')
