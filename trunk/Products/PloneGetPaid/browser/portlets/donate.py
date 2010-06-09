from zope.interface import implements
from zope.component import getUtility
from plone.app.portlets.portlets import base
from plone.portlets.interfaces import IPortletDataProvider

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.PloneGetPaid.browser.portlets.base import GetPaidRenderer
from Products.PloneGetPaid.i18n import _
from Products.PloneGetPaid.interfaces import IDonatableMarker, ICurrencyFormatter
from Products.PloneGetPaid.browser.interfaces import IDontShowGetPaidPortlets

class IDonatablePortlet(IPortletDataProvider):
    pass


class Assignment(base.Assignment):
    implements(IDonatablePortlet)

    @property
    def title(self):
        """Title shown in @@manage-portlets.
        """
        return _(u"Donatable")


class AddForm(base.NullAddForm):

    def create(self):
        return Assignment()


class Renderer(GetPaidRenderer):
    marker = IDonatableMarker
    render = ViewPageTemplateFile('../templates/portlet-content-donatable.pt')

    @property
    def available(self):
        #don't show this portlet when a cart view is active
        #eg when viewing buyable-object/@@getpaid-cart-add
        return not IDontShowGetPaidPortlets.providedBy(self.view) and super(Renderer, self).available


    def currency(self):
        context = self.context.aq_inner
        formatter = getUtility(ICurrencyFormatter)
        return formatter.currency(context)
