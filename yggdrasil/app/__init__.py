from functools import reduce
from operator import getitem
from inspect import getdoc

from werkzeug.exceptions import HTTPException, NotFound
from werkzeug.wrappers import Request

from yggdrasil.record import Record

class WebApp(object):
    def __init__(self, urlmap, namespace, renderer, show_refs=False):
        self.urlmap = urlmap
        self.renderer = renderer
        self.namespace = namespace
        self.show_refs = show_refs

    def build_url(self, request, endpoint, **params):
        return request.urls.build(endpoint, params, force_external=True)

    def __getitem__(self, name):
        method = getattr(self, "on_" + name, None)
        if method is not None:
            return method
        return self.namespace[name]

    def dispatch(self, request):
        adapter = self.urlmap.bind_to_environ(request.environ)
        try:
            path, values = adapter.match()
        except HTTPException as error:
            return error
        segments = path.split(".")
        endpoint = reduce(getitem, segments, self)
        request.urls = adapter
        try:
            data = endpoint(request, **values)
        except HTTPException as error:
            return error
        return self.renderer(data)

    def wsgi_app(self, environ, start_response):
        request = Request(environ)
        response = self.dispatch(request)
        return response(environ, start_response)

    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)

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
                if self.show_refs:
                    value["ref"] = self.build_url(request, rule.endpoint)
            except: pass
            rules[key] = value


        return result