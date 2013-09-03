import json as libjson
from collections import UserString

from yggdrasil import node

class APIEncoder(libjson.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UserString):
            return str(obj)
        return libjson.JSONEncoder.default(self, obj)

def json(data):
    return libjson.dumps(data, 
    	cls=APIEncoder, 
    	indent=2, 
    	sort_keys=True)
