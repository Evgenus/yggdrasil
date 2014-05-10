from . import Page
from werkzeug.exceptions import NotFound
from yggdrasil.node import (
    RevisionId, 
    BranchId,
    )

class Revisions(Page):
    def __init__(self, runtime):
        self.runtime = runtime

    def on_revision_by_id(self, request, rid): 
        rid = RevisionId.from_string(rid)
        revision = self.runtime.get_revision(rid)
        if revision is None:
            raise NotFound()
        nodes = list(revision._nodes)
        node_refs = list(revision._refs.keys())

        refs = {
            "ancestors": {},
            "nodes": {},
            "nodes_refs": {},
        }
        refs["branch"] = self.build_url(request, 
                "branches.branch_by_id", bid=rid.branch)
        for number, rid in enumerate(revision._ancestors):
            refs["ancestors"][number] = self.build_url(request, 
                "revisions.revision_by_id", rid=rid)
        for number, uid in enumerate(nodes):
            refs["nodes"][number] = self.build_url(request, 
                "nodes.by_uid", uid=uid)
        for number, uid in enumerate(node_refs):
            refs["nodes_refs"][number] = self.build_url(request, 
                "nodes.by_uid", uid=uid)

        result = dict(
            rid=revision.id,
            ancestors=revision._ancestors,
            nodes=nodes,
            nodes_refs=node_refs,
            finished=revision._finished,
            refs=refs,
            )
        return result

    def on_all_revision_nodes(self): 
        pass
