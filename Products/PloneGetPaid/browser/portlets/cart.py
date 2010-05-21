from zope.interface import implements
from plone.app.portlets.portlets import base
from plone.portlets.interfaces import IPortletDataProvider

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.PloneGetPaid.browser.portlets.base import GetPaidRenderer
from Products.PloneGetPaid.i18n import _
from Products.PloneGetPaid.browser.interfaces import ICartView

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
        The only situation we do not need it is when we display the shopping
        cart.

        The template does some checking of its own via another browser
        view that is called.
        """
        return not ICartView.providedBy(self.view)

