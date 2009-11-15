"""

    Unit tests for taxes and prices.

"""

__author__ = "Mikko Ohtamaa <mikko.ohtamaa@twinapex.com> http://www.twinapex.com"
__docformat__ = "epytext"
__copyright__ = "2009 Twinapex Research"


import unittest

from zope.app.component.hooks import getSite
from zope.component import getUtility, getMultiAdapter
from Testing.ZopeTestCase import ZopeDocTestSuite
from Products.Five.utilities.marker import mark

from utils import optionflags
from base import PloneGetPaidTestCase, TestHelperMixin

from Products.PloneGetPaid import interfaces
import getpaid.core.interfaces
from getpaid.core.interfaces import IShoppingCartUtility
from getpaid.core.interfaces import IPriceValueAdjuster

from Products.PloneGetPaid.interfaces import IGetPaidManagementSalesTaxOptions, IGetPaidManagementOptions

class TestTaxAndPrices(TestHelperMixin, PloneGetPaidTestCase):

    def afterSetUp(self):
        PloneGetPaidTestCase.afterSetUp(self)
        self.settings = IGetPaidManagementOptions(self.portal)
        self.utility = IPriceValueAdjuster(self.portal)

    def assertAlmostEqual(self, x, y):
        """
        Floating point aware number comparison
        """
        PloneGetPaidTestCase.assertAlmostEqual(self, x, y, places=4)

    def set_tax(self):
        self.assertEqual(self.settings.tax_percent, 0) # See that tax variable is available
        self.settings.tax_percent = 6.6600 # Use funny multiplier to detect rounding errors


    def test_set_tax_option(self):
        """
        Check that we can manipulate VAT options correctly.
        """
        self.set_tax()

        # See that we got tax
        settings = IGetPaidManagementOptions(self.portal)
        self.assertAlmostEqual(settings.tax_percent, 6.66)

    def test_get_tax_free_price(self):
        """ Check that tax free prices are calculated correctly """
        self.set_tax()
        self.settings.tax_in_set_prices = True

        price = self.utility.getTaxFreePrice(10.00, None)
        self.assertAlmostEqual(price, 9.38)

        self.settings.tax_in_set_prices = False
        price = self.utility.getTaxFreePrice(10.00, None)
        self.assertAlmostEqual(price, 10.00)

    def test_get_shop_price(self):
        """ Check that user visible prices are calculated correctly """
        self.set_tax()
        self.settings.tax_in_set_prices = False

        self.settings.tax_visible_in_prices = True
        price = self.utility.getShopPrice(10.00, None)
        self.assertAlmostEqual(price, 10.6700)

        self.settings.tax_visible_in_prices = False
        price = self.utility.getShopPrice(10.00, None)
        self.assertAlmostEqual(price, 10.00)

    def test_calculate_taxed_price(self):
        """ Check that tax amounts (for invoices) are calculated correctly """
        self.set_tax()
        self.settings.tax_in_set_prices = False

        taxed_price = self.utility.getTaxedPrice(10.00, None)
        self.assertAlmostEqual(taxed_price, 10.67)

        self.settings.tax_in_set_prices = True
        taxed_price = self.utility.getTaxedPrice(10.00, None)
        self.assertAlmostEqual(taxed_price, 10.00)

    def test_taxes_in_cart(self):
        """ Test that getpaid.core.cart container total calculator uses taxes correctly.
        """
        self.set_tax()
        self.loginAsPortalOwner()
        self.setupBuyingSituation()

        # Add item to the cart
        self.createSomethingBuyable()
        self.addCartItem(self.portal.buyitem)

        site = getSite()
        price_adjuster = IPriceValueAdjuster(site)

        totals = getMultiAdapter((self.cart, price_adjuster), getpaid.core.interfaces.ILineContainerTotals)

        shipping_price = totals.getShippingCost()
        self.assertAlmostEqual(shipping_price, 0)

        subtotal_price = totals.getSubTotalPrice()
        self.assertAlmostEqual(subtotal_price, 10.00)

        tax_cost = totals.getSalesTaxCost()
        self.assertAlmostEqual(tax_cost, 0.67)


        total_price = totals.getTotalPrice()
        self.assertAlmostEqual(total_price, 10.67)



def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestTaxAndPrices))
    return suite

