"""
$Id$
"""

from config import PLONE3
# CMFonFive has been integrated in CMFCore since version 2.0, so in
# Plone 3.0 we do not depend on it anymore.
if PLONE3:
    _GETPAID_DEPENDENCIES_ = [ ]
else:
    _GETPAID_DEPENDENCIES_ = [ 'CMFonFive' ]

import os, sys
from Globals import package_home

import _patch

pkg_home = package_home( globals() )
lib_path = os.path.join( pkg_home, 'lib' )
if os.path.exists( lib_path ):
    sys.path.append( lib_path )
import catalog
import permissions
