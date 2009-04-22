from zope.interface import implements
from getpaid.core.payment import CreditCardTypeEnumerator
from getpaid.core.interfaces import ICreditCardTypeEnumerator
from interfaces import IGetPaidManagementOptions
from Products.CMFCore.utils import getToolByName

class CreditCardTypeEnumerator(CreditCardTypeEnumerator):
    implements(ICreditCardTypeEnumerator)

    def __init__(self, context):
        self.context = context

    def acceptedCreditCardTypes(self):
        # Get the configured values
        portal = getToolByName(self.context.context, 'portal_url').getPortalObject()
        options = IGetPaidManagementOptions(portal)
        return options.accepted_credit_cards
