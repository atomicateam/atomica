from uuid import uuid4, UUID
from copy import deepcopy as dcp

class NotFoundError(Exception): pass
class NotAllowedError(Exception): pass

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

class SList(object):
    def __init__(self,allow_duplicates=False,enforce_type=None):
        self._objs = []
        self.allow_duplicates = allow_duplicates # Allow duplicate names, duplicate UIDs never allowed
        self.enforce_type = None

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
        raise NotAllowedError('Can only insert items via .insert()')

    def __iter__(self):
        for x in self._objs:
            yield x

    def __delitem__(self, item):
        if isinstance(item,UUID):
            self._objs = filter(lambda x: x.uid != item, self._objs)
        elif isinstance(item,str):
            self._objs = filter(lambda x: x.name != item, self._objs)
        else:
            self._objs.pop(item)

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
            raise NotAllowedError('Item already present')
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
        return str(self._objs)


## Example usage below - This can be moved to documentation later
if __name__ == '__main__':
    # f_string = 'exp(x)+y**2'
    # fcn,dep_list = parse_function(f_string)
    # print(dep_list)
    # deps = {'x':1,'y':2}
    # print(fcn(**deps))
    # print(fcn(x=1,y=3)) # The use of **deps means you can write out keyword arguments for `fcn` directly
    x = SList()
    x.insert(NamedItem('a'))
    x.insert(NamedItem('b'))



