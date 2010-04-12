"""Unit test for payment processing.
"""

import unittest
from Testing.ZopeTestCase import ZopeDocTestSuite
from utils import optionflags

from base import PloneGetPaidTestCase

def createPayableType():
    pass

def setupCart():
    """Test that a cart can be instantiated

    >>> from zope.component import getUtility
    >>> from getpaid.core.interfaces import IShoppingCartUtility
    >>> cart_util = getUtility(IShoppingCartUtility)
    

    """

def test_payments():
    """Test that payments can be processed.
    
    >>> self.setRoles(('Manager',))

    """
    

def test_suite():
    return unittest.TestSuite((
            ZopeDocTestSuite(test_class=PloneGetPaidTestCase,
                             optionflags=optionflags),
        ))
