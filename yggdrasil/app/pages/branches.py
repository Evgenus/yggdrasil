from werkzeug.exceptions import NotFound
from yggdrasil.node import BranchId

from . import Page

class Branches(Page):
    def __init__(self, runtime):
        self.runtime = runtime

    def on_all_branches(self, request): 
        branches = list(self.runtime.get_branches())

        refs = {"branches": {}}
        for number, bid in enumerate(branches):
            refs["branches"][number] = self.build_url(request,
                "branches.branch_by_id", bid=bid)

        result = dict(
            branches=branches,
            refs=refs,
            )
        return result

    def on_branch_by_id(self, request, bid):
        branch = self.runtime.get_branch(BranchId.from_string(bid))
        if branch is None:
            raise NotFound()

        refs = {}
        refs["list"] = self.build_url(request,
            "branches.all_branches")
        refs["revisions"] = self.build_url(request,
            "branches.all_branch_revisions", bid=bid)

        result = dict(
            bid=branch.id,
            revision=branch._revision,
            wc=branch._wc,
            refs=refs,
            )
        return result

    def on_all_branch_revisions(self, request, bid):
        branch = self.runtime.get_branch(BranchId.from_string(bid))
        if branch is None:
            raise NotFound()
        revisions = list(self.runtime.get_revisions(branch.id))

        refs = {"revisions": {}}
        for number, rid in enumerate(revisions):
            refs["revisions"][number] = self.build_url(request,
                "revisions.revision_by_id", rid=rid)

        return dict(
            revisions=revisions,
            refs=refs,
            )

