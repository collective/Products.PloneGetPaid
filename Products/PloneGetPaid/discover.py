"""Routines to find what GetPaid components are installed."""

from zope import component
from zope.app.component.hooks import getSite

from Products.PloneGetPaid.interfaces import IGetPaidManagementOptions

from getpaid.core.interfaces import (
    IPaymentProcessor, IOffsitePaymentProcessor, IShoppingCartUtility,
    )
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
    """Return the list of the active offsite payment processors."""

    site = getSite()
    manage_options = IGetPaidManagementOptions(site)
    processors = []
    for name in sorted(manage_options.offsite_payment_processors):
        cart_util = component.getUtility(IShoppingCartUtility)
        cart = cart_util.get(site, create=True)

        situation = PaymentSituation(None, None)
        processor = component.queryAdapter(
            situation, IOffsitePaymentProcessor, name=name)

        # If the processor was not found, ignore silently; this just
        # means that the site owner has un-installed a payment processor
        # module while its name is still hanging around in our settings.
        # The value will get removed the next time the store owner
        # submits the "Payment Options" page.

        if processor is None:
            continue

        # Not finding the options for a processor that is indeed
        # installed, however, ranks as an error, so we let getAdapter()
        # raise its exception in that case.

        processor.cart = cart
        processor.options = component.getAdapter(
            site, processor.options_interface)
        processor.store_url = site.absolute_url()
        processors.append(processor)

    return processors
