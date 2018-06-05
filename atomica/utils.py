import sciris.core as sc
from atomica.system import NotAllowedError


class NamedItem(object):
    def __init__(self,name=None):
        if name is None:
            name = '<unnamed>'
        self.name = name
        self.uid = sc.uuid()

    def copy(self, name=None):
        x = sc.dcp(self)
        if name is not None:
            x.name = name
        x.uid = sc.uuid()
        return x

    def __repr__(self):
        return sc.desc(self)


class SList(sc.odict):
    def __init__(self, *args, **kwargs):
        sc.odict.__init__(self, *args, **kwargs)
        return None

    def __setitem__(self, key, item):
        if not isinstance(item,NamedItem):
            raise NotAllowedError("Only NamedItems can be stored in SLists")
        item.name = key
        sc.odict.__setitem__(self, key, item)
        return None
    
    def insert(self, pos=None, key=None, value=None):
        if key is None:
            key = value.name
        else:
            value.name = key
        sc.odict.insert(self, pos=pos, key=key, value=value)
        return None



