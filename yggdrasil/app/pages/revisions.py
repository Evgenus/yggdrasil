from werkzeug.exceptions import NotFound

from yggdrasil.record import Record
from yggdrasil.node import (
    RevisionId, 
    BranchId,
    NodeId,
    )

from . import Page

class Revisions(Page):
    def __init__(self, runtime, show_refs=False):
        self.runtime = runtime
        self.show_refs = show_refs

    def on_revision_by_id(self, request, rid): 
        rid = RevisionId.from_string(rid)
        revision = self.runtime.get_revision(rid)
        if revision is None:
            raise NotFound()

        result = Record()
        result.rid = revision.id
        result.finished = revision.finished
        result.ancestors = revision.ancestors
        result.nodes = revision.nodes
        result.nodes_refs = revision.refs

        if self.show_refs:
            result.refs = refs = Record()
            refs.branch = self.build_url(request, 
                    "branches.branch_by_id", bid=rid.branch)

            refs.ancestors = Record()
            for number, rid in enumerate(revision.ancestors):
                refs.ancestors[number] = self.build_url(request, 
                    "revisions.revision_by_id", rid=rid)

            refs.nodes = Record()
            for number, node_ref in enumerate(revision.nodes):
                refs.nodes[number] = self.build_url(request, 
                    "nodes.by_uid", uid=NodeId(node_ref, revision.id))

            refs.nodes_refs = Record()
            for number, (ref, rid) in enumerate(revision.refs.items()):
                refs.nodes_refs[number] = self.build_url(request, 
                    "nodes.by_uid", uid=NodeId(ref, rid))

        return result
