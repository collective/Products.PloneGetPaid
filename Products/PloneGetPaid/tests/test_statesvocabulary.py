"""Test of make payable functionality

These tests verify that content classes can be marked as payable
and that they receive the payable functlionality when they are
marked as such
"""

import unittest
from Testing.ZopeTestCase import ZopeDocTestSuite

from base import PloneGetPaidTestCase
from utils import optionflags

class TestStatesVocabulary(PloneGetPaidTestCase):

    def test_columbia_district(self):
        """Test that objects can be marked as payable

        >>> from zope.app import zapi
        >>> from Products.PloneGetPaid.interfaces import ICountriesStates

        >>> utility = zapi.getUtility(ICountriesStates)
        >>> states = utility.states(country='US')
        >>> ('US-DC', u'District of Columbia') in states
        True

        >>> len(states)
        58

        Now everything looks good...
        """

def test_suite():
    return unittest.TestSuite((
            ZopeDocTestSuite(test_class=PloneGetPaidTestCase,
                             optionflags=optionflags),
        ))
