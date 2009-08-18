from zope import component
from zope.interface import implements
from plone.app.portlets.portlets import base
from plone.portlets.interfaces import IPortletDataProvider
from getpaid.core.interfaces import IPaymentProcessor

from Products.CMFCore.utils import getToolByName
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.PloneGetPaid.i18n import _
from Products.PloneGetPaid.interfaces import IGetPaidManagementOptions


class ICartPortlet(IPortletDataProvider):
    pass


class Assignment(base.Assignment):
    implements(ICartPortlet)

    @property
    def title(self):
        """Title shown in @@manage-portlets.
        """
        return _(u"Shopping Cart")


class AddForm(base.NullAddForm):

    def create(self):
        return Assignment()


class Renderer(base.Renderer):
    render = ViewPageTemplateFile('../templates/portlet-cart.pt')

    @property
    def available(self):
        """Portlet is always available.

        The template does some checking of its own via another browser
        view that is called.
        """
        return True

    def checkout_link(self):
        """Return the HTML for the link or button to the checkout wizard."""

        # Get the active Payment Processor.  The following code is
        # copied from PloneGetPaid.browser.checkout, and needs to be
        # refactored into a single function that is used everywhere for
        # uniformly discovering which payment processor is currently
        # active for a site.

        siteroot = getToolByName(self.context, "portal_url").getPortalObject()
        manage_options = IGetPaidManagementOptions(siteroot)
        processor_name = manage_options.payment_processor

        if not processor_name:
            raise RuntimeError( "No Payment Processor Specified" )

        processor = component.getAdapter( siteroot,
                                          IPaymentProcessor,
                                          processor_name )

        # Ask the Payment Processor what HTML it would like placed
        # wherever a "Checkout" button belongs.

        return processor.checkout_link()
