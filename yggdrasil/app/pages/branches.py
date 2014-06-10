from werkzeug.exceptions import NotFound

from yggdrasil.record import Record
from yggdrasil.node import BranchId

from . import Page

class Branches(Page):
    def __init__(self, runtime):
        self.runtime = runtime

    def on_all_branches(self, request): 
        branches = list(self.runtime.get_branches())

        result = Record()
        result.branches = branches

        return result

    def on_branch_by_id(self, request, bid):
        branch = self.runtime.get_branch(BranchId.from_string(bid))
        if branch is None:
            raise NotFound()

        result = Record()  
        result.bid = branch.id
        result.revision = branch.revision
        result.wc = branch.wc.id

        return result

    def on_all_branch_revisions(self, request, bid):
        branch = self.runtime.get_branch(BranchId.from_string(bid))
        if branch is None:
            raise NotFound()
        revisions = list(self.runtime.get_revisions(branch.id))

        result = Record()
        result.revisions = revisions

        return result

class BranchesRefs(Branches):
    def on_all_branches(self, request):
        result = super().on_all_branches(request)

        result.refs = refs = Record()
        refs.branches = Record()
        for number, bid in enumerate(result.branches):
            refs.branches[number] = self.build_url(request,
                "branches.branch_by_id", bid=bid)

        return result

    def on_branch_by_id(self, request, bid):
        result = super().on_branch_by_id(request, bid)

        result.refs = refs = Record()
        refs.list = self.build_url(request,
            "branches.all_branches")
        refs.revisions = self.build_url(request,
            "branches.all_branch_revisions", bid=bid)
        refs.wc = self.build_url(request,
            "revisions.revision_by_id", rid=result.wc)

        return result

    def on_all_branch_revisions(self, request, bid):
        result = super().on_all_branch_revisions(request, bid)

        result.refs = refs = Record()
        refs.revisions = Record()
        for number, rid in enumerate(result.revisions):
            refs.revisions[number] = self.build_url(request,
                "revisions.revision_by_id", rid=rid)

        return result
