
from persistent import Persistent
from BTrees.OOBTree import OOBTree
from zope import interface

#from getpaid.core import interfaces
from zope.container.btree import BTreeContainer

import interfaces


class AddressBook(BTreeContainer):
    interface.implements(interfaces.IAddressBook)


class AddressBookUtility(Persistent):
    interface.implements(interfaces.IAddressBookUtility)

    def __init__(self):
        self._addresses = OOBTree()

    def get(self, uid, create=True):
        if uid not in self._addresses:
            if not create:
                return
            self._addresses[uid] = book = AddressBook()
            book.__name__ = uid
        return self._addresses[uid]

    def destroy(self, uid):
        if uid not in self._addresses:
            return
        del self._addresses[uid]

    def manage_fixupOwnershipAfterAdd(self):
        pass

#EOF
