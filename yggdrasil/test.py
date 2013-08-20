import unittest
from .node import *

class TestProxyList(unittest.TestCase):
    def setUp(self):
        self.runtime = Runtime()

    def test_1(self):
        branch = self.runtime.create_branch()
        wc = branch.wc
        self.assertEqual(wc.get_node(wc.ref), wc)
        self.assertEqual(wc.get_node(branch.ref), branch)
        self.assertEqual(list(wc.__dict__.keys()), [])
        self.assertEqual(list(branch.__dict__.keys()), [])

    def test_2(self):
        branch = self.runtime.create_branch()
        wc = branch.wc

        # _______________________________________________________ bootstrap __ #

        NodeType = wc.create_node() # object
        TypeType = wc.create_node() # type

        NodeType.__isinstance__ = TypeType.ref
        NodeType.__bases__ = ()
        NodeType.__duck__ = True

        TypeType.__isinstance__ = TypeType.ref
        TypeType.__bases__ = (NodeType.ref, )

        # ____________________________________________________ fields layer __ #

        StringField = wc.create_node()
        TypeField = wc.create_node()
        TypesListField = wc.create_node()
        FieldsDictionaryField = wc.create_node()
        FieldTypeField = wc.create_node()
        BooleanField = wc.create_node()

        NodeType.__fields__ = dict(
            __name__=StringField.ref
            )

        TypeType.__fields__ = dict(
            __isinstance__=TypeField.ref,
            __bases__=TypesListField.ref,
            __fields__=FieldsDictionaryField.ref,
            __abstract__=BooleanField.ref,
            __duck__=BooleanField.ref,
            )

        # Actually it is possible to make universal field type by describing 
        # collections and atomic types inside tree
        FieldType = wc.create_node()
        FieldType.__isinstance__ = TypeType.ref
        FieldType.__bases__ = (NodeType.ref, )
        FieldType.__abstract__ = True

        AtomicFieldType = wc.create_node()
        AtomicFieldType.__isinstance__ = TypeType.ref
        AtomicFieldType.__bases__ = (NodeType.ref, )
        AtomicFieldType.__fields__ = dict(
            __type__=StringField.ref,
            )

        LinkFieldType = wc.create_node()
        LinkFieldType.__isinstance__ = TypeType.ref
        LinkFieldType.__bases__ = (FieldType.ref, )
        LinkFieldType.__fields__ = dict(
            __type__=TypeField.ref,
            )

        ComplexFieldType = wc.create_node()
        ComplexFieldType.__isinstance__ = TypeType.ref
        ComplexFieldType.__bases__ = (FieldType.ref, )
        ComplexFieldType.__abstract__ = True

        ListFieldType = wc.create_node()
        ListFieldType.__isinstance__ = TypeType.ref
        ListFieldType.__bases__ = (ComplexFieldType.ref, )
        ListFieldType.__abstract__ = True

        DictionaryFieldType = wc.create_node()
        DictionaryFieldType.__isinstance__ = TypeType.ref
        DictionaryFieldType.__bases__ = (ComplexFieldType.ref, )
        DictionaryFieldType.__abstract__ = True

        UniformListFieldType = wc.create_node()
        UniformListFieldType.__isinstance__ = TypeType.ref
        UniformListFieldType.__bases__ = (ListFieldType.ref, )
        UniformListFieldType.__fields__ = dict(
            __item__=FieldType.ref,
            )

        UniformDictionaryFieldType = wc.create_node()
        UniformDictionaryFieldType.__isinstance__ = TypeType.ref
        UniformDictionaryFieldType.__bases__ = (DictionaryFieldType.ref, )
        UniformDictionaryFieldType.__fields__ = dict(
            __key__=FieldType.ref,
            __value__=FieldType.ref,
            )

        FieldsDictionaryField.__isinstance__ = UniformDictionaryFieldType.ref
        FieldsDictionaryField.__key__ = StringField.ref
        FieldsDictionaryField.__value__ = FieldTypeField.ref

        FieldTypeField.__isinstance__ = LinkFieldType.ref
        FieldTypeField.__type__ = FieldType.ref

        TypeField.__isinstance__ = LinkFieldType.ref
        TypeField.__type__ = TypeType.ref

        TypesListField.__isinstance__ =  UniformListFieldType.ref
        TypesListField.__item__ = TypeField.ref

        StringField.__isinstance__ = AtomicFieldType.ref
        StringField.__type__ = "String"

        BooleanField.__isinstance__ = AtomicFieldType.ref
        BooleanField.__type__ = "Boolean"

        # ___________________________________________________ runtime layer __ #

        RevisionType = wc.create_node()
        RevisionType.__isinstance__ = TypeType.ref
        RevisionType.__bases__ = (NodeType.ref, )

        BranchType = wc.create_node()
        BranchType.__isinstance__ = TypeType.ref
        BranchType.__bases__ = (NodeType.ref, )


        assert False
