from zope.dottedname.resolve import resolve

import yaml
from functools import reduce, partial
from collections import UserDict

__all__ = "load_config"

class Loader(yaml.Loader):
    dependencies = {}

def construct_from_mapping(cls, loader, node):
    mapping = loader.construct_mapping(node, True)
    return cls(**mapping)

def construct_from_sequence(cls, loader, node):
    sequence = loader.construct_sequence(node, True)
    return cls(*sequence)

def construct_from_string(cls, loader, node):
    scalar = str(loader.construct_scalar(node))
    return cls(scalar)

def construct_from_integer(cls, loader, node):
    scalar = int(loader.construct_scalar(node))
    return cls(scalar)

def resolve_builtin(loader, node):
    scalar = loader.construct_scalar(node)
    return resolve(scalar)

def get_dependency(name): 
    return Loader.dependencies[name]

def add_dependencies(**deps): 
    Loader.dependencies.update(deps)

class Config(UserDict): pass

class TypesTable(object):
    loader = Loader
    def __init__(self, **types):
        for name, declaration in types.items():
            self.register(name, **declaration)

    def register(self, _name, type, load):
        loader = partial(load, type)
        self.loader.add_constructor("!" + _name, loader)

Loader.add_constructor("!TypesTable", partial(construct_from_mapping, TypesTable))
Loader.add_constructor("!resolve", resolve_builtin)

def load_file(filename_or_stream):
    if isinstance(filename_or_stream, str):
        stream = open(filename_or_stream, "rt")
    else:
        stream = filename_or_stream

    return yaml.load(stream, Loader=Loader)

def load_config(filename_or_stream):
    if isinstance(filename_or_stream, str):
        stream = open(filename_or_stream, "rt")
    else:
        stream = filename_or_stream

    for part in list(yaml.load_all(stream, Loader=Loader)):
        if isinstance(part, Config):
            return part
