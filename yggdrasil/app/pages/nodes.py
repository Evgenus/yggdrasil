from werkzeug.exceptions import NotFound

from yggdrasil.record import Record
from yggdrasil.node import NodeId, NodeRef
from yggdrasil.utils import ReadOnlyDict

from . import Page

class Nodes(Page):
    def __init__(self, runtime):
        self.runtime = runtime

    def on_by_uid(self, request, uid):
        uid = NodeId.from_string(uid)
        node = self.runtime.get_node(uid)
        if node is None:
            raise NotFound()

        result = Record()
        result["="] = type(node).__name__
        result.ref = node.ref
        result.data = node.content

        return result

class NodesRefs(Nodes):
    def inspect(self, request, revision, value):
        if isinstance(value, NodeRef):
            uid = NodeId(value, revision.search(value).id)
            return self.build_url(request, "nodes.by_uid", uid=uid)
        elif isinstance(value, tuple):
            result = Record()
            for number, subvalue in enumerate(value):
                subinspect = self.inspect(request, revision, subvalue)
                if subinspect is not None:
                    result[number] = subinspect
            if result: return result
        elif isinstance(value, ReadOnlyDict):
            result = Record()
            for name, subvalue in value.items():
                subinspect = self.inspect(request, revision, subvalue)
                if subinspect is not None:
                    result[name] = subinspect
            if result: return result

    def on_by_uid(self, request, uid):
        result = super().on_by_uid(request, uid)

        uid = NodeId.from_string(uid)
        revision = self.runtime.get_revision(uid.revision)

        result.refs = refs = Record()
        for name, value in result.data.items():
            inspected = self.inspect(request, revision, value)
            if inspected is not None:
                refs[name] = inspected

        return result
