"""
migrate store settings from annotations to persistent utility.

install new addressbook utility
"""

from Products.PloneGetPaid.Extensions.install import setup_settings, setup_addressbook
from Products.PloneGetPaid import preferences, interfaces

from zope import component, schema

def evolve( portal ):

    setup_settings( portal )
    setup_addressbook( portal )
    
    settings = component.getUtility( interfaces.IGetPaidManagementOptions )
    old_settings = preferences.OldConfigurationPreferences( portal )

    for field in schema.getFields( interfaces.IGetPaidManagementOptions ).values():
        field.set( settings, field.query( old_settings  ) )
        

    
    

    
