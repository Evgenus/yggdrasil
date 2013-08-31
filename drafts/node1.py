import uuid
import weakref
import ast

from .utils import (
    undefined,
    )

"""

node-id: instance:branch:version
node:
    array of acpects:
        isinstance

"""

class Aspect(object):
    __slots__ = "__node__", "__name__", "__describer__", "__items__"
    def __init__(self, *args, **kwargs):
        node, name, describer = args
        self.__node__ = weakref.proxy(node)
        self.__name__ = name
        self.__describer__ = describer
        self.__items__ = dict(kwargs)

    def __getattr__(self, name):
        return self.__items__[name]

    def __setattr__(self, name, value):
        if name in type(self).__slots__:
            object.__setattr__(self, name, value)
        else:
            self.__items__[name] = value

    def isdescribedby(self, describer):
        return self.__describer__ is describer

    @property
    def describer(self):
        return self.__describer__

    def iterfields(self):
        return self.__items__.items()

class Node(object):
    def __init__(self):
        self.__uid__ = uuid.uuid4().hex
        self.__aspects__ = {}
        self.__order__ = []

    def add_aspect(self, *args, **kwargs):
        name, describer = args
        aspect = self.__aspects__.get(name, undefined)
        if aspect is not undefined:
            raise KeyError(name)
        aspect = Aspect(self, name, describer, **kwargs)
        self.__aspects__[name] = aspect
        self.__order__.append(name)
        return aspect

    def get_aspect(self, name):
        return self.__aspects__[name]        

    def del_aspect(self, name):
        del self.__aspects__[name]
        self.__order__.remove(name)

    def get_aspects_by_describer(self, describer):
        for name in self.__order__:
            aspect = self.__aspects__[name]
            if aspect.isdescribedby(describer):
                return aspect
        raise TypeError(describer)

    @classmethod
    def inject(cls, func):
        setattr(cls, func.__name__, func)

def boiler_plate():
    type_type = Node()
    field_type = Node()

    @Node.inject
    def add_field(node, _name, _type, _default=undefined):
        kwargs = dict(
            name=_name,
            type=_type,
            )
        if _default is not undefined:
            kwargs["default"] = _default
        node.add_aspect("field_" + _name, field_type, **kwargs)

    @Node.inject
    def declare_type(node, _abstract=undefined):
        kwargs = {}
        if _abstract is not undefined:
            kwargs["abstract"] = _abstract
        node.add_aspect("type", type_type, **kwargs)

    type_type.declare_type(True)
    type_type.add_field("abstract", "Boolean", False)

    field_type.declare_type()
    field_type.add_field("name", "String")
    field_type.add_field("type", "String")
    field_type.add_field("default", "Object", None)

    compilation_unit_type = Node()
    compilation_unit_type.declare_type()

    python_callable_type = Node()
    python_callable_type.declare_type()
    python_callable_type.add_field("code", "NodeReference")

    python_bytecode_type = Node()
    python_bytecode_type.declare_type()
    python_bytecode_type.add_field("co_argcount", "Integer")
    python_bytecode_type.add_field("co_kwonlyargcount", "Integer")
    python_bytecode_type.add_field("co_nlocals", "Integer")
    python_bytecode_type.add_field("co_stacksize", "Integer")
    python_bytecode_type.add_field("co_flags", "Integer")
    python_bytecode_type.add_field("co_code", "BytesArray")
    python_bytecode_type.add_field("co_consts", "Tuple")
    python_bytecode_type.add_field("co_names", "Tuple")
    python_bytecode_type.add_field("co_varnames", "Tuple")
    python_bytecode_type.add_field("co_filename", "String")
    python_bytecode_type.add_field("co_name", "String")
    python_bytecode_type.add_field("co_firstlineno", "Integer")
    python_bytecode_type.add_field("co_lnotab", "BytesArray")
    python_bytecode_type.add_field("co_freevars", "Tuple")
    python_bytecode_type.add_field("co_cellvars", "Tuple")

    call_site_type = Node()
    call_site_type.declare_type()
    call_site_type.add_field("function_node", "NodeReference")
    call_site_type.add_field("function_aspect_name", "String", "callable")
    call_site_type.add_field("output_node", "NodeReference")
    call_site_type.add_field("output_aspect_name", "String")
    call_site_type.add_field("output_aspect_type", "NodeReference")
    call_site_type.add_field("output_field_name", "String", None)

    @Node.inject
    def on_aspect_added(aspect):
        if aspect.isdescribedby(call_site_type):
            node = aspect.node

    argument_type = Node()
    argument_type.declare_type()
    argument_type.add_field("name", "String")
    argument_type.add_field("type", "String")
    argument_type.add_field("node_ref", "NodeReference", None)
    argument_type.add_field("value_int", "Integer", None)
    argument_type.add_field("value_string", "String", None)
    argument_type.add_field("value_bool", "Boolean", None)
    argument_type.add_field("value_float", "Float", None)

    python_compiler_ast_root = Node()
    python_compiler_ast_root.add_aspect("ast", compilation_unit_type,
        )

    python_compiler_code = Node()

    compile_source = """
def compile_ast(node):
    pass
    """
    compile_module_ast_root = ast.parse(compile_source)
    code = __builtins__["compile"](compile_module_ast_root, python_compiler_code.__uid__)
    print(ast.dump(compile_func_tree_root))
    code = compile.__code__

    python_compiler_code.add_aspect("code", python_bytecode_type,
        co_argcount=code.co_argcount,
        co_kwonlyargcount=code.co_kwonlyargcount,
        co_nlocals=code.co_nlocals,
        co_stacksize=code.co_stacksize,
        co_flags=code.co_flags,
        co_code=code.co_code,
        co_consts=code.co_consts,
        co_names=code.co_names,
        co_varnames=code.co_varnames,
        co_filename=python_compiler_code.__uid__,
        co_name=code.co_name,
        co_firstlineno=1,
        co_lnotab=b'',
        co_freevars=code.co_freevars,
        co_cellvars=code.co_cellvars,
        )

    python_compiler = Node()
    python_compiler.add_aspect("callable", python_callable_type,
        code=python_compiler_code,
        )

    python_compiler_compilation = Node()
    python_compiler_compilation.add_aspect("projection", call_site_type,
        function_node=python_compiler,
        function_aspect_name="callable",
        output_node=python_compiler_code,
        output_aspect_name="code",
        output_aspect_type=python_bytecode_type,
        )

    python_compiler_compilation.add_aspect("argument", argument_type,
        name="source",
        type="NodeReference",
        node_ref=python_compiler_ast_root,
        )
