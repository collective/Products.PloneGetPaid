from zope import component
from zope.app.component.hooks import getSite

from Products.Five.browser import BrowserView
from Products.PloneGetPaid import interfaces, discover

class CheckoutButtons(BrowserView):
    """View which renders one or more Checkout buttons.

    This view presents zero, one, or more checkout buttons, depending on
    how the store owner has configured the site.

    If the store owner has activated on-site payment processing, then a
    plain "Checkout" button is shown that leads to the first page of the
    GetPaid checkout wizard.

    If the store owner has activated an off-site payment processor that
    needs the user sent off-site right at the beginning of the checkout
    process, then that processor's button will appear.

    If the store owner activated both on-site and off-site processing,
    or if they activated multiple off-site processors, then multiple
    buttons will be shown, allowing the shopper to choose.

    If no processor is active, a message is displayed suggesting that
    the store owner might want to activate one.

    """
    def __call__(self):
        """Render our template, after computing some instance attributes.

        Before asking our template to render, we figure out whether the
        on-site checkout button should display, and also look up the
        views for the various off-site checkout buttons that we need to
        render.

        """
        self.show_onsite_button = False
        self.offsite_buttons = []

        siteroot = getSite()
        manage_options = interfaces.IGetPaidManagementOptions(siteroot)
        if manage_options.allow_onsite_payment:
            self.show_onsite_button = True

        # TODO: the payment "situation" should include pp options and
        # shopping cart, so that processors can vary their answers about
        # whether they offer a checkout button

        for opp in discover.selectedOffsitePaymentProcessors(manage_options):
            checkout_button = opp.checkout_button
            if checkout_button is not None:
                view = component.getMultiAdapter((opp, self.request),
                                                 name=checkout_button)
                view = view.__of__(self.context) # magic that makes it work
                self.offsite_buttons.append(view)
            elif opp.payment_form:
                self.show_onsite_button = True

        # Render our template.

        return self.index()
