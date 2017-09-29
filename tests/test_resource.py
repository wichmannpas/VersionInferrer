from unittest import TestCase

from analysis.resource import Resource


class TestRetrieval(TestCase):
    def test_retrieval_on_content_access(self):
        resource = Resource('https://heise.de')
        self.assertFalse(resource.retrieved)
        resource.content
        self.assertTrue(resource.retrieved)

    def test_explicit_retrieval(self):
        resource = Resource('https://heise.de')
        self.assertFalse(resource.retrieved)
        resource.retrieve()
        self.assertTrue(resource.retrieved)
