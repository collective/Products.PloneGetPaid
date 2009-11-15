"""
    Tax management.

"""

__author__ = "Mikko Ohtamaa <mikko.ohtamaa@twinapex.com> http://www.twinapex.com"
__docformat__ = "epytext"
__copyright__ = "2009 Twinapex Research"

import zope.interface

from getpaid.core.interfaces import IPriceValueAdjuster

from Products.PloneGetPaid.interfaces import IGetPaidManagementSalesTaxOptions, IGetPaidManagementOptions

class PriceValueAdjuster(object):
    """ Deal with tax and tax-free presentations of prices on the site.

    How to use this utility::


        from getpaid.core.interfaces import IPriceValueAdjuster

        # You need to have a handle to site root

        price_value_adjuster = IPriceValueAdjuster(site)


    How to get the price which you need to display to the user::

        from zope.component import getUtility, queryAdapter
        from getpaid.core.interfaces import IPriceValueAdjuster, IBuyableContent

        price_value_adjuster = IPriceValueAdjuster(site)

        # Assume context is a PloneGetPaid object
        adapter = queryAdapter(context, IBuyableContent)
        # adapter == None if the context does not support IBuyableContent
        raw_price = adapter.price
        tax_adjusted_price = price_value_adjuster.getShopPrice(raw_price, contxet)

        return tax_adjusted_price

    How to get line container totals for a cart::



    This default implementation ignores item hint: it
    assumes all items have the same sales tax.

    """
    zope.interface.implements(IPriceValueAdjuster)

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
        return round(value, 2)


    def calculateTaxAmount(self, value, item):
        """
        """
        tax = self.getAppliedTax(item)
        tax_amount = value * tax
        return self.roundTax(tax_amount)

    def calculateIncludedTaxAmount(self, value, item):
        """

        """
        tax = self.getAppliedTax(item)
        tax_free = value / (1+tax)
        return self.calculateTaxAmount(tax_free, item)

    def getAppliedTax(self, item):
        """
        Assume all items have the same tax base.

        Alternative would have content/line item specific
        adapters which would return the item tax base here.
        """
        return self.settings.tax_percent / 100.0

    def hasTaxInPrice(self):
        """
        """
        return self.settings.tax_in_set_prices

    def isTaxVisibleInPrice(self):
        """
        """
        return self.settings.tax_visible_in_prices

    def getTax(self, raw_price, item):
        """ Calculate how much there is tax for a priced item

        We ignore item as we assume all items
        use the same generic sales tax on the site.
        You could override this to use different
        """
        tax_free = self.getTaxFreePrice(raw_price, item)
        return self.calculateTaxAmount(tax_free, item)

    def getTaxedPrice(self, raw_price, item):
        if self.hasTaxInPrice():
            return raw_price
        else:
            tax = self.calculateTaxAmount(raw_price, item)
            return raw_price + tax

    def getTaxFreePrice(self, raw_price, item):

        if self.hasTaxInPrice():
            tax = self.calculateIncludedTaxAmount(raw_price, item)
            return raw_price - tax
        else:
            return raw_price

    def getShopPrice(self, raw_price, item):
        if self.isTaxVisibleInPrice():
            return self.getTaxedPrice(raw_price, item)
        else:
            return self.getTaxFreePrice(raw_price, item)



def manufacture_price_adjuster(context):
    return PriceValueAdjuster(context)