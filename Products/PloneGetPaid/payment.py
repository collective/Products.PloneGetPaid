from zope.component import adapter, queryAdapter
from zope.interface import implements
from getpaid.core.payment import CreditCardTypeEnumerator
from getpaid.core.interfaces import ICreditCardTypeEnumerator
from getpaid.core.interfaces import IStore
from getpaid.core.interfaces import IPaymentProcessor
from interfaces import IGetPaidManagementOptions
from Products.CMFCore.utils import getToolByName

class CreditCardTypeEnumerator(CreditCardTypeEnumerator):
    implements(ICreditCardTypeEnumerator)

    def __init__(self, context):
        self.context = context

    def acceptedCreditCardTypes(self):
        # Get the configured values
        context = getattr(self.context, 'context', self.context)
        portal = getToolByName(context, 'portal_url').getPortalObject()
        options = IGetPaidManagementOptions(portal)
        return options.accepted_credit_cards


@adapter(IStore)
def DefaultPaymentProcessorAdapterFactory(store):
    manage_options = IGetPaidManagementOptions(store)
    processor_name = manage_options.payment_processor
    if not processor_name:
        raise ValueError("No Payment Processor Specified")
    return processor_name, queryAdapter(store, IPaymentProcessor, processor_name)
