"""

Annotation Property Storage and Site Configuration Settings

$Id$
"""

from browser.checkout import BillingInfo
from getpaid.core import interfaces as core_interfaces
from getpaid.core.options import PersistentOptions, PersistentBag,FormSchemas
from member import ShipAddressInfo, BillAddressInfo, ContactInfo
from zope import component
import interfaces

def ConfigurationPreferences( site ):

    settings = component.queryUtility(interfaces.IGetPaidManagementOptions)

    if settings is None: # we have an unmigrated site.. fallback gracefully
        return OldConfigurationPreferences( site )
    
    # store access to the site, because our vocabularies get the setting as context
    # and want to access portal tools to construct various vocabs
    settings._v_site = site
    return settings

# previously we stored settings as annotations on the site, we've migrated this to
# its own utility, so we don't have to carry context to access the store settings.
# we have it here so we can do a migration. 
OldConfigurationPreferences = PersistentOptions.wire("OldConfigurationPreferences",
                                                     "getpaid.configuration",
                                                     interfaces.IGetPaidManagementOptions )

_StoreSettings = PersistentBag.makeclass( interfaces.IGetPaidManagementOptions )

class StoreSettings( _StoreSettings ):

    _v_site = None
    
    @property
    def context( self ):
        return self._v_site

    def manage_fixupOwnershipAfterAdd( self ): pass

class DefaultFormSchemas(FormSchemas):

    interfaces = {
        'billing_address':core_interfaces.IBillingAddress,
        'shipping_address':core_interfaces.IShippingAddress,
        'contact_information':core_interfaces.IUserContactInformation,
        'payment':core_interfaces.IUserPaymentInformation,
        }

    bags = {
        'billing_address':BillAddressInfo,
        'shipping_address':ShipAddressInfo,
        'contact_information':ContactInfo,
        'payment':BillingInfo,
        }

