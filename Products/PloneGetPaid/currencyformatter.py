from Products.PloneGetPaid import interfaces, vocabularies

class CurrencyFormatter(object):
    
    def currency(self, context):
        """
        @return: Formatted price text
        """
        
        portal = context.portal_url.getPortalObject()
        

        # 1. read the setting
        options = interfaces.IGetPaidManagementOptions(portal)

        # 2. format the string
        currency = options.currency_symbol

        return currency