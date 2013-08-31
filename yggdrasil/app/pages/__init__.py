class Page(object):
    def __getitem__(self, name):
        method = getattr(self, "on_" + name, None)
        if method is None:
            raise KeyError(name)
        return method
