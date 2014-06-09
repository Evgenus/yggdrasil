import random
from collections import UserString, Mapping, Sequence, deque, defaultdict
from functools import lru_cache

from .utils import (
    ReadOnlyDict,
    ReadOnlySet,
    )

# ____________________________________________________________________________ #

@lru_cache()
def UUID(length, alphabet=None):
    _alphabet = alphabet or "23456789abcdefghijkmnopqrstuvwxyz"
    class _UUID(UserString):
        def __init__(self):
            super().__init__(
                ''.join(random.choice(_alphabet)  
                    for i in range(length))
            )
        @classmethod
        def from_string(cls, s):
            assert isinstance(s, str)
            assert len(s) == length
            assert all(c in _alphabet for c in s)
            instance = cls()
            instance.data = s
            return instance
    return _UUID

# ____________________________________________________________________________ #

class NodeNotFound(KeyError): pass
class RevisionFinishedError(RuntimeError): pass
class RevisionNotFinishedError(RuntimeError): pass

# ____________________________________________________________________________ #

class NodeMeta(type):
    def __new__(meta, name, bases, namespace):
        slots = set(namespace.pop("__slots__", ()))
        for base in bases:
            slots |= set(getattr(base, "__slots__", ()))
        if bases:
            slots.discard("__dict__")
        namespace["__slots__"] = tuple(slots)
        cls = type.__new__(meta, name, bases, namespace)
        return cls

# ____________________________________________________________________________ #

class NodeRef(UserString):
    def __init__(self, uid:UUID(32)=None):
        assert uid is None or isinstance(uid, UUID(32))
        super().__init__(UUID(32)() if uid is None else uid)
    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        return super().__eq__(other)
    def __hash__(self): 
        return super().__hash__()
    @classmethod
    def from_string(cls, s):
        return cls(UUID(32).from_string(s))

class BranchId(UserString):
    def __init__(self, uid:UUID(16)=None):
        assert uid is None or isinstance(uid, UUID(16))
        super().__init__(UUID(16)() if uid is None else uid)
    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        return super().__eq__(other)
    def __hash__(self): 
        return super().__hash__()
    @classmethod
    def from_string(cls, s):
        return cls(UUID(16).from_string(s))

class RevisionId(UserString):
    def __init__(self, branch_id:BranchId, number:int):
        self.branch = branch_id
        self.number = number
        super().__init__("{0}:{1:08x}".format(self.branch, self.number))
    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        return super().__eq__(other)
    def __hash__(self): 
        return super().__hash__()
    @classmethod
    def from_string(cls, s):
        assert isinstance(s, str)
        assert len(s) == 25
        bid = BranchId.from_string(s[:16])
        number = int(s[17:], 16)
        return cls(bid, number)

class NodeId(UserString):
    def __init__(self, node_ref:NodeRef, revision_id:RevisionId):
        self.node_ref = node_ref
        self.revision = revision_id
        super().__init__("{0}:{1}".format(self.revision, self.node_ref))
    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        return super().__eq__(other)
    def __hash__(self): 
        return super().__hash__()
    @classmethod
    def from_string(cls, s):
        assert isinstance(s, str)
        assert len(s) == 58
        rid = RevisionId.from_string(s[:25])
        ref = NodeRef.from_string(s[26:])
        return cls(ref, rid)

# ____________________________________________________________________________ #

class Node(metaclass=NodeMeta):
    __slots__ = "_runtime", "_ref", "__dict__"
    def __init__(self, runtime, node_ref:NodeRef=None):
        self._runtime = runtime
        if node_ref is None:
            node_ref = NodeRef()
        self._ref = node_ref

    @property
    def ref(self):
        return self._ref

    @property
    def runtime(self):
        return self._runtime

    @property
    def content(self):
        return ReadOnlyDict(self.__dict__)

class ReadOnlyNodeProxy(object):
    """
    We need some proxy layer abstraction to control working copy bounds.
    This is basic proxy wrapper used for read only nodes accessed from 
    read-only (already committed) revision.
    """
    __slots__ = "_revision", "_node"
    __atomic_types__ = int, str, float, bool, NodeRef, BranchId, RevisionId, NodeId

    def __init__(self, revision, node):
        self._revision = revision
        self._node = node

    def __setattr__(self, name, value):
        if name in self.__slots__:
            object.__setattr__(self, name, value)
        raise RuntimeError("This node is read only")

    def __getattr__(self, name):
        klass_ref = getattr(self._node, "__isinstance__", None)
        if klass_ref is not None:
            if klass_ref == self._node.ref:
                klass = self._node
            else:
                klass = self._revision.get_node(klass_ref)
            getter = getattr(klass, "getter", None)
            if getter is not None:
                return getter(self, name)
        return getattr(self._node, name)

    def __call__(self):
        return self._node

class ReadWriteNodeProxy(ReadOnlyNodeProxy):
    __slots__ = "_revision", "_node"
    def _check_value(self, value):
        if value is None:
            pass
        elif isinstance(value, self.__atomic_types__):
            pass
        elif isinstance(value, Mapping):
            for k, v in value.items():
                self._check_value(v)
        elif isinstance(value, Sequence):
            for i in value:
                self._check_value(i)
        else:
            raise TypeError(type(value))

    def __setattr__(self, name, value):
        if name in self.__slots__:
            object.__setattr__(self, name, value)
        else:
            try:
                self._check_value(value)
            except TypeError as error:
                raise AttributeError(name)
            setattr(self._node, name, value)

class CopyOnWriteNodeProxy(ReadWriteNodeProxy): pass

class Revision(Node):
    __slots__ = "_rid", "_ancestors", "_nodes", "_refs", "_finished"
    def __init__(self, runtime, node_ref:NodeRef, revision_id:RevisionId, *ancestors):
        super().__init__(runtime, node_ref)
        self._rid = revision_id
        self._ancestors = ancestors
        self._nodes = set() # NodeRef
        self._refs = {} # NodeRef -> RevisionId
        self._finished = False
        self.attach_node(self)
        runtime.register_revision(self)

    @property
    def id(self):
        return self._rid

    @property
    def finished(self):
        return self._finished

    @property
    def ancestors(self):
        return self._ancestors

    @property
    def nodes(self):
        return ReadOnlySet(self._nodes)

    @property
    def refs(self):
        return ReadOnlyDict(self._refs)

    def create_node(self):
        if self.finished: 
            raise RevisionFinishedError(self)
        node = Node(self.runtime)
        self.attach_node(node)
        return ReadWriteNodeProxy(self, node)

    def attach_node(self, node):
        if self.finished:
            raise RevisionFinishedError(self)
        node_id = NodeId(node.ref, self.id)
        self._nodes.add(node.ref)
        self._refs[node.ref] = self.id
        self.runtime.register_node(node_id, node)

    def has_node(self, node_ref:NodeRef):
        return node_ref in self._nodes

    def search(self, node_ref:NodeRef):
        if self.has_node(node_ref):
            return self
        return self.get_node(self._refs[node.ref])

    def get_node(self, node_ref:NodeRef):
        if node_ref == self.ref:
            if self.finished:
                return ReadOnlyNodeProxy(self, self)
            else:
                return ReadWriteNodeProxy(self, self)
        
        if node_ref in self._nodes:
            node_uid = NodeId(node_ref, self._rid)
            node = self.runtime.get_node(node_uid)
            if self.finished:
                return ReadOnlyNodeProxy(self, node)
            else:
                return ReadWriteNodeProxy(self, node)

        revision_id = self._refs.get(node_ref)
        if revision_id is None:
            raise NodeNotFound(node_ref)

        node_uid = NodeId(node_ref, revision_id)
        node = self.runtime.get_node(node_uid)

        return CopyOnWriteNodeProxy(self, node)
        
"""
    def _merge(self, revision):
        if self.finished: 
            raise RevisionFinishedError(self)
        if not revision.finished: 
            raise RevisionNotFinishedError(self)
        # TODO: find conflicted nodes
        for node_ref, node_id in revision._nodes.items():
            if node_ref in self._nodes:
                # node merge
                pass
            elif node_ref in self._refs:
                revision_ref = self._refs[node_ref]
                if revision_ref != revision.ref:
                    # node merge
                    pass
            else:
                self._refs[node_ref] = revision.ref

        for node_ref, revision_ref in revision._refs.items():
            if node_ref in self._nodes:
                pass
            elif node_ref in self._refs:
                pass
            else:
                pass
"""

class Branch(Node):
    __slots__ = "_bid", "_revision", "_wc"
    def __init__(self, runtime, node_ref:NodeRef=None, branch_id:BranchId=None):
        super().__init__(runtime, node_ref)
        if branch_id is None:
            branch_id = BranchId()
        self._bid = branch_id
        self._revision = 0
        wc = Revision(runtime, None, RevisionId(self.id, self._revision))
        self._wc = wc.id
        wc.attach_node(self)
        runtime.register_branch(self)

    @property
    def id(self):
        return self._bid

    @property
    def wc(self):
        return self.runtime.get_revision(self._wc)

    @property
    def revision(self):
        return self._revision

    def merge(self, revision_id:RevisionId):
        revision = runtime.get_revision(revision_id)
        self.wc._merge(revision)

    def commit(self):
        # TODO: Check for conflicts 
        old = self.wc
        old._finished = True
        self._revision += 1
        wc = Revision(self._runtime, None, RevisionId(self.id, self._revision), old.id)
        self._wc = wc.id

# TODO: Determine whether node created or requested
# TODO: Transactions for rollbacks 
class Runtime(object):
    def __init__(self):
        self._nodes = {}
        self._revisions = {}
        self._branches = {}

    def register_node(self, node_id, node):
        self._nodes[node_id] = node

    def register_revision(self, revision):
        self._revisions[revision.id] = revision

    def register_branch(self, branch):
        self._branches[branch.id] = branch

    def create_branch(self):
        branch = Branch(self)
        return branch

    def fork(self, revision_id:RevisionId):
        branch = Branch(self)
        branch.merge(revision_id)
        return branch

    def get_node(self, node_id:NodeId):
        return self._nodes.get(node_id)

    def get_revision(self, revision_id:RevisionId):
        return self._revisions.get(revision_id)

    def get_branch(self, branch_id:BranchId):
        return self._branches.get(branch_id)

    def get_branches(self):
        for bid in self._branches:
            yield bid

    def get_revisions(self, branch_id:BranchId):
        for rid in self._revisions:
            if rid.branch == branch_id:
                yield rid

class BoilerPlate(object):
    def __init__(self, runtime, features=()):
        self._runtime = runtime
        self._branch = self._runtime.create_branch()
        self._wc = self._branch.wc
        self._delayed = defaultdict(deque)
        self._finish = set()
        if features:
            self.make(*features)
        self._branch.commit()

    @property
    def meta(self):
        class Metaclass(type):
            layers = "types", "fields"

            def __new__(meta, name, bases, namespace):
                node = self._wc.create_node()
                node.__name__ = name

                for layer in meta.layers:
                    func = namespace.get(layer)
                    if func is None:
                        continue
                    if layer in self._finish:
                        func(node)
                    else:
                        self._delayed[layer].append((func, node))

                return node
        return Metaclass

    def finish(self, layer):
        group = self._delayed[layer]
        while group:
            func, node = group.popleft()
            func(node)
        self._finish.add(layer)

    def make(hub, *names):
        class NodeType(metaclass=hub.meta):
            def types(node):
                node.__isinstance__ = TypeType.ref
                node.__bases__ = ()
                node.__duck__ = True
            def fields(node):
                class StringField(metaclass=hub.meta):
                    def types(node):
                        node.__isinstance__ = AtomicFieldType.ref
                        node.__type__ = "String"
                        node.required = False
                        node.default = None
                node.__fields__ = ReadOnlyDict(
                    __name__=StringField.ref,
                    )

        class TypeType(metaclass=hub.meta):
            def types(node):
                node.__isinstance__ = TypeType.ref
                node.__bases__ = (NodeType.ref, )
            def fields(node):
                class IsinstanceField(metaclass=hub.meta):
                    def types(node):
                        node.__isinstance__ = LinkFieldType.ref
                    def fields(node):
                        node.__type__ = TypeType.ref
                class TypesListField(metaclass=hub.meta):
                    def types(node):
                        node.__isinstance__ = UniformListFieldType.ref
                    def fields(node):
                        class TypeField(metaclass=hub.meta):
                            def types(node):
                                node.__isinstance__ = LinkFieldType.ref
                                node.__type__ = TypeType.ref
                        node.__item__ = TypeField.ref

                class FieldsDictionaryField(metaclass=hub.meta):
                    def types(node):
                        node.__isinstance__ = UniformDictionaryFieldType.ref
                    def fields(node):
                        class StringField(metaclass=hub.meta):
                            def types(node):
                                node.__isinstance__ = AtomicFieldType.ref
                                node.__type__ = "String"
                                node.required = True
                                node.default = None
                        class FieldField(metaclass=hub.meta):
                            def types(node):
                                node.__isinstance__ = LinkFieldType.ref
                                node.__type__ = FieldType.ref
                                node.required = True
                                node.default = None
                        node.__key__ = StringField.ref
                        node.__value__ = FieldField.ref
                class AbstractField(metaclass=hub.meta):
                    def types(node):
                        node.__isinstance__ = AtomicFieldType.ref
                        node.__type__ = "Boolean"
                        node.required = False
                        node.default = False
                class DuckField(metaclass=hub.meta):
                    def types(node):
                        node.__isinstance__ = AtomicFieldType.ref
                        node.__type__ = "Boolean"
                        node.required = False
                        node.default = False
                node.__fields__ = ReadOnlyDict(
                    __isinstance__=IsinstanceField.ref,
                    __bases__=TypesListField.ref,
                    __fields__=FieldsDictionaryField.ref,
                    __abstract__=AbstractField.ref,
                    __duck__=DuckField.ref,
                    )

        class FieldType(metaclass=hub.meta):
            def types(node):
                node.__isinstance__ = TypeType.ref
                node.__bases__ = (NodeType.ref, )
                node.__abstract__ = True

        class AtomicFieldType(metaclass=hub.meta):
            def types(node):
                node.__isinstance__ = TypeType.ref
                node.__bases__ = (FieldType.ref, )
                node.__abstract__ = False
            def fields(node):
                class StringField(metaclass=hub.meta):
                    def types(node):
                        node.__isinstance__ = AtomicFieldType.ref
                        node.__type__ = "String"
                        node.required = True
                        node.default = None
                node.__fields__ = ReadOnlyDict(
                    __type__=StringField.ref,
                    )

        class LinkFieldType(metaclass=hub.meta):
            def types(node):
                node.__isinstance__ = TypeType.ref
                node.__bases__ = (FieldType.ref, )
                node.__abstract__ = False
            def fields(node):
                class TypeField(metaclass=hub.meta):
                    def types(node):
                        node.__isinstance__ = LinkFieldType.ref
                        node.__type__ = TypeType.ref
                node.__fields__ = ReadOnlyDict(
                    __type__=TypeField.ref,
                    )

        class ComplexFieldType(metaclass=hub.meta):
            def types(node):
                node.__isinstance__ = TypeType.ref
                node.__bases__ = (FieldType.ref, )
                node.__abstract__ = True

        class ListFieldType(metaclass=hub.meta):
            def types(node):
                node.__isinstance__ = TypeType.ref
                node.__bases__ = (ComplexFieldType.ref, )
                node.__abstract__ = True

        class DictionaryFieldType(metaclass=hub.meta):
            def types(node):
                node.__isinstance__ = TypeType.ref
                node.__bases__ = (ComplexFieldType.ref, )
                node.__abstract__ = True

        class UniformListFieldType(metaclass=hub.meta):
            def types(node):
                node.__isinstance__ = TypeType.ref
                node.__bases__ = (ListFieldType.ref, )
                node.__abstract__ = False
            def fields(node):
                node.__fields__ = ReadOnlyDict(
                    __item__=FieldType.ref,
                    )

        class UniformDictionaryFieldType(metaclass=hub.meta):
            def types(node):
                node.__isinstance__ = TypeType.ref
                node.__bases__ = (DictionaryFieldType.ref, )
                node.__abstract__ = False
            def fields(node):
                node.__fields__ = ReadOnlyDict(
                    __key__=FieldType.ref,
                    __value__=FieldType.ref,
                    )

        for name in names:
            hub.finish(name)
