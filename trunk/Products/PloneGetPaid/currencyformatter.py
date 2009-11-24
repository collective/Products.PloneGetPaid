from Products.PloneGetPaid import interfaces, vocabularies

class CurrencyFormatter(object):
    
    def currency(self, context):
        """
        @return: Formatted price text
        """
        
        portal = context.portal_url.getPortalObject()
        

        # 1. read the settings
        options = interfaces.IGetPaidManagementOptions(portal)

        # 2. format the string
        currency = options.currency_symbol

        return currency
    
    def order(self, context):
        """
        @return: Wether the currency symbol is before or after the amount.
        """
        
        portal = context.portal_url.getPortalObject()
        
        # Read the settings
        options = interfaces.IGetPaidManagementOptions(portal)
        
        # Return the setting as string
        return options.currency_formatting