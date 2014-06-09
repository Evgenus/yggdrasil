import collections

class Undefined(object):
    def __repr__(self):
        return "???"
undefined = Undefined()

class ReadOnlySet(collections.Set):
    def __init__(self, data):
        self.__items__ = data
    def __iter__(self):
        return iter(self.__items__)
    def __contains__(self, value):
        return value in self.__items__
    def __len__(self):
        return len(self.__items__)
    def __str__(self):
        return str(self.__items__)
    def __eq__(self, other):
        if not isinstance(other, collections.Set):
            return False
        for item in self:
            if item not in other:
                return False
        for item in other:
            if item not in self:
                return False
        return True
    def __ne__(self, other):
        return not self == other
    def __repr__(self):
        return "ReadOnlySet({!r})".format(self.__items__)

class ReadOnlyDict(collections.Mapping):
    def __init__(self, *args, **kwargs):
        if len(args) > 1:
            return ValueError("Invalid arguments")
        if len(args) == 1:
            self.__items__ = args[0]
            self.__items__.update(kwargs)
        else:
            self.__items__ = kwargs
    def __getitem__(self, key):
        return self.__items__[key]
    def __iter__(self):
        return iter(self.__items__)
    def __contains__(self, key):
        return key in self.__items__
    def __len__(self):
        return len(self.__items__)
    def keys(self):
        return self.__items__.keys()
    def items(self):
        return self.__items__.items()
    def values(self):
        return self.__items__.values()
    def get(self, name, default=None):
        return self.__items__.get(name, default)
    def __str__(self):
        return str(self.__items__)
    def __eq__(self, other):
        if not isinstance(other, collections.Mapping):
            return False
        for key, value in self.items():
            if value != other.get(key, undefined):
                return False
        for key, value in other.items():
            if value != self.get(key, undefined):
                return False
        return True
    def __ne__(self, other):
        return not self == other
    def __repr__(self):
        return "ReadOnlyDict({!r})".format(self.__items__)

class ProxySet(collections.MutableSet):
    def __init__(self, data=None):
        if data is None:
            data = set()
        self.__items__ = data
        self.__added__ = set()
        self.__removed__ = set()
    def __iter__(self):
        return iter(self.__items__)
    def __contains__(self, key):
        return key in self.__items__
    def __len__(self):
        return len(self.__items__)
    def add(self, value):
        self.__removed__.discard(value)
        self.__added__.add(value)
        self.__items__.add(value)
    def discard(self, value):
        if value in self.__items__:
            self.__removed__.add(value)
        self.__added__.discard(value)
        self.__items__.discard(value)

class ProxyListItem(object):
    def set(self, value):
        assert not self.removed
        if not self.inserted:
            if not self.changed:
                self.changed = True
                self.old = self.value
        self.value = value
    def delete(self):
        assert not self.removed
        if self.inserted:
            self.value = None
            return True
        self.removed = True
        if not self.changed:
            self.old = self.value
        else:
            self.changed = False
        self.value = None
        return False
    @classmethod
    def insert(cls, value):
        return cls(value, True)
    def __init__(self, value,
            inserted=False, 
            changed=False, 
            removed=False,
            old=None,
            ):
        self.value = value
        self.old = old
        self.inserted = inserted
        self.changed = changed
        self.removed = removed
    def __repr__(self):
        if self.inserted:
            return "Item(inserted, {!r})".format(self.value)
        if self.changed:
            return "Item(changed, {!r}, {!r})".format(self.value, self.old)
        if self.removed:
            return "Item(removed, {!r})".format(self.old)
        return "Item({!r})".format(self.value)

class ProxyList(collections.MutableSequence):
    def __init__(self, data=None):
        self.__items__ = []
        if data is not None:
            self.__length__ = len(data)
            for value in data:
                item = ProxyListItem(value)
                self.__items__.append(item)
        else:
            self.__length__ = 0
    def __iter__(self):
        for item in self.__items__:
            if item.removed: continue
            yield item.value
    def __contains__(self, value):
        for item in self:
            if value == item.value:
                return True
        return False
    def __len__(self):
        return self.__length__
    def __repr__(self):
        return "["+ ", ".join(repr(item) for item in self.__items__) + "]"
    def __eq__(self, other):
        if not isinstance(other, collections.Iterable):
            return False
        if len(v1) != len(v2):
            return False
        for v1, v2 in zip(self, other):
            if v1 != v2: return False
        return True
    def translate(self, index):
        iterator = iter(self.__items__)
        real = 0
        virtual = index
        while True:
            try:
                item = next(iterator)
            except StopIteration:
                if virtual > 0:
                    raise IndexError(index)
                break
            if not item.removed:
                if virtual == 0:  
                    break
                virtual -= 1
            real += 1
        return real
    def __getitem__(self, index):
        index = self.translate(index)
        return self.__items__[index].value
    def __setitem__(self, index, value):
        index = self.translate(index)
        self.__items__[index].set(value)
    def __delitem__(self, index):
        index = self.translate(index)
        self.__length__ -= 1
        if self.__items__[index].delete():
            del self.__items__[index]
    def insert(self, index, value):
        index = self.translate(index)
        item = ProxyListItem.insert(value)
        self.__items__.insert(index, item)
        self.__length__ += 1
    def iterdata(self):
        for item in self.__items__:
            yield item
        while True: yield None

class MergeResult(object): pass

"""
Conflicts:

      0 V I C R
    0 - - - - -
    V - - - - -
    I - - - - -
    C - - - X X
    R - - - X -
"""

class MergeConflict(MergeResult): pass
class RCMergeConflict(MergeConflict): pass
class CRMergeConflict(MergeConflict): pass
class CCMergeConflict(MergeConflict): pass

"""
Errors:

      0 V I C R
    0 - - - - -
    V - X - X X
    I - - - - -
    C - X - X X
    R - X - X X

"""

class MergeError(MergeResult): pass
class RRMergeError(MergeError): pass
class RCMergeError(MergeError): pass
class RVMergeError(MergeError): pass
class CRMergeError(MergeError): pass
class VRMergeError(MergeError): pass
class CCMergeError(MergeError): pass
class CVMergeError(MergeError): pass
class VCMergeError(MergeError): pass
class VVMergeError(MergeError): pass

class ComplettedMergeResult(MergeResult): pass

class ProxyListMerge(object):
    def __init__(self, list1, list2):
        self.list1 = list1
        self.list2 = list2
        self.iter1 = iter(list1.iterdata())
        self.iter2 = iter(list2.iterdata())
        self.item1 = next(self.iter1)
        self.item2 = next(self.iter2)
        self.result = []

    def take1(self):
        result.append(self.item1)
        self.item1 = next(self.iter1)
        self.item2 = next(self.iter2)

    def take2(self):
        result.append(self.item2)
        self.item1 = next(self.iter1)
        self.item2 = next(self.iter2)

    def push1(self):
        result.append(self.item1)
        self.item1 = next(self.iter1)

    def push2(self):
        result.append(self.item2)
        self.item2 = next(self.iter2)

    @classmethod
    def merge_one(self):
        if self.item1 is None: # 0?
            if self.item2 is None: # 00 
                return ComplettedMergeResult()
            self.push2()
        elif self.item2 is None: # 0?
            self.push1()
        elif self.item1.inserted: # I?
            self.push1()
        elif self.item2.inserted: # ?I
            self.push2()
        elif self.item1.removed: # R?
            if self.item2.removed: # RR
                if self.item1.old == self.item2.old:
                    self.take1()
                else:
                    return RRMergeError()
            elif self.item2.changed: # RC
                if self.item1.old == self.item2.old:
                    return RCMergeConflict()
                else:
                    return RCMergeError()                    
            else: # RV
                if self.item1.old == self.item2.value:
                    self.take2()
                else:
                    return RVMergeError()
        elif self.item2.removed: # ?R
            if self.item1.changed: # CR
                if self.item1.old == self.item2.old:
                    return CRMergeConflict()
                else:
                    return CRMergeError()
            else: # VR
                if self.item1.value == self.item2.old:
                    self.take2()
                else:
                    return VRMergeError()
        elif self.item1.changed: # C?
            if self.item2.changed: # CC
                if self.item1.old == self.item2.old:
                    return CCMergeConflict()
                else:
                    return CCMergeError()
            else: # CV
                if self.item1.value == self.item2.old:
                    self.take2()
                else:
                    return CVMergeError()
        if self.item2.changed: # VC
            if self.item1.value == self.item2.old:
                self.push1().pop()
            else:
                return VCMergeError()
        else:
            if self.item1.value == self.item2.value:
                self.push1().pop()
            else:
                return VVMergeError()

        raise RuntimeError("Unreachable code")

class ProxyDict(collections.MutableMapping):
    def __init__(self, data):
        self.fields = type(data)(data) # contains new changed or added values
        self.changed = {} # contains old changed values
        self.added = set() # contains keys for added values
        self.removed = {} # contains old removed values

    def __iter__(self):
        return iter(self.fields)

    def __len__(self):
        return len(self.fields)

    def __getitem__(self, key):
        value = self.fields.get(key, undefined)
        if value is undefined:
            raise KeyError(key)
        return value

    def __setitem__(self, key, value):
        old = self.fields.get(key, undefined)
        if old is undefined:
            old = self.removed.pop(key, undefined)
            if old is undefined:
                self.added.add(key)
            else:
                self.changed[key] = old
        else:
            if key not in self.added:
                self.changed.setdefault(key, old)
        self.fields[key] = value

    def __delitem__(self, key):
        old = self.fields.pop(key, undefined)
        if old is undefined:
            raise KeyError(key)
        if key in self.added:
            self.added.remove(key)
        else:
            old = self.changed.pop(key, old)
            self.removed[key] = old
