from werkzeug.exceptions import NotFound
from yggdrasil.node import BranchId, RevisionId

from . import Page

class Branches(Page):
    def __init__(self, runtime):
        self.runtime = runtime

    def on_all_branches(self, request): 
        branches = list(self.runtime.get_branches())
        result = dict(
            branches=branches,
            )
        return result

    def on_branch_by_id(self, request, bid):
        branch = self.runtime.get_branch(BranchId(bid))
        if branch is None:
            raise NotFound()
        result = dict(
            bid=branch._bid,
            revision=branch._revision,
            wc=branch._wc,
            data=branch.__dict__,
            )
        return result

    def on_all_branch_revisions(self, request, bid):
        branch = self.runtime.get_branch(BranchId(bid))
        if branch is None:
            raise NotFound()
        return list(self.runtime.get_revisions(bid))

    def on_branch_revision_by_number(self, request, bid, number):
        rid = RevisionId(BranchId(bid), int(number, 16))
        revision = self.runtime.get_revision(rid)
        if revision is None:
            raise NotFound()
        result = dict(
            rid=revision._rid,
            ancestors=revision._ancestors,
            nodes=list(revision._nodes),
            refs=list(revision._refs.keys()),
            finished=revision._finished,
            )
