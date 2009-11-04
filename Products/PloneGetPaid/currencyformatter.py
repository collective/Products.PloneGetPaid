from decimal import *
from Products.PloneGetPaid import interfaces, vocabularies

class CurrencyFormatter(object):
    
    def format(self, context, value):
        """
        @param value: price as a float
        @return: Formatted price text
        """
        
        portal = context.portal_url.getPortalObject()
        

        # 1. read the setting
        options = interfaces.IGetPaidManagementOptions(portal)

        # 2. format the string
        currency = options.currency_symbol
        digits_after_decimal = options.digits_after_decimal
        
        if (value == None):
            value = 0.0

        getcontext().prec = digits_after_decimal
        return "%s %s" % (currency, str(Decimal(str(value))))