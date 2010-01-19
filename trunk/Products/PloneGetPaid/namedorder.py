from persistent import Persistent
from BTrees.OOBTree import OOBTree
from zope import interface, schema

#from getpaid.core import interfaces
from zope.app.container.btree import BTreeContainer

import interfaces

class NamedOrderList(BTreeContainer):
    interface.implements(interfaces.INamedOrderList)

class NamedOrderUtility(Persistent):
    interface.implements(interfaces.INamedOrderUtility)

    def __init__(self):
        self._orders = OOBTree()

    def get(self, uid, create=True):
        if not self._orders.has_key(uid):
            if not create:
                return
            self._orders[uid] = orderlist = NamedOrderList() 
            orderlist.__name__ = uid
        return self._orders[uid]

    def destroy(self, uid):
        if not self._orders.has_key(uid):
            return
        del self._orders[uid]

    def manage_fixupOwnershipAfterAdd(self): pass
