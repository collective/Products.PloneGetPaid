"""Unit tests for setting type as shippable.
"""

import unittest
from Testing.ZopeTestCase import ZopeDocTestSuite
from utils import optionflags

from base import PloneGetPaidTestCase

def test_make_premium():
 
    """Test that objects can be marked as premium
    
    >>> from Products.PloneGetPaid import interfaces
    >>> from getpaid.core import interfaces as coreInterfaces 

    Create a document object.    
    >>> self.setRoles(('Manager',))
    >>> id = self.portal.invokeFactory('Document', 'doc')
    >>> doc = self.portal.doc
    
    Check make sure it doesn't have the IPremiumMarker set already.
    >>> interfaces.IPremiumMarker.implementedBy(doc)
    False
    
    Make sure the Document class is not marked as Premium Content yet.
    >>> from Acquisition import aq_base
    >>> docClass = aq_base(doc).__class__
    >>> coreInterfaces.IPremiumContent.providedBy(docClass)
    False
    
    >>> options = interfaces.IGetPaidManagementOptions(self.portal)
    >>> options.premium_types
    []
    
    >>> options.premium_types = ['Document']
    >>> options.premium_types
    ['Document']
    
    >>> from Products.Five.utilities.marker import mark
    
    Mark the document class as premium content
    >>> mark(docClass, coreInterfaces.IPremiumContent)
    >>> coreInterfaces.IPremiumContent.providedBy(docClass)
    True
    
    Mark the test document as premium
    >>> mark(doc, interfaces.IPremiumMarker)
    >>> interfaces.IPremiumMarker.providedBy(doc)
    True
    
    """



def test_suite():
    return unittest.TestSuite((
            ZopeDocTestSuite(test_class=PloneGetPaidTestCase,
                             optionflags=optionflags),
        ))
