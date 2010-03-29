from zope.interface import implements
from zope.component import getUtility
from plone.app.portlets.portlets import base
from plone.portlets.interfaces import IPortletDataProvider

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.PloneGetPaid.browser.portlets.base import GetPaidRenderer
from Products.PloneGetPaid.i18n import _
from Products.PloneGetPaid.interfaces import IPremiumMarker, ICurrencyFormatter


class IPremiumPortlet(IPortletDataProvider):
    pass


class Assignment(base.Assignment):
    implements(IPremiumPortlet)

    @property
    def title(self):
        """Title shown in @@manage-portlets.
        """
        return _(u"Premium")


class AddForm(base.NullAddForm):

    def create(self):
        return Assignment()


class Renderer(GetPaidRenderer):
    marker = IPremiumMarker
    render = ViewPageTemplateFile('../templates/portlet-content-premium.pt')

    def currency(self):
        context = self.context.aq_inner
        formatter = getUtility(ICurrencyFormatter)
        return formatter.currency(context)
