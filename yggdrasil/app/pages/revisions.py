from werkzeug.exceptions import NotFound

from yggdrasil.record import Record
from yggdrasil.node import (
    RevisionId, 
    BranchId,
    NodeId,
    )

from . import Page

class Revisions(Page):
    def __init__(self, runtime):
        self.runtime = runtime

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

        return result

class RevisionsRefs(Revisions):
    def on_revision_by_id(self, request, rid): 
        result = super().on_revision_by_id(request, rid)

        result.refs = refs = Record()
        refs.branch = self.build_url(request, 
                "branches.branch_by_id", bid=result.rid.branch)

        refs.ancestors = Record()
        for number, rid in enumerate(result.ancestors):
            refs.ancestors[number] = self.build_url(request, 
                "revisions.revision_by_id", rid=rid)

        refs.nodes = Record()
        for number, node_ref in enumerate(result.nodes):
            refs.nodes[number] = self.build_url(request, 
                "nodes.by_uid", uid=NodeId(node_ref, result.rid))

        refs.nodes_refs = Record()
        for number, (ref, rid) in enumerate(result.nodes_refs.items()):
            refs.nodes_refs[number] = self.build_url(request, 
                "nodes.by_uid", uid=NodeId(ref, result.rid))

        return result
