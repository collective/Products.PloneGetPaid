"""Base class for integration tests, based on ZopeTestCase and PloneTestCase.

Note that importing this module has various side-effects: it registers a set of
products with Zope, and it sets up a sandbox Plone site with the appropriate
products installed.
"""

from Testing import ZopeTestCase

# Let Zope know about the products we require above-and-beyond a basic
# Plone install (PloneTestCase takes care of these).
from Products.PloneGetPaid.config import PLONE3
if not PLONE3:
    ZopeTestCase.installProduct('CMFonFive')
ZopeTestCase.installProduct('PloneGetPaid')



# Import PloneTestCase - this registers more products with Zope as a side effect
from Products.PloneTestCase.PloneTestCase import PloneTestCase
from Products.PloneTestCase.PloneTestCase import FunctionalTestCase
from Products.PloneTestCase.PloneTestCase import setupPloneSite

# Set up a Plone site.

setupPloneSite()


def baseAfterSetUp( self ):
    """Code that is needed is the afterSetUp of both test cases.
    """

    # This looks like a safe place to install Five.
    ZopeTestCase.installProduct('Five')

    # XXX monkey patch everytime (until we figure out the problem where
    #   monkeypatch gets overwritten somewhere)
    try:
        from Products.Five import pythonproducts
        pythonproducts.setupPythonProducts(None)
    except ImportError:
        # Not needed in Plone 3
        pass

    # Set up sessioning objects
    ZopeTestCase.utils.setupCoreSessions(self.app)


class PloneGetPaidTestCase(PloneTestCase):
    """Base class for integration tests for the 'PloneGetPaid' product. This may
    provide specific set-up and tear-down operations, or provide convenience
    methods.
    """
    def afterSetUp( self ):
        baseAfterSetUp(self)
        # I moved here so that doctests work ok without needing to add PloneGetPaid
        #   and so we don't need to add this line to all our unit tests
        self.portal.portal_quickinstaller.installProduct('PloneGetPaid')


class PloneGetPaidFunctionalTestCase(FunctionalTestCase):
    """Base class for functional integration tests for the 'PloneGetPaid' product.
    This may provide specific set-up and tear-down operations, or provide
    convenience methods.
    """

    def afterSetUp( self ):
        baseAfterSetUp(self)

    class Session(dict):
        def set(self, key, value):
            self[key] = value

    def _setup(self):
        FunctionalTestCase._setup(self)
        self.app.REQUEST['SESSION'] = self.Session()

class ErrorAwarePloneGetPaidFunctionalTestCase(PloneGetPaidFunctionalTestCase):
    """
    Functional test case base class with advanced error tracing features.

    1. Login as admin by default

    2. Print error tracebacks to console when occur

    https://svn.plone.org/svn/collective/collective.developermanual/trunk/source/testing_and_debugging/functional_testing.txt
    """

    def loginBrowserAsAdmin(self):
        from Products.Five.testbrowser import Browser

        self.browser = Browser()

        self.browser.open(self.portal.absolute_url())

        from Products.PloneTestCase.setup import portal_owner, default_password

         # Go admin
        browser.open(self.portal.absolute_url() + "/login_form")
        browser.getControl(name='__ac_name').value = portal_owner
        browser.getControl(name='__ac_password').value = default_password
        browser.getControl(name='submit').click()


    def afterSetUp(self):

        PloneGetPaidFunctionalTestCase.afterSetUp(self)

        self.browser.handleErrors = False
        self.portal.error_log._ignored_exceptions = ()

        def raising(self, info):
            import traceback
            traceback.print_tb(info[2])
            print info[1]

        from Products.SiteErrorLog.SiteErrorLog import SiteErrorLog
        SiteErrorLog.raising = raising

        self.loginBrowserAsAdmin()


class TestHelperMixin(object):
    """ Helper functions for unit and functional tests.

    To include these to your unit test, subclass this::

        class YourTestCase(TestHelperMixin, PloneGetPaidTestCase):
            pass

    """

    def makeBuyable(self, context, price, product_code):
        """ Performs make buyable action on a content item."""


        import getpaid.core.interfaces as igetpaid
        from AccessControl import getSecurityManager
        from getpaid.core import options, event, order
        from Products.PloneGetPaid import interfaces
        from Products.Five.utilities import marker
        from zope.component import queryAdapter

        # Turn on marker interface
        from Products.Five.utilities import marker
        marker.mark(context, interfaces.IBuyableMarker)

        # Add in buy data
        adapter = queryAdapter(context, igetpaid.IBuyableContent)
        assert adapter != None

        adapter.made_payable_by = getSecurityManager().getUser().getId()
        adapter.price = price
        adapter.product_code = product_code

        return adapter

    def createSomethingBuyable(self):
        """ Create a Document content which is buyable with price 10.00 """
        from Products.PloneGetPaid import interfaces
        import getpaid.core.interfaces

        options = interfaces.IGetPaidManagementOptions(self.portal)
        options.buyable_types = ['Document']

        self.portal.invokeFactory("Document", "buyitem")
        self.makeBuyable(self.portal.buyitem, 10.00, "0001")

    def setupBuyingSituation(self):
        """ Create unit test specific cart.

        The cart is not peristent. The cart can be used to create orders.
        """
        import getpaid.core.interfaces
        from zope import component
        self.cart = component.getUtility(getpaid.core.interfaces.IShoppingCartUtility).get(self.portal, create=True)

    def addCartItem(self, context):
        """ Add one item to cart.

        @param context: OBject implementing IBuyable
        """
        from zope import component
        import getpaid.core.interfaces
        assert self.cart != None

        # Order lines are cart specific - cart reference is always there
        item_factory = component.getMultiAdapter((self.cart, context), getpaid.core.interfaces.ILineItemFactory)
        item = item_factory.create()


    def createOrder(self):
        """ Create an order based on the current cart."""
        import pickle
        from zope import component
        from getpaid.core import interfaces
        from getpaid.core.order import Order
        from AccessControl import getSecurityManager

        order_manager = component.getUtility( interfaces.IOrderManager )

        order = Order()

        # loads() / dumps() magic makes sure that cart is pickable
        # and it cleans up objects referred in external database
        order.shopping_cart = pickle.loads(pickle.dumps(self.cart))

        order.order_id = u"order0001"
        order.user_id = getSecurityManager().getUser().getId()

        return order

    def setupInvoice(self):
        from getpaid.invoice.interfaces import IInvoiceSettings
        settings = IInvoiceSettings(self.portal)
        settings.terms_of_payment = "14 days"
        settings.penalty_interest = "14.0%"
        settings.running_counter = 1000
