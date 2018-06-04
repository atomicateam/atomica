from uuid import uuid4, UUID
from sciris.utils import dcp, defaultrepr
from atomica.system import NotAllowedError, NotFoundError, UnknownInputError


class NamedItem(object):
    def __init__(self,name):
        assert name is not None, 'Name cannot be None'
        self.name = name
        self.uid = uuid4()

    def copy(self,name):
        x = dcp(self)
        x.name = name
        x.uid = uuid4()
        return x

    def __repr__(self):
        return defaultrepr(self)

class SList(object):
    def __init__(self,allow_duplicates=False,enforce_type=None):
        self._objs = []
        self.allow_duplicates = allow_duplicates # Allow duplicate names, duplicate UIDs never allowed
        self.enforce_type = enforce_type

    def __getitem__(self, item):
        if isinstance(item,UUID):
            matches = [x for x in self._objs if x.uid == item]
        elif isinstance(item,int):
            return self._objs[item]
        elif isinstance(item,str):
            matches = [x for x in self._objs if x.name == item]
        else:
            raise NotAllowedError('Cannot index SList using something other than int, UUID, str')

        if not matches:
            raise NotFoundError()
        elif len(matches) == 1:
            return matches[0]
        else:
            return matches

    def __setitem__(self, key, item):

        if not isinstance(item,NamedItem):
            raise NotAllowedError("Only NamedItems can be stored in SLists")

        old_name = item.name
        item.name = key
        try:
            self.insert(item)
        except:
            item.name = old_name
            raise # re-raise the original error

    def __iter__(self):
        for x in self._objs:
            yield x

    def __delitem__(self, item):
        if item not in self:
            raise NotFoundError('Item not present in SList')

        if isinstance(item,UUID):
            self._objs = [x for x in self._objs if x.uid != item]
        elif isinstance(item,str):
            self._objs = [x for x in self._objs if x.name != item]
        elif isinstance(item,NamedItem):
            self._objs = [x for x in self._objs if x.uid != item.uid]
        else:
            UnknownInputError('Item to delete must be a NamedItem, a UID, or a name')

    def __contains__(self, item):
        # Returns True if UUID or name is in this SList
        # Note that the item itself will return False - the idea
        # is that if 'x in SList' returns True then 'SList[x]' will
        # return an object
        if isinstance(item,str):
            for x in self._objs:
                if x.name == item:
                    return True
            return False
        elif isinstance(item,UUID):
            for x in self._objs:
                if x.uid == item:
                    return True
            return False
        elif isinstance(item,NamedItem):
            return item.uid in self
        else:
            return False

    def rename(self,old_name,new_name):
        if new_name in self and not self.allow_duplicates:
            raise NotAllowedError('New name already exists')

        items = self[old_name]
        items = [items] if not isinstance(items, list) else items
        for x in items:
            x.name = new_name

    def __len__(self):
        return len(self._objs)

    def insert(self,item):
        # Insert a storable item - a storable item has both a name and a UID
        assert isinstance(item,NamedItem)

        if self.enforce_type:
            assert isinstance(item,self.enforce_type)
        if item in self:
            raise NotAllowedError('Item already present - cannot determine whether to rename or insert a copy') # NB. If the item is already present, it's not ambiguous whether the user wants to rename or insert a copy
        elif item.name in self and not self.allow_duplicates:
            raise NotAllowedError('An item with that name is already present')
        else:
            self._objs.append(item)

    def copy(self,old_name,new_name):
        # Copying item assigns new UUID to copies
        items = self[old_name]
        items = [items] if not isinstance(items,list) else items

        for y in items:
            x = y.copy(new_name)
            self.insert(x)

    def remove(self,item):
        del self[item]

    def __repr__(self):
        return '['+','.join(['{}:"{}"'.format(x.__class__.__name__,x.name) for x in self._objs]) + ']'

