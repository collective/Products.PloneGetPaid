"""
$Id$
"""
from StringIO import StringIO

from Products.CMFCore.utils import getToolByName
from Products.PloneGetPaid import _GETPAID_DEPENDENCIES_
from Products.Five.site.localsite import enableLocalSiteHook
from Products.Archetypes.utils import shasattr

from zope.interface import alsoProvides, directlyProvides, directlyProvidedBy
from zope.event import notify
from zope.app.component.hooks import setSite
from zope.app.component.interfaces import ISite
from Products.PloneGetPaid import generations, preferences, addressbook
from Products.PloneGetPaid.interfaces import IGetPaidManagementOptions, IAddressBookUtility
from Products.PloneGetPaid.config import PLONE3
from Products.PloneGetPaid.cart import ShoppingCartUtility
from five.intid.site import add_intids
from getpaid.core.interfaces import IOrderManager, IStore, IShoppingCartUtility, StoreInstalled, StoreUninstalled
from getpaid.core.order import OrderManager
from getpaid.core.payment import CREDIT_CARD_TYPES

def setup_site( self ):
    portal = getToolByName( self, 'portal_url').getPortalObject()    
    
    if ISite.providedBy( portal ):
        setSite( portal )
        return
    enableLocalSiteHook( portal )
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

def setup_intid( self ):
    portal = getToolByName( self, 'portal_url').getPortalObject()
    add_intids( portal ) 

def install_dependencies( self ):
    quickinstaller = self.portal_quickinstaller
    for dependency in _GETPAID_DEPENDENCIES_:
        quickinstaller.installProduct( dependency )    

def install_cart_portlet( self, uninstall=False ):
    slot = 'here/@@portlet-shopping-cart/index/macros/portlet'
    portal = self.portal_url.getPortalObject()
    right_slots = portal.getProperty('right_slots', None)
    if right_slots is None:
        # Plone 3 does not use left/right_slots so bail out here.
        return
    if isinstance( right_slots, str):
        right_slots = right_slots.split('\n')
    else:
        right_slots = list( right_slots )
    if uninstall:
        if slot in right_slots:
            right_slots.remove( slot )
    else:
        if slot not in right_slots:
            right_slots.append( slot )
    portal._updateProperty( 'right_slots', '\n'.join( right_slots ) )    

def install_contentwidget_portlet( self, uninstall=False ):
    slot = 'here/@@portlet-contentwidget'
    portal = self.portal_url.getPortalObject()
    right_slots = portal.getProperty('right_slots', None)
    if right_slots is None:
        return
    if isinstance( right_slots, str):
        right_slots = right_slots.split('\n')
    else:
        right_slots = list( right_slots )
    if uninstall:
        if slot in right_slots:
            right_slots.remove( slot )
    else:
        if slot not in right_slots:
            right_slots.append( slot )
    portal._updateProperty( 'right_slots', '\n'.join( right_slots ) )    

def uninstall_cart_portlet( self ):
    install_cart_portlet( self, True )

def uninstall_contentwidget_portlet( self ):
    install_contentwidget_portlet (self, True )
    
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
    if not PLONE3:
        return

    # Do the imports here, as we only need them here and this only
    # gets run on Plone 3.0.
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

def register_shopping_cart_utility(self):
    """ Register a local utility to make carts persists
    """
    portal = getToolByName(self, 'portal_url').getPortalObject()
    sm = portal.getSiteManager()

    if not sm.queryUtility(IShoppingCartUtility):
        if PLONE3:
            sm.registerUtility(ShoppingCartUtility(), IShoppingCartUtility)
        else:
            sm.registerUtility(IShoppingCartUtility, ShoppingCartUtility())

def setup_settings( self ):
    portal = getToolByName( self, 'portal_url').getPortalObject()
    sm = portal.getSiteManager()

    if not sm.queryUtility( IGetPaidManagementOptions ):
        if PLONE3:
            sm.registerUtility( preferences.StoreSettings(), IGetPaidManagementOptions )
        else:
            sm.registerUtility( IGetPaidManagementOptions, preferences.StoreSettings() )

def setup_addressbook( self ):
    portal = getToolByName( self, 'portal_url').getPortalObject()
    sm = portal.getSiteManager()

    if not sm.queryUtility(IAddressBookUtility):
        if PLONE3:
            sm.registerUtility( addressbook.AddressBookUtility(), IAddressBookUtility)
        else:
            sm.registerUtility( IAddressBookUtility, addressbook.AddressBookUtility() )

def register_shopping_cart_utility(self):
    """ Register a local utility to make carts persists
    """
    portal = getToolByName(self, 'portal_url').getPortalObject()
    sm = portal.getSiteManager()

    if not sm.queryUtility(IShoppingCartUtility):
        if PLONE3:
            sm.registerUtility(ShoppingCartUtility(), IShoppingCartUtility)
        else:
            sm.registerUtility(IShoppingCartUtility, ShoppingCartUtility())

def install( self ):
    out = StringIO()

    print >> out, "Installing Dependencies"
    install_dependencies(self)

    # Run all import steps for getPaid
    setup_tool = getToolByName(self, 'portal_setup')
    if shasattr(setup_tool, 'runAllImportStepsFromProfile'):
        # Plone 3
        setup_tool.runAllImportStepsFromProfile('profile-Products.PloneGetPaid:default')
    else:
        # Plone 2.5.  Would work on 3.0 too, but then it gives tons of
        # DeprecationWarnings when running the tests, causing failures
        # to drown in the noise.
        old_context = setup_tool.getImportContextID()
        setup_tool.setImportContext('profile-Products.PloneGetPaid:default')
        setup_tool.runAllImportSteps()
        setup_tool.setImportContext(old_context)
    
    return out.getvalue()

def uninstall( self ):
    out = StringIO()

    print >> out, "Removing GetPaid"

    # This is not defined anywhere.
    #print >> out, "Uninstalling Control Panels Actions"
    #uninstall_control_panel( self )

    print >> out, "Uninstalling Cart Portlets"
    uninstall_cart_portlet( self )

    print >> out, "Uninstalling Content Portlets"    
    uninstall_contentwidget_portlet( self )

    teardown_store( self )

    return out.getvalue()
