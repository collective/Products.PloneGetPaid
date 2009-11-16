"""Unit test for sessions methods
"""

import unittest

from Testing.ZopeTestCase import ZopeDocTestSuite
from utils import optionflags
from base import PloneGetPaidTestCase

class TestSessions(PloneGetPaidTestCase):

      def test_set_and_get_came_from_url(self):
        """
        We can use sessions to store and get a came_from url relevant to
        the context passed.

        >>> from Products.PloneGetPaid import sessions
        >>> sessions.set_came_from_url(self.portal)
        >>> sessions.get_came_from_url(self.portal)
        'http://nohost/plone'
        """

def test_suite():
    return unittest.TestSuite((
            ZopeDocTestSuite(test_class=TestSessions,
                             optionflags=optionflags),
        ))

