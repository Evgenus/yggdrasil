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
        result = dict(
            rid=revision.id,
            ancestors=revision._ancestors,
            nodes=list(revision._nodes),
            refs=list(revision._refs.keys()),
            finished=revision._finished,
            )
        return result

    def on_all_revision_nodes(self): 
        pass
