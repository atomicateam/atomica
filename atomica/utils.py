import sciris as sc
from .system import NotAllowedError

class NamedItem(object):
    def __init__(self,name=None):
        if name is None:
            name = '<unnamed>'
        self.name = name
        self.created = sc.now()
        self.modified = sc.now()

    def copy(self, name=None):
        x = sc.dcp(self)
        if name is not None:
            x.name = name
        return x

    def __repr__(self):
        return sc.prepr(self)

class NDict(sc.odict):
    def __init__(self, *args, **kwargs):
        sc.odict.__init__(self, *args, **kwargs)
        return None

    def __setitem__(self, key, item):
        # Store an item in the NDict with an explicitly provided key. If the item is a NamedItem
        # then the name of the item will be automatically synchronized - otherwise, it will just behave
        # like a normal odict
        sc.odict.__setitem__(self, key, item)

        # If it is a NamedItem, then synchronize the name of the object with the specified key
        if isinstance(item,NamedItem):
            item.name = key
            item.modified = sc.now()
        return None
    
    def append(self, value):
        # Insert a NamedItem into the NDict by using the name of the item as the key. Of course this only
        # works for NamedItems, otherwise you have to explicitly provide the key
        if not isinstance(value,NamedItem):
            raise NotAllowedError('Can only automatically get the name from NamedItems. Instead of `x.append(y)` you need `x["name"]=y`')
        key = value.name
        sc.odict.append(self, key=key, value=value)
        return None

    def copy(self,old,new):
        sc.odict.copy(self,old,new)
        if isinstance(self[new],NamedItem):
            self[new].name=new
        return None

