from Products.PloneGetPaid import interfaces, vocabularies

class CurrencyFormatter(object):
    
    def format(self, context, value):
        """
        @param value: price as a float
        @return: Formatted price text
        """
        
        portal = context.portal_url.getPortalObject()
        

        # 1. read the setting
        options = interfaces.IGetPaidManagementOptions(portal )

        # 2. format the string
        currency = options.currency_symbol
        return "%f %s" % (value, currency)