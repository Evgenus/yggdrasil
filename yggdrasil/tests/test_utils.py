import unittest
from ..utils import *

class TestProxyDict(unittest.TestCase):
    def check(self, d, added, changed, removed):
        self.assertEquals(d.added, set(added), "added")
        self.assertEquals(d.changed, changed, "changed")
        self.assertEquals(d.removed, removed, "removed")

    def test_empty(self):
        d = ProxyDict()
        self.check(d, {}, {}, {})

    def test_added_once(self):
        d = ProxyDict()
        d['a'] = 1
        self.assertEquals(d['a'], 1)
        self.check(d, {"a"}, {}, {})

    def test_added_twice(self):
        d = ProxyDict()
        d['a'] = 1
        d['a'] = 2
        self.assertEquals(d['a'], 2)
        self.check(d, {"a"}, {}, {})

    def test_added_removed(self):
        d = ProxyDict()
        d['a'] = 1
        del d['a']
        self.check(d, {}, {}, {})

    def test_added_removed_added(self):
        d = ProxyDict()
        d['a'] = 1
        del d['a']
        d['a'] = 2
        self.check(d, {"a"}, {}, {})

    def test_changed_once(self):
        d = ProxyDict({"a":0})
        d['a'] = 1
        self.assertEquals(d['a'], 1)
        self.check(d, {}, {"a":0}, {})

    def test_changed_twice(self):
        d = ProxyDict({"a":0})
        d['a'] = 1
        d['a'] = 2
        self.assertEquals(d['a'], 2)
        self.check(d, {}, {"a":0}, {})

    def test_changed_removed(self):
        d = ProxyDict({"a":0})
        d['a'] = 1
        del d['a']
        self.check(d, {}, {}, {"a":0})

    def test_changed_removed_changed(self):
        d = ProxyDict({"a":0})
        d['a'] = 1
        del d['a']
        d['a'] = 2
        self.check(d, {}, {"a":0}, {})

class TestProxyList(unittest.TestCase):
    def test_remove_existing(self):
        l = ProxyList(list("ABC"))
        del l[1]
        self.assertEquals(l[0], "A")
        self.assertEquals(l[1], "C")
        self.assertEquals(len(l), 2)

    def test_insert_new_remove_existing(self):
        l = ProxyList(list("ABC"))
        l.insert(2, "D")
        self.assertEquals(l[0], "A")
        self.assertEquals(l[1], "B")
        self.assertEquals(l[2], "D")
        self.assertEquals(l[3], "C")
        self.assertEquals(len(l), 4)
        del l[1]
        self.assertEquals(l[0], "A")
        self.assertEquals(l[1], "D")
        self.assertEquals(l[2], "C")
        self.assertEquals(len(l), 3)

    def test_remove_existing_change_existing(self):
        l = ProxyList(list("ABC"))
        del l[1]
        self.assertEquals(l[0], "A")
        self.assertEquals(l[1], "C")
        l[0] = "D"
        l[1] = "E"
        self.assertEquals(l[0], "D")
        self.assertEquals(l[1], "E")
        self.assertEquals(len(l), 2)

    def test_insert_new_remove_new_tail(self):
        l = ProxyList(list("AB"))
        l.insert(2, "D")
        self.assertEquals(len(l), 3)
        del l[2]
        self.assertEquals(l[0], "A")
        self.assertEquals(l[1], "B")
        self.assertEquals(len(l), 2)

    def test_insert_new_remove_new_body(self):
        l = ProxyList(list("ABC"))
        l.insert(2, "D")
        self.assertEquals(len(l), 4)
        del l[2]
        self.assertEquals(l[0], "A")
        self.assertEquals(l[1], "B")
        self.assertEquals(l[2], "C")
        self.assertEquals(len(l), 3)

"""
    def test_merge_1(self):
        l1 = ProxyList(list("ABCDEF"))
        l2 = ProxyList(list("ABCDEF"))
        m = ProxyListMerge(l1, l2)
        while True:
            result = m.merge_one()
            if isinstance(result, ComplettedMergeResult):
                break
        self.assertEquals(l, list("ABCDEF"))

    def test_merge_2(self):
        l1 = ProxyList(list("ABCDEF"))
        l2 = ProxyList(list("ABCDEF"))
        l1.insert(2, "M")
        l2.insert(3, "N")
        l = ProxyList.merge(l1, l2)
        self.assertEquals(l, list("ABMCNDEF"))

    def test_merge_3(self):
        l1 = ProxyList(list("ABCDEF"))
        l2 = ProxyList(list("ABCDEF"))
        del l1[2]
        del l2[4]
        l = ProxyList.merge(l1, l2)
        self.assertEquals(l, list("ABDF"))
        assert False
"""
