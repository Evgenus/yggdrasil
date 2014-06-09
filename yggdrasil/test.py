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

        """
        # ______________________________________________________ code layer __ #

        class RevisionType(metaclass=hub.meta):
            def types(node):
                node.__isinstance__ = TypeType.ref
                node.__bases__ = (NodeType.ref, )

        class BranchType(metaclass=hub.meta):
            def types(node):
                node.__isinstance__ = TypeType.ref
                node.__bases__ = (NodeType.ref, )

        wc.__isinstance__ = RevisionType.ref
        branch.__isinstance__ = BranchType.ref

        CodeType = wc.create_node()
        CodeType.__isinstance__ = TypeType.ref
        CodeType.__bases__ = (NodeType.ref, )
        CodeType.__fields__ = {
            co_argcount
            co_kwonlyargcount
            co_nlocals
            co_stacksize
            co_flags
            co_code
            co_consts
            co_names
            co_varnames
            co_filename
            co_name
            co_firstlineno
            co_lnotab
            co_freevars
            co_cellvars
            }
        MethodType = wc.create_node()
        MethodType.__isinstance__ = TypeType.ref
        MethodType.__bases__ = (NodeType.ref, )

        """
