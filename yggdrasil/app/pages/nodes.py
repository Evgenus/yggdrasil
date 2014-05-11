from yggdrasil.record import Record
from yggdrasil.node import NodeId

from . import Page

class Nodes(Page):
    def __init__(self, runtime, show_refs=False):
        self.runtime = runtime
        self.show_refs = show_refs

    def on_by_uid(self, request, uid):
        uid = NodeId.from_string(uid)
        node = self.runtime.get_node(uid)
        if node is None:
            raise NotFound()

        request = Record()
        request.ref = node.ref
        request.data = node.content
        return request
        