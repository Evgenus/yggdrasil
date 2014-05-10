'''
Holding Record class.
'''

__all__ = [
    'Record',
    ]

from collections import OrderedDict

class Record(OrderedDict):
    """
    This class is derived from dict.
    Gives access to items as if they are attributes.
    """

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(key)

    def __setattr__(self, key, value):
        if "__" in key:
            OrderedDict.__setattr__(self, key, value)
        else:
            self.__setitem__(key, value)

    def __delattr__(self, key):
        self.__delitem__(key)

    def setvalue(self, key, value):
        "Set's value of a key and returns that value"
        self[key] = value
        return value

    def copy(self):
        'Creates a shallow copy of instance'
        return self.__class__(self)

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, dict.__repr__(self))