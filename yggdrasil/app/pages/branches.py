from werkzeug.exceptions import NotFound
from yggdrasil.node import BranchId

from . import Page

class Branches(Page):
    def __init__(self, runtime):
        self.runtime = runtime

    def on_all_branches(self, request): 
        branches = list(self.runtime.get_branches())
        result = dict(
            branches=branches,
            refs={number: request.urls.build(
                "branches.branch_by_id", 
                {"bid": bid}, 
                force_external=True
                ) for number, bid in enumerate(branches)},
            )
        return result

    def on_branch_by_id(self, request, bid):
        branch = self.runtime.get_branch(BranchId.from_string(bid))
        if branch is None:
            raise NotFound()
        result = dict(
            bid=branch.id,
            revision=branch._revision,
            wc=branch._wc,
            refs=dict(
                parent=request.urls.build("branches.all_branches", 
                    force_external=True),
                revisions=request.urls.build("branches.all_branch_revisions", 
                    {"bid": bid}, force_external=True)
                ),
            )
        return result

    def on_all_branch_revisions(self, request, bid):
        branch = self.runtime.get_branch(BranchId.from_string(bid))
        if branch is None:
            raise NotFound()
        revisions = list(self.runtime.get_revisions(branch.id))
        return dict(
            revisions=revisions,
            refs={number: request.urls.build(
                "revisions.revision_by_id", {"rid": rid},
                force_external=True
                ) for number, rid in enumerate(revisions)},
            )

