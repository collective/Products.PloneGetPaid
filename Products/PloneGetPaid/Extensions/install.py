"""
$Id$
"""
from StringIO import StringIO

from Products.CMFCore.utils import getToolByName

from zope.interface import alsoProvides, directlyProvides, directlyProvidedBy
from zope.event import notify
from zope.app.component.hooks import setSite
from Products.PloneGetPaid import generations, preferences, addressbook, namedorder
from Products.PloneGetPaid.interfaces import IGetPaidManagementOptions, IAddressBookUtility, INamedOrderUtility
from Products.PloneGetPaid.cart import ShoppingCartUtility
import zope.component
import five.intid.site
from getpaid.core.interfaces import IOrderManager, IStore, IShoppingCartUtility, StoreInstalled, StoreUninstalled
from getpaid.core.order import OrderManager
from getpaid.core.payment import CREDIT_CARD_TYPES

def setup_site( self ):
    portal = getToolByName( self, 'portal_url').getPortalObject()
    setSite( portal )

def setup_software_generation( self ):
    # mark the current version of the software in the database on install
    generations.setAppVersion( self, generations.getAppSoftwareVersion() )

def setup_store( self ):
    portal = getToolByName( self, 'portal_url').getPortalObject()
    alsoProvides(portal, IStore)
    
def notify_install( self ):
    notify( StoreInstalled( self ) )

def notify_uninstalled( self ):
    notify( StoreUninstalled( self ) )

def teardown_store( self ):
    portal = getToolByName( self, 'portal_url').getPortalObject()
    directlyProvides(portal, directlyProvidedBy(portal) - IStore)

def setup_order_manager( self ):
    portal = getToolByName( self, 'portal_url').getPortalObject()
    sm = portal.getSiteManager()
    is_already_registered = [u for u in sm.getUtilitiesFor(IOrderManager)]
    if not len(is_already_registered):
        manager = OrderManager()
        try:
            sm.registerUtility(component=manager, provided=IOrderManager)
        except TypeError:
            # BBB for Zope 2.9
            sm.registerUtility(interface=IOrderManager, utility=manager)

def install_plone3_portlets(self):
    """Add all portlets to the right column in the portal root.

    Other variations are possible:

    - At least do this for the cart portlet as that one always makes
      sense.

    - Assign the one correct portlet for an object at the moment that
      we make it buyable, donatable, etc.

    - When setting a content type as payable in the control panel,
      assign the correct portlet to that content type.
    """

    # Do the imports here, as we only need them here
    from zope.app.container.interfaces import INameChooser
    from zope.component import getUtility, getMultiAdapter
    from plone.portlets.interfaces import IPortletManager, IPortletAssignmentMapping
    from Products.PloneGetPaid.browser import portlets

    # Get some definitions.
    portal = self.portal_url.getPortalObject()
    column = getUtility(IPortletManager, name="plone.rightcolumn", context=portal)
    manager = getMultiAdapter((portal, column), IPortletAssignmentMapping)
    portletnames = [v.title for v in manager.values()]
    chooser = INameChooser(manager)

    assignments = [
        portlets.cart.Assignment(),
        portlets.buy.Assignment(),
        portlets.donate.Assignment(),
        portlets.variableamountdonate.Assignment(),
        portlets.ship.Assignment(),
        portlets.premium.Assignment(),
        ]

    for assignment in assignments:
        title = assignment.title
        if title not in portletnames:
            manager[chooser.chooseName(title, assignment)] = assignment

def setup_payment_options(self):
    """ Set the default payment options for credit card types.
    """
    manage_options = IGetPaidManagementOptions(self)
    manage_options.setProperty('credit_cards', CREDIT_CARD_TYPES)

def setup_settings( self ):
    portal = getToolByName( self, 'portal_url').getPortalObject()
    sm = portal.getSiteManager()

    if not sm.queryUtility( IGetPaidManagementOptions ):
        sm.registerUtility( preferences.StoreSettings(), IGetPaidManagementOptions )

def setup_addressbook( self ):
    portal = getToolByName( self, 'portal_url').getPortalObject()
    sm = portal.getSiteManager()

    if not sm.queryUtility(IAddressBookUtility):
        sm.registerUtility( addressbook.AddressBookUtility(), IAddressBookUtility)

def setup_named_orders(self):
    portal = getToolByName( self, 'portal_url').getPortalObject()
    sm = portal.getSiteManager()

    if not sm.queryUtility(INamedOrderUtility):
        sm.registerUtility( namedorder.NamedOrderUtility(), INamedOrderUtility)

def register_shopping_cart_utility(self):
    """ Register a local utility to make carts persists
    """
    portal = getToolByName(self, 'portal_url').getPortalObject()
    sm = portal.getSiteManager()

    if not sm.queryUtility(IShoppingCartUtility):
        sm.registerUtility(ShoppingCartUtility(), IShoppingCartUtility)

def install( self ):
    out = StringIO()

    # Run all import steps for getPaid
    setup_tool = getToolByName(self, 'portal_setup')
    setup_tool.runAllImportStepsFromProfile('profile-Products.PloneGetPaid:default',
            purge_old=False)
    
    return out.getvalue()

def beforeUninstall(self, reinstall=False, product=None, cascade=[]):
    try:
        cascade.remove('utilities')
    except ValueError:
        pass
    return True, cascade

def uninstall( self ):
    out = StringIO()

    print >> out, "Removing GetPaid"

    teardown_store( self )

    return out.getvalue()
