"""Unit tests for manager interface.
"""

import unittest
from Testing.ZopeTestCase import ZopeDocTestSuite
from utils import optionflags

from base import PloneGetPaidTestCase

def test_add_to_cart():
    """Test that payments can be processed.
    
    >>> self.setRoles(('Manager',))

    """



def test_suite():
    return unittest.TestSuite((
            ZopeDocTestSuite(test_class=PloneGetPaidTestCase,
                             optionflags=optionflags),
        ))
