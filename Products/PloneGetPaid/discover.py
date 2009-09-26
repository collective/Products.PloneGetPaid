"""Routines to find what GetPaid components are installed."""

from zope import component
from zope.app.component.hooks import getSite

from Products.PloneGetPaid.interfaces import IGetPaidManagementOptions

from getpaid.core.interfaces import IOffsitePaymentProcessor
from getpaid.core.processors import PaymentSituation

def selectedOffsitePaymentProcessors(manage_options=None):
    """Return the list of the active offsite payment processors.

    As a shortcut, if the caller already has hold of the global GetPaid
    options, they can pass it to prevent its being re-discovered.

    """
    if manage_options is None:
        manage_options = IGetPaidManagementOptions(getSite())
    situation = PaymentSituation(None, None)
    return [
        component.getAdapter(situation, IOffsitePaymentProcessor, name=name)
        for name in sorted(manage_options.offsite_payment_processors)
        ]
