from werkzeug.exceptions import NotFound

from yggdrasil.record import Record
from yggdrasil.node import NodeId, NodeRef
from yggdrasil.utils import ReadOnlyDict

from . import Page

class Nodes(Page):
    def __init__(self, runtime, show_refs=False):
        self.runtime = runtime
        self.show_refs = show_refs

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
        uid = NodeId.from_string(uid)
        node = self.runtime.get_node(uid)
        if node is None:
            raise NotFound()

        result = Record()
        result.ref = node.ref
        result.data = node.content

        revision = self.runtime.get_revision(uid.revision)

        if self.show_refs:
            result.refs = refs = Record()
            for name, value in node.content.items():
                inspected = self.inspect(request, revision, value)
                if inspected is not None:
                    refs[name] = inspected

        return result
