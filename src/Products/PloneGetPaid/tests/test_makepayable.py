"""Test of make payable functionality

These tests verify that content classes can be marked as payable
and that they receive the payable functlionality when they are 
marked as such
"""

import unittest
from Testing.ZopeTestCase import ZopeDocTestSuite

from base import PloneGetPaidTestCase
from utils import optionflags

class TestMakePayable(PloneGetPaidTestCase):
    
    def test_mark_object_payable(self):
        """Test that objects can be marked as payable
        
        >>> from Products.PloneGetPaid import interfaces
        >>> from getpaid.core import interfaces as coreInterfaces 

        Create a document object.    
        >>> self.setRoles(('Manager',))
        >>> id = self.portal.invokeFactory('Document', 'doc')
        >>> doc = self.portal.doc
        
        Check make sure it doesn't have the IBuyableMarker set already.
        >>> interfaces.IBuyableMarker.implementedBy(doc)
        False
        
        Make sure the Document class is not marked as Buyable Content yet.
        >>> from Acquisition import aq_base
        >>> docClass = aq_base(doc).__class__
        >>> coreInterfaces.IBuyableContent.providedBy(docClass)
        False
        
        >>> options = interfaces.IGetPaidManagementOptions(self.portal)
        >>> options.buyable_types
        []
        
        >>> options.buyable_types = ['Document']
        >>> options.buyable_types
        ['Document']
        
        >>> from Products.Five.utilities.marker import mark
        
        Mark the document class as buyable content
        >>> mark(docClass, coreInterfaces.IBuyableContent)
        >>> coreInterfaces.IBuyableContent.providedBy(docClass)
        True
        
        Mark the test document as buyable
        >>> mark(doc, interfaces.IBuyableMarker)
        >>> interfaces.IBuyableMarker.providedBy(doc)
        True
        
        """

def test_suite():
    return unittest.TestSuite((
            ZopeDocTestSuite(test_class=PloneGetPaidTestCase,
                             optionflags=optionflags),
        ))
