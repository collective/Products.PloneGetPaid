"""Routines to find what GetPaid components are installed."""

from zope import component
from zope.app.component.hooks import getSite

from Products.PloneGetPaid.interfaces import IGetPaidManagementOptions

from getpaid.core.interfaces import IPaymentProcessor, IOffsitePaymentProcessor
from getpaid.core.processors import PaymentSituation

def selectedOnsitePaymentProcessor():
    """Return the currently selected on-site payment processor, or None."""
    site = getSite()
    manage_options = IGetPaidManagementOptions(site)
    if not manage_options.allow_onsite_payment:
        return
    name = manage_options.payment_processor
    if not name:
        return
    processor = component.queryAdapter(site, IPaymentProcessor, name)
    if processor is None:
        return
    processor.name = name  # until old-timey processors start providing this
    return processor

def selectedOffsitePaymentProcessors():
    """Return the list of the active offsite payment processors.

    As a shortcut, if the caller already has hold of the global GetPaid
    options, they can pass it to prevent its being re-discovered.

    """
    site = getSite()
    manage_options = IGetPaidManagementOptions(site)
    processors = []
    for name in sorted(manage_options.offsite_payment_processors):
        situation = PaymentSituation(None, None)
        processor = component.getAdapter(
            situation, IOffsitePaymentProcessor, name=name)
        processor.options = component.getAdapter(
            site, processor.options_interface)
        processor.store_url = site.absolute_url()
        processors.append(processor)
    return processors
