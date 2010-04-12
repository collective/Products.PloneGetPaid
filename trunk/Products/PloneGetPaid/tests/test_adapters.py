"""Integration tests for adapter registrations.

These tests ensure that the various adapter registrations are in effect,
not the exact functionality they promise. They utilise the full PloneTestCase
bases, since we are actually testing that the registrations are properly loaded
at Zope start-up, not just that they could be made to work (e.g. using the
zope testing API)
"""

import unittest
from Testing.ZopeTestCase import ZopeDocTestSuite

from base import PloneGetPaidTestCase
from utils import optionflags

def test_payable():
    """Check that we can declare an object buyable
    
    >>> from getpaid.core.interfaces import IPayable
    
    """
    
def test_donation():
    """Check that we can declare an object buyable

    >>> from getpaid.core.interfaces import IDonationContent

    """
    
def test_suite():
    return unittest.TestSuite((
            ZopeDocTestSuite(test_class=PloneGetPaidTestCase,
                             optionflags=optionflags),
        ))
