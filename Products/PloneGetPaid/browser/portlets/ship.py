from zope.interface import implements
from zope.component import getUtility
from plone.app.portlets.portlets import base
from plone.portlets.interfaces import IPortletDataProvider

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.PloneGetPaid.browser.portlets.base import GetPaidRenderer
from Products.PloneGetPaid.i18n import _
from Products.PloneGetPaid.interfaces import IShippableMarker, ICurrencyFormatter


class IShippablePortlet(IPortletDataProvider):
    pass


class Assignment(base.Assignment):
    implements(IShippablePortlet)

    @property
    def title(self):
        """Title shown in @@manage-portlets.
        """
        return _(u"Shippable")


class AddForm(base.NullAddForm):

    def create(self):
        return Assignment()


class Renderer(GetPaidRenderer):
    marker = IShippableMarker
    render = ViewPageTemplateFile('../templates/portlet-content-shippable.pt')
    
    def price(self):
        context = self.context.aq_inner
        formatter = getUtility(ICurrencyFormatter)
        price = getattr(self.payable, "price", 0.0)
        return formatter.format(context, price)
