from functools import reduce
from operator import getitem

from werkzeug.exceptions import HTTPException, NotFound
from werkzeug.wrappers import Request
from werkzeug import routing

from yggdrasil.record import Record

class WebApp:
    def __init__(self, urlmap, namespace):
        self.urlmap = urlmap
        self.namespace = namespace

    def dispatch(self, request):
        adapter = self.urlmap.bind_to_environ(request.environ)
        try:
            path, values = adapter.match()
        except HTTPException as error:
            return error
        segments = path.split(".")
        endpoint = reduce(getitem, segments, self.namespace)
        request.urls = adapter
        try:
            return endpoint(request, **values)
        except HTTPException as error:
            return error

    def wsgi_app(self, environ, start_response):
        request = Request(environ)
        response = self.dispatch(request)
        return response(environ, start_response)

    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)

class Rules(routing.RuleFactory):
    def __init__(self, *rules):
        self.rules = rules

    def get_rules(self, map):
        for rulefactory in self.rules:
            for rule in rulefactory.get_rules(map):
                rule = rule.empty()
                yield rule

class Wrapper:
    def __init__(self, method, content):
        self.method = method
        self.content = content

    def __getitem__(self, name):
        next = self.content[name]
        if next is None:
            raise KeyError(name)
        return Wrapper(self.method, next)

    def __call__(self, *args, **kwargs):
        return self.method(self.content(*args, **kwargs))
