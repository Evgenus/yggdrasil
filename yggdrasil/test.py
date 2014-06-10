import unittest
import yaml
from .node import *
from .utils import undefined

class TestNodesBolierPlate(unittest.TestCase):
    def setUp(self):
        self.runtime = Runtime()

    def test_working_copy_integrity(self):
        branch = self.runtime.create_branch()
        wc = branch.wc
        self.assertEqual(wc.get_node(wc.ref)(), wc)
        self.assertEqual(wc.get_node(branch.ref)(), branch)
        self.assertEqual(list(wc.__dict__.keys()), [])
        self.assertEqual(list(branch.__dict__.keys()), [])

    def test_proxy(self):
        branch = self.runtime.create_branch()
        wc = branch.wc

        NodeType = wc.create_node() # object
        assert NodeType._node.__dict__ is NodeType.__dict__
        NodeType = wc.get_node(NodeType.ref)
        assert NodeType._node.__dict__ is NodeType.__dict__

    def test_all(self):
        hub = BoilerPlate(self.runtime, features=("types", "fields"))

