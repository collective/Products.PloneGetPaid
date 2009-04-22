import os, sys

import glob
import doctest
import unittest
from Globals import package_home
from base import PloneGetPaidFunctionalTestCase
from Testing.ZopeTestCase import FunctionalDocFileSuite as Suite

from Products.PloneGetPaid.config import GLOBALS

OPTIONFLAGS = (doctest.REPORT_ONLY_FIRST_FAILURE |
               doctest.ELLIPSIS |
               doctest.NORMALIZE_WHITESPACE)

def list_doctests():
    home = package_home(GLOBALS)
    return [filename for filename in
            glob.glob(os.path.sep.join([home, '*.txt']))]

def test_suite():
    filenames = list_doctests()
    return unittest.TestSuite(
        [Suite(os.path.basename(filename),
               optionflags=OPTIONFLAGS,
               package='Products.PloneGetPaid',
               test_class=PloneGetPaidFunctionalTestCase)
         for filename in filenames]
        )

if __name__ == '__main__':
    framework()