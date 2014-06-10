from functools import reduce
from operator import getitem
from inspect import getdoc

from werkzeug.exceptions import NotFound

from yggdrasil.record import Record

from . import Page

class Root(Page):
    def __init__(self, urlmap):
        self.urlmap = urlmap

    def on_intro(self, request):
        """
        This page shows current routing table with endpoints and descriptions.
        """

        result = Record()
        result.rules = rules = Record()
        for rule in self.urlmap.iter_rules():
            key = rule.rule
            value = dict(
                endpoint=rule.endpoint,
                )
            segments = rule.endpoint.split(".")
            try:
                endpoint = reduce(getitem, segments, self)
            except KeyError:
                endpoint = None
            if rule.methods is not None:
                value["methods"] = tuple(rule.methods)
            description = getdoc(endpoint)
            if description is not None:
                value["description"] = description
            try:
                if True:
                    value["ref"] = self.build_url(request, rule.endpoint)
            except: pass
            rules[key] = value

        return result