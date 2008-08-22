"""
upgrade addressbook storage
"""

from Products.PloneGetPaid.interfaces import IAddressBookUtility
from zope import component

def evolve( portal ):
    utility = component.getUtility( IAddressBookUtility )
    for book in utility._addresses.values():
        storage = book._SampleContainer__data
        if isinstance( storage, dict ):
            book._SampleContainer__data = book._newContainerData()
            
