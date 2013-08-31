if __name__ == '__main__' and __package__ is None:
    import sys, os
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, parent_dir)
    import yggdrasil.app
    __package__ = str("yggdrasil.app")
    del sys, os

from functools import reduce
from operator import getitem

from werkzeug.exceptions import HTTPException, NotFound
from werkzeug.wrappers import Request, Response

from yggdrasil.node import Runtime, BoilerPlate
from .config import load_config

class WebApp(object):
    def __init__(self, urlmap, namespace, renderer):
        self.urlmap = urlmap
        self.renderer = renderer
        self.namespace = namespace

    def dispatch(self, request):
        adapter = self.urlmap.bind_to_environ(request.environ)
        try:
            path, values = adapter.match()
        except HTTPException as error:
            return error
        segments = path.split(".")
        endpoint = reduce(getitem, segments, self.namespace)
        try:
            data = endpoint(request, **values)
            body = self.renderer(data)
            return Response(body)
        except HTTPException as error:
            return error

    def wsgi_app(self, environ, start_response):
        request = Request(environ)
        response = self.dispatch(request)
        return response(environ, start_response)

    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)

def parse_args():
    import argparse

    parser = argparse.ArgumentParser(description='Repository web application.')
    
    parser.add_argument('-c', '--config', 
        dest='config', help='path to config file (should be yaml)')

    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    config = load_config(args.config)

    server_config = dict(
        hostname="127.0.0.1",
        port=5000,
        )
    server_config.update(config.pop("serving", {}))
    server_config['application'] = WebApp(**config)
    server_config['extra_files'] = [
        args.config,
        ]

    from werkzeug.serving import run_simple
    run_simple(**server_config)