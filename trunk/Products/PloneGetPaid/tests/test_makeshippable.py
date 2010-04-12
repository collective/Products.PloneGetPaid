"""Test of make payable functionality

These tests verify that content classes can be marked as payable
and that they receive the payable functlionality when they are 
marked as such
"""

import unittest
from Testing.ZopeTestCase import ZopeDocTestSuite

from base import PloneGetPaidTestCase
from utils import optionflags
from Products.PloneGetPaid import interfaces
    
def test_mark_object_shippable(self):
    """ test that we can designate a page as shippable
    
    >>> from Products.PloneGetPaid import interfaces
    >>> options = interfaces.IGetPaidManagementOptions(portal)
    >>> options.shippable_types = ['Document']
    
    Create a page to mark payable
    
    >>> self.setRoles(('Manager'),)
    >>> self.portal.invokeFactory('Document', 'testpage')
    'testpage'
    
    >>> testpage = self.portal.testpage
    >>> IShippableMarker = interfaces.IShippableMarker
    >>> from Products.Five.utilities.marker import mark
    >>> mark(testpage, IShippableMarker)
    >>> IShippableMarker(testpage)
    <ATDocument at ...>
    """
    
def test_suite():
    return unittest.TestSuite((
            ZopeDocTestSuite(test_class=PloneGetPaidTestCase,
                             optionflags=optionflags),
        ))

