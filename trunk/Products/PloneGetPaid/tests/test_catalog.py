"""Test of make payable functionality

These tests verify that content classes can be marked as payable
and that they receive the payable functlionality when they are 
marked as such
"""

import unittest
from Testing.ZopeTestCase import ZopeDocTestSuite

from base import PloneGetPaidTestCase
from utils import optionflags

class TestCatalog(PloneGetPaidTestCase):
    
    def test_catalog(self):
        """Test that objects marked as payable are indexed
        
        >>> from Products.PloneGetPaid import interfaces
        >>> from getpaid.core import interfaces as coreInterfaces 
        >>> import Missing

        Create a document object.    
        >>> self.setRoles(('Manager',))
        >>> id = self.portal.invokeFactory('Document', 'doc')
        >>> doc = self.portal.doc
        
        Check make sure it doesn't have the IBuyableMarker set already.
        >>> interfaces.IBuyableMarker.implementedBy(doc)
        False
        
        >>> options = interfaces.IGetPaidManagementOptions(self.portal)
        >>> options.buyable_types
        []
        
        >>> options.buyable_types = ['Document']
        >>> options.buyable_types
        ['Document']
        
        >>> from Products.Five.utilities.marker import mark
        
        Mark the test document as buyable
        >>> mark(doc, interfaces.IBuyableMarker)
        >>> interfaces.IBuyableMarker.providedBy(doc)
        True
        
        Adapt to byuable
        >>> payable = coreInterfaces.IBuyableContent( doc )
        >>> payable.setProperty('price', 40.5)
        >>> payable.price == 40.5
        True
        
        >>> catalog = self.portal.portal_catalog
        >>> brain = catalog(getId='doc')[0]
        >>> brain.price in [None, Missing.Value]
        True
        
        >>> doc.reindexObject()
        >>> brain = catalog(getId='doc')[0]
        >>> brain.price
        40.5
        
        """

def test_suite():
    return unittest.TestSuite((
            ZopeDocTestSuite(test_class=PloneGetPaidTestCase,
                             optionflags=optionflags),
        ))
