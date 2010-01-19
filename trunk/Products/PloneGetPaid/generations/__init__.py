"""
Simple Upgrading Framework

we put modules in generations/r500 corresponding to revision numbers and increment
the revision on db-version.txt .. each module has an evolve function which is called
in order to increment the app version to the latest software version which is nominally
post the upgrade module's revision.

$Id$

"""

import os, StringIO

def getAppSoftwareVersion( ):
    from Products.PloneGetPaid import pkg_home
    fh = open( os.path.join( pkg_home, 'db-version.txt'))
    db_version = fh.readline()
    fh.close()
    return int( db_version.split()[1] )

def getAppVersion( context ):
    return getattr( context.portal_url.getPortalObject(), '_getpaid_version', 0)

def setAppVersion( context, version ):
    context.portal_url.getPortalObject()._getpaid_version = int( version )

def getUpgrades( self ):
    version  = getAppVersion( self )
    software_version = getAppSoftwareVersion( )
    
    revisions = range( version+1, software_version+1 )
    base_generation_path = os.path.dirname( __file__ )

    upgrades = []
    for rev in revisions:
        rev_module = "r%s"%rev
        if os.path.exists( os.path.join( base_generation_path, "%s.py"%rev_module) ):
            module = __import__( "Products.PloneGetPaid.generations.%s"%rev_module, globals(), locals(), [rev_module] )
            upgrades.append( (rev, module.__doc__) )
    return upgrades
    
def upgrade( self ):

    out = StringIO.StringIO()
    
    version  = getAppVersion( self )
    software_version = getAppSoftwareVersion( )

    print >> out, "Upgrading From ", version, "to", software_version

    revisions = range( version+1, software_version+1 )

    base_generation_path = os.path.dirname( __file__ )

    portal = self.portal_url.getPortalObject()
    
    for rev in revisions:
        rev_module = "r%s"%rev
        if os.path.exists( os.path.join( base_generation_path, "%s.py"%rev_module) ):
            print >> out, "Upgrading Rev", rev
            module = __import__( "Products.PloneGetPaid.generations.%s"%rev_module, globals(), locals(), [rev_module] )
            print >> out, "  ", module.__doc__            
            module.evolve( portal )

    setAppVersion( portal, software_version )
    
    print >> out, "Finished Upgrade - System at ", software_version
    return out.getvalue()
            
            
        
        
        
