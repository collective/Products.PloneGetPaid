from zope import component
from zope.app.component.hooks import getSite

#from getpaid.core.interfaces import ICheckoutWizard

from Products.Five.browser import BrowserView
from Products.PloneGetPaid.interfaces import IGetPaidManagementOptions

class CheckoutButton(BrowserView):
    """View which renders a Checkout button for the current wizard.

    The different on-site and off-site checkout wizards supported by
    GetPaid need quite different sorts of "Checkout" buttons to be
    rendered at the bottom of shopping cart views and portals.  The
    default on-site wizard, for example, can be visited through a simple
    link, since the on-site wizard can then access the current user's
    shopping cart directly.  Most off-site processors, by contrast, can
    only be activated through a sophisticated form POST that sends
    enough hidden fields to tell the remote site how to call back and
    find out what is in the user's shopping cart, or, at the very least,
    what its total is.

    The purpose of this `CheckoutButton`, then, is simple: to look up
    the currently active checkout wizard; to ask it for the view that
    defines its checkout button; and then to render that view whenever
    we ourselves are asked to be rendered.

    """
    def __call__(self):
        siteroot = getSite()
        manage_options = IGetPaidManagementOptions(siteroot)
        wizard_name = manage_options.checkout_wizard

        if not wizard_name:
            raise RuntimeError( "No Checkout Wizard Specified" )

        wizard = component.getAdapter(siteroot, ICheckoutWizard, wizard_name)

        view_name = wizard.checkout_button_view_name
        view = self.context.restrictedTraverse(
            '@@' + view_name).__of__(self.context)
        return view()
