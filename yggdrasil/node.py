from shortuuid import uuid as uuid_short
from collections import UserString, Mapping, Sequence, deque

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
    def __init__(self, uid=None):
        super().__init__(uuid_short() if uid is None else uid)
    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        return super().__eq__(other)
    def __hash__(self): return super().__hash__()

class BranchId(UserString):
    def __init__(self, uid=None):
        super().__init__(uuid_short() if uid is None else uid)
    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        return super().__eq__(other)
    def __hash__(self): return super().__hash__()

class RevisionId(UserString):
    def __init__(self, branch_id:BranchId, number:int):
        self.branch = branch_id
        self.number = number
        super().__init__("{0}:{1:08x}".format(self.branch, self.number))
    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        return super().__eq__(other)
    def __hash__(self): return super().__hash__()

class NodeId(UserString):
    def __init__(self, node_ref:NodeRef, revision_id:RevisionId):
        self.node_ref = node_ref
        self.revision = revision_id
        super().__init__("{0}:{1}".format(self.revision, self.node_ref))
    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        return super().__eq__(other)
    def __hash__(self): return super().__hash__()

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
        if name not in self.__slots__:
            object.__setattr__(self, name, value)
        raise RuntimeError("This node is read only")

    def __getattr__(self, name):
        klass_ref = getattr(self._node, "__isinstance__", None)
        if klass_ref is not None:
            klass = self._revision.get_node(klass_ref)
            getter = getattr(klass, "getter", None)
            if getter is not None:
                return getter(name)
        return getattr(self._node, name)


class ReadWriteNodeProxy(ReadOnlyNodeProxy): pass
"""
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
        if name not in self.__slots__:
            try:
                self._check_value(value)
            except TypeError as error:
                raise AttributeError(name)
        object.__setattr__(self._node, name, value)    
"""

class Revision(Node):
    __slots__ = "_cid", "_ancestors", "_nodes", "_refs", "_finished", "_conflicts"
    def __init__(self, runtime, node_ref:NodeRef, revision_id:RevisionId, *ancestors):
        super().__init__(runtime, node_ref)
        self._cid = revision_id
        self._ancestors = ancestors
        self._nodes = {} # NodeRef -> NodeId
        self._refs = {} # NodeRef -> RevisionNodeRef
        self._finished = False
        self._conflicts = {} # NodeRef -> [ NodeId ]
        self.attach_node(self)
        runtime.register_revision(self)

    @property
    def id(self):
        return self._cid

    @property
    def finished(self):
        return self._finished

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
        self._nodes[node.ref] = node_id
        self._refs[node.ref] = self.ref
        self.runtime.register_node(node_id, node)

    def has_node(self, node_ref:NodeRef):
        return node_ref in self._nodes
    
    def search(self, node_ref:NodeRef):
        if self.has_node(node_ref):
            return self
        return self.get_node(self._refs[node.ref])

    def get_node(self, node_ref:NodeRef):
        if node_ref == self.ref:
            return self
        
        node_uid = self._nodes.get(node_ref)
        if node_uid is not None: 
            return self.runtime.get_node(node_uid)
        
        revision_node_ref = self._refs.get(node_ref)
        if revision_node_ref is None:
            raise NodeNotFound(node_ref)
        revision = self.get_node(revision_node_ref)
        node = revision.get_node(node_ref)
        return ReadWriteNodeProxy(self, node)

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
        wc = Revision(runtime, None, RevisionId(self.id, self._revision), old)
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
        return self._nodes[node_id]

    def get_revision(self, revision_id:RevisionId):
        return self._revisions[revision_id]

    def get_branch(self, branch_id:BranchId):
        return self._branches[branch_id]
