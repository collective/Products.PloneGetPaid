"""
    Tax management.

"""

__author__ = "Mikko Ohtamaa <mikko.ohtamaa@twinapex.com> http://www.twinapex.com"
__docformat__ = "epytext"
__copyright__ = "2009 Twinapex Research"

from getpaid.core.interfaces import IPriceValueAdjuster

from Products.PloneGetPaid.interfaces import IGetPaidManagementSalesTaxOptions, IGetPaidManagementOptions

class PriceValueAdjuster(object):
    """ Deal with tax and tax-free presentations of prices on the site.

    How to use this utility::


        from zope.component import getUtility
        from getpaid.core.interfaces import IPriceValueAdjuster

        # You need to have a handle to site root

        price_value_adjuster = getUtility(IPriceValueAdjuster, context=site)

    """

    def __init__(self, context):
        self.site = context

        self.prepare()

    def prepare(self):
        """ Do necessary utility look-ups for other methods to perform.
        """
        self.settings = IGetPaidManagementOptions(self.site)


    def roundTax(self, value):
        """ Round value of price to user visible decimals.

        By default, two decimals are used.

        @return: Rounded value
        """
        pass

    def calculateTaxAmount(self, value):
        """
        """
        tax = self.getAppliedTax()
        value = value * tax
        return self.roundTax(value)

    def calculateIncludedTaxAmount(self, value):
        """

        """

        tax = self.getAppliedTax()

        tax_free = value / tax
        return self.calculateTaxAmount(tax_free, tax)

    def getAppliedTax(self):
        return self.settings.tax_percent / 100.0

    def hasTaxInPrice(self):
        """
        """
        return self.settings.tax_in_set_prices

    def getTax(self, raw_price, item):
        """ Calculate how much there is tax for a priced item

        We ignore item as we assume all items
        use the same generic sales tax on the site.
        You could override this to use different
        """
        tax_free = self.getTaxFreePrice(raw_price)
        return self.calculateTaxAmount(tax_free)


    def getTaxFreePrice(raw_price):

        if self.hasTaxInPrice():
            tax = self.calculateIncludedTaxAmount(raw_price)
            return raw_price - tax
        else:
            return raw_price

    def getShopPrice(self, raw_price):
        tax_free = self.getTaxFreePrice(raw_price)
        if self.showTaxInPrice():
            return self.getTaxPrice(tax_free)
        else:
            return tax_free


def manufacture_price_adjuster(context):
    return PriceValueAdjuster(context)