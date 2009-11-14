"""

    Unit tests for taxes and prices.

"""

__author__ = "Mikko Ohtamaa <mikko.ohtamaa@twinapex.com> http://www.twinapex.com"
__docformat__ = "epytext"
__license__ = "GPL"
__copyright__ = "2009 Twinapex Research"


import unittest

from zope.component import getUtility
from Testing.ZopeTestCase import ZopeDocTestSuite
from Products.Five.utilities.marker import mark

from utils import optionflags
from base import PloneGetPaidTestCase

from Products.PloneGetPaid import interfaces
from getpaid.core.interfaces import IShoppingCartUtility
from getpaid.core.interfaces import IPriceValueAdjuster

from Products.PloneGetPaid.interfaces import IGetPaidManagementSalesTaxOptions, IGetPaidManagementOptions

class TestTaxAndPrices(PloneGetPaidTestCase):

    def afterSetUp(self):
        PloneGetPaidTestCase.afterSetUp(self)
        self.settings = IGetPaidManagementOptions(self.portal)

        self.utility = IPriceValueAdjuster(self.portal)


    def set_tax(self):
        settings = IGetPaidManagementOptions(self.portal)
        settings.tax = 6.6666 # Use funny multiplier to detect rounding errors

    def test_set_tax_option(self):
        """
        Check that we can manipulate VAT options correctly.
        """
        self.set_tax()

    def test_get_tax_free_price(self):
        """ Check that tax free prices are calculated correctly """
        self.set_tax()
        self.settings.tax_in_set_prices = True

        price = self.utility.getTaxFreePrice(10.00, None)
        self.assertEqual(price, 8.50)

        self.settings.tax_in_set_prices = False
        price = self.utility.getTaxFreePrice(10.00, None)
        self.assertEqual(price, 10.00)

    def test_get_shop_price(self):
        """ Check that user visible prices are calculated correctly """
        self.set_tax()
        self.settings.tax_in_set_prices = False


        self.settings.tax_included_in_prices = True
        price = self.utility.getTaxedPrice(10.00, None)
        self.assertEqual(price, 10.6600)

        self.settings.tax_included_in_prices = False
        price = self.utility.getTaxedPrice(10.00, None)
        self.assertEqual(price, 10.00)

    def test_calculate_tax(self):
        """ Check that tax amounts (for invoices) are calculated correctly """
        self.set_tax()
        self.settings.tax_in_set_prices = False

        tax = self.utility.getTaxedPrice(10.00, None)
        self.assertEqual(tax, 0.66)

        self.settings.tax_in_set_prices = True
        tax = self.utility.getTaxedPrice(10.00, None)
        self.assertEqual(tax, 0.66)


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestTaxAndPrices))
    return suite

