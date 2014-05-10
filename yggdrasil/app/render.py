import json as libjson
from collections import UserString

from werkzeug.wrappers import Response

from yggdrasil import node

class APIEncoder(libjson.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UserString):
            return str(obj)
        return libjson.JSONEncoder.default(self, obj)

def json(data):
    body = libjson.dumps(data, 
    	cls=APIEncoder, 
    	indent=2, 
    	sort_keys=True)
    return Response(body, content_type="application/json")