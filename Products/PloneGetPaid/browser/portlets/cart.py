from zope import component
from zope.interface import implements
from plone.app.portlets.portlets import base
from plone.portlets.interfaces import IPortletDataProvider

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.PloneGetPaid.i18n import _

from getpaid.core import interfaces

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

    def doesCartContainItems( self, *args ):
        cart_manager = component.getUtility( interfaces.IShoppingCartUtility )
        cart = cart_manager.get( self.context, create=True )
        return bool(  len( cart ) )

    def shouldCheckoutButtonBeShown(self):
        """Return whether the checkout button stack should be shown."""

        # The checkout buttons that we want to display here in this
        # portlet (the onsite button together with any offsite buttons)
        # are the same ones that will already have been rendered in the
        # center of the page if we're sitting next to one of those
        # @@getpaid-cart views or any of its variants.

        # Since it is both an error and an offense against good taste to
        # display the same forms, with the same HTML IDs, twice on the
        # same page, this routine tries to prevent us from displaying
        # the checkout button if they are already probably somewhere on
        # the page.  The actual test below is really a bit of a guess:
        # it hopes that views placing the checkout button stack in the
        # middle of the page

        if not self.doesCartContainItems():
            return False

        url = self.request.getURL().split('?', 1)[0]
        if '@@getpaid-cart' in url:
            return False

        return True
