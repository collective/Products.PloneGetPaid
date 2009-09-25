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
