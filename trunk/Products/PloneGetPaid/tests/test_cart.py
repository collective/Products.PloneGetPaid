"""Unit test for adding a payable type to a shopping cart.
"""

import unittest

from zope.component import getUtility
from Testing.ZopeTestCase import ZopeDocTestSuite
from Products.Five.utilities.marker import mark

from utils import optionflags
from base import PloneGetPaidTestCase

from Products.PloneGetPaid import interfaces
from getpaid.core.interfaces import IShoppingCartUtility

class TestCart(PloneGetPaidTestCase):

    def mySetup(self):
        self.setRoles(('Manager',))
        id = self.portal.invokeFactory('Document', 'doc')
        options = interfaces.IGetPaidManagementOptions(self.portal)
        options.buyable_types = ['Document']
        mark(self.portal.doc, interfaces.IBuyableMarker)
        self.cart_util = getUtility(IShoppingCartUtility)

    def test_doesNotCreateCartIfNotRequested(self):
        """Test that a cart is not instantiated if not requested

        >>> self.mySetup()
        >>> self.cart_util.get(self.portal, create=False)
        >>> 
        """
    def test_createsCartWhenRequsted(self):
        """

        >>> self.mySetup()
        >>> self.cart_util.get(self.portal, create=True)
        <getpaid.core.cart.ShoppingCart object at 0x...>

        """

    def test_getCartViaKeyForUser(self):
        """Test retrieval of a cart for a user via a key.

        First we need to create a cart for a user and get its
        corresponding key:

        >>> self.mySetup()
        >>> self.cart_util.get(self.portal, create=True)
        <getpaid.core.cart.ShoppingCart object at 0x...>
        >>> key = self.cart_util.getKey(self.portal)

        Since we want to test cart retrieval using the key we logout
        to make sure that we can retrieve the cart of a different user:

        >>> self.logout()
        >>> self.cart_util.get(self.portal, key=key)
        <getpaid.core.cart.ShoppingCart object at 0x...>
        """

    def test_getCartViaKeyForAnonymous(self):
        """Test retrieval of a cart for an anonymous user via a key.

        First we need to create a cart for an anonymous user and get
        its corresponding key:

        >>> self.mySetup()
        >>> self.logout()
        >>> self.cart_util.get(self.portal, create=True)
        <getpaid.core.cart.ShoppingCart object at 0x...>
        >>> key = self.cart_util.getKey(self.portal)

        Since we want to test cart retrieval via a key we need to swap
        to a clean session to make sure we can retrieve the cart from
        a different session:

        >>> self.pauseBrowserSession()
        >>> self.cart_util.get(self.portal, key=key)
        <getpaid.core.cart.ShoppingCart object at 0x...>
        """

    def test_destroyDestroysCart(self):
        """
        >>> self.mySetup()
        >>> self.cart_util.get(self.portal, create=True)
        <getpaid.core.cart.ShoppingCart object at 0x...>
        >>> self.cart_util.destroy(self.portal)
        >>> self.cart_util.get(self.portal, create=False)
        >>>
        """
    def test_destroyCopesWithNotHavingAnythingToDo(self):
        """
        >>> self.mySetup()
        >>> self.cart_util.destroy(self.portal)
        >>> self.cart_util.get(self.portal, create=False)
        >>>
        """

    def test_destroyDestroysCartViaKeyForUser(self):
        """Test cart destruction of a user for a given key.

        Create a cart and get its corresponding key:

        >>> self.mySetup()
        >>> self.cart_util.get(self.portal, create=True)
        <getpaid.core.cart.ShoppingCart object at 0x...>
        >>> key = self.cart_util.getKey(self.portal)

        Since we want to test cart destruction using the key we logout
        to make sure that we can destroy the cart of a different user:

        >>> self.logout()
        >>> self.cart_util.destroy(self.portal, key)

        Now login and observe that the cart for that user has been
        destroyed:

        >>> self.login()
        >>> print self.cart_util.get(self.portal, create=False)
        None
        """

    def test_destroyDestroysCartViaKeyForAnonymous(self):
        """Test cart destruction of an anonymous user for a given key.

        >>> self.mySetup()
        >>> self.logout()

        Create a cart for an anonymous user:

        >>> self.cart_util.get(self.portal, create=True)
        <getpaid.core.cart.ShoppingCart object at 0x...>
        >>> key = self.cart_util.getKey(self.portal)

        Since we want to test cart destruction using the key we need
        to swap to a clean session to make sure we can destroy the
        cart from a different session:

        >>> self.pauseBrowserSession()
        >>> self.cart_util.destroy(self.portal, key)

        Now rejoin the original session that created the cart and
        observed the cart it been destroyed:

        >>> self.resumeBrowserSession()
        >>> print self.cart_util.get(self.portal, create=False)
        None
        """

    def test_exceptionRaisedForMailformedKey(self):
        """Test exception thrown for various malformed keys.

        >>> self.mySetup()
        >>> self.cart_util._decodeKey('example-malformed-key')
        Traceback (most recent call last):
          ...
        ValueError: Malformed key: example-malformed-key

        >>> self.cart_util._decodeKey('example:malformed:key')
        Traceback (most recent call last):
          ...
        ValueError: Malformed key: example:malformed:key
        """

    def pauseBrowserSession(self):
        """Utility that disables the current session. The session can
        be resumed using resumeBrowserSession.
        """
        self._paused_browser_id = self.portal.REQUEST.browser_id_
        self.portal.REQUEST.browser_id_ = None

    def resumeBrowserSession(self):
        """Utility to restore the previous session.
        """
        self.portal.REQUEST.browser_id_ = self._paused_browser_id


def test_suite():
    return unittest.TestSuite((
            ZopeDocTestSuite(test_class=TestCart,
                             optionflags=optionflags),
        ))
