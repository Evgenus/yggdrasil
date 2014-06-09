import json as libjson
from collections import UserString

from werkzeug.wrappers import Response

from yggdrasil.utils import (
    ReadOnlySet,
    ReadOnlyDict,
    )

class APIEncoder(libjson.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UserString):
            return str(obj)
        elif isinstance(obj, ReadOnlySet):
            return tuple(obj.__items__)
        elif isinstance(obj, ReadOnlyDict):
            return {str(k): v for k, v in obj.__items__.items()}
        else:
            return libjson.JSONEncoder.default(self, obj)

def renderer(data):
    body = libjson.dumps(data, 
        cls=APIEncoder, 
        indent=2)
    return Response(body, content_type="application/json")