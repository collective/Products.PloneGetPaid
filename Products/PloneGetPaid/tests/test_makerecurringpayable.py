"""Unit tests for setting type as shippable.
"""

import unittest
from Testing.ZopeTestCase import ZopeDocTestSuite
from utils import optionflags

from base import PloneGetPaidTestCase

def test_mark_object_recurringpayable():
    """ test that we can designate a page as recurringpayable

    >>> from Products.PloneGetPaid import interfaces
    >>> options = interfaces.IGetPaidManagementOptions(portal)
    >>> options.buyable_types = ['Document']

    Create a page to mark recurring payable

    >>> self.setRoles(('Manager'),)
    >>> self.portal.invokeFactory('Document', 'testpage')
    'testpage'

    >>> testpage = self.portal.testpage
    >>> IRecurringPaymentMarker = interfaces.IRecurringPaymentMarker
    >>> from Products.Five.utilities.marker import mark
    >>> mark(testpage, IRecurringPaymentMarker)
    >>> IRecurringPaymentMarker(testpage)
    <ATDocument at ...>
    >>> IRecurringPaymentMarker.providedBy( testpage )
    True
    """

def test_suite():
    return unittest.TestSuite((
            ZopeDocTestSuite(test_class=PloneGetPaidTestCase,
                             optionflags=optionflags),
        ))
