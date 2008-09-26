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
        """Test that asking for US states contains Columbia as an example

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

    def test_special_values(self):
        """Test that there is 3 different special values for States

        >>> from zope.app import zapi
        >>> from Products.PloneGetPaid.interfaces import ICountriesStates
        >>> utility = zapi.getUtility(ICountriesStates)

        >>> len(utility.special_values)
        3

        >>> from zope.schema.interfaces import IVocabularyFactory
        >>> factory = zapi.getUtility(IVocabularyFactory,name=u'getpaid.states')
        >>> all_states_vocabulary = factory(None)
        >>> len(all_states_vocabulary)
        3752

        There is a special value to allow the user not select any state (when
        the field is not required) which is on the vocabulary

        >>> utility._allowed_no_values[0][0] in all_states_vocabulary
        True

        >>> us_states = utility.states('US',allow_no_values=True)
        >>> utility._allowed_no_values[0] in us_states
        True

        And another no_values that is not a vocabularty value that is used when
        the field is required

        >>> utility._no_values[0][0] in all_states_vocabulary
        False

        >>> us_states = utility.states('US',allow_no_values=False)
        >>> utility._no_values[0] in us_states
        True

        Finally check that there is a special value 'not applicable' in the vocabulary
        >>> utility._not_aplicable[0][0] in all_states_vocabulary
        True

        That not applicable value is used when the desired country has no states
        For example, for the Country named Niue
        >>> niue_states = utility.states('NU')
        >>> len(niue_states)
        1
        >>> utility._not_aplicable[0] in niue_states
        True
        """


def test_suite():
    return unittest.TestSuite((
            ZopeDocTestSuite(test_class=PloneGetPaidTestCase,
                             optionflags=optionflags),
        ))
