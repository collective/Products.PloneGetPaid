"""
$Id$
"""

import os, sys
from Globals import package_home

import _patch

pkg_home = package_home( globals() )
lib_path = os.path.join( pkg_home, 'lib' )
if os.path.exists( lib_path ):
    sys.path.append( lib_path )
import catalog
import permissions
