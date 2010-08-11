"""
Currency Formatter Utility
"""

__version__ = "$Revision$"
# $Id$
# $URL$

from zope import component, globalrequest

from Products.PloneGetPaid.interfaces import IGetPaidManagementCurrencyOptions

from zope.i18n import translate

class CurrencyFormatter(object):

    def format(self, value):
        site = component.getSiteManager()
        request = globalrequest.getRequest()

        portal_state = component.getMultiAdapter((site, request), name=u"plone_portal_state")
        language = portal_state.language()

        decimal_symbol = translate("decimal_symbol", domain="Products.PloneGetPaid", default=",",
                         target_language = language)

        return translate("formatted_price", domain="Products.PloneGetPaid", default="${value} ${currency}",
                         mapping = {"value": ("%0.2f" % value).replace(".", decimal_symbol),
                                    "currency": self.currency_symbol },
                         target_language = language)
    @property
    def precision(self):
        ### FIXME: Why this field on IGetPaidManagementCurrencyOptions is TextLine?
        options = component.queryUtility(IGetPaidManagementCurrencyOptions)
        return int(options.digits_after_decimal)

    @property
    def currency_symbol(self):
        options = component.queryUtility(IGetPaidManagementCurrencyOptions)
        return options.currency_symbol

    # legacy method
    def currency(self, context):
        """ returns currency symbol """
        return self.currency_symbol
