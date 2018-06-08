import sciris.core as sc
from atomica.core.system import NotAllowedError, NotFoundError, AtomicaInputError


class NamedItem(object):
    def __init__(self,name=None):
        if name is None:
            name = '<unnamed>'
        self.name = name
        self.uid = sc.uuid()

    def __copy__(self, name=None):
        x = sc.dcp(self)
        if name is not None:
            x.name = name
        x.uid = sc.uuid()
        return x

    def __deepcopy__(self, name=None):
        x = self.__copy__(name=name)
        return x

    def __repr__(self):
        return sc.desc(self)


class NDict(sc.odict):
    def __init__(self, *args, **kwargs):
        sc.odict.__init__(self, *args, **kwargs)
        return None

    def __setitem__(self, key, item):
        if not isinstance(item,NamedItem):
            raise NotAllowedError("Only NamedItems can be stored in SLists")
        sc.odict.__setitem__(self, key, item)
        item.name = key
        return None
    
    def append(self, value):
        key = value.name
        sc.odict.append(self, key=key, value=value)
        return None



