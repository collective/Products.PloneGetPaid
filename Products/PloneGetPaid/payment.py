from zope.interface import implements
from getpaid.core.payment import CreditCardTypeEnumerator
from getpaid.core.interfaces import ICreditCardTypeEnumerator
from interfaces import IGetPaidManagementOptions, IGetPaidManagementPaymentOptions
from Products.CMFCore.utils import getToolByName

from getpaid.paymentprocessors.registry import paymentProcessorRegistry

class CreditCardTypeEnumerator(CreditCardTypeEnumerator):
    implements(ICreditCardTypeEnumerator)

    def __init__(self, context):
        self.context = context

    def acceptedCreditCardTypes(self):
        # Get the configured values
        portal = getToolByName(self.context.context, 'portal_url').getPortalObject()
        options = IGetPaidManagementOptions(portal)
        return options.accepted_credit_cards


def getActivePaymentProcessors(context):
    """ Return list of activated payment processors.
    
    @return: List of getpaid.paymentprocessor.registry.Entry objects
    """
    
    enabled = IGetPaidManagementPaymentOptions(context).enabled_processors
    
    processors = paymentProcessorRegistry.getProcessors()
    
    # Filter out processors which are activated in the settings
    
    return [ p for p in processors if p.name in enabled ]
    
