from zope.interface import implements
from zope.component import getUtility
from plone.app.portlets.portlets import base
from plone.portlets.interfaces import IPortletDataProvider

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.PloneGetPaid.browser.portlets.base import GetPaidRenderer
from Products.PloneGetPaid.i18n import _
from Products.PloneGetPaid.interfaces import IRecurringPaymentMarker, ICurrencyFormatter


class IRecurringPaymentPortlet(IPortletDataProvider):
    pass


class Assignment(base.Assignment):
    implements(IRecurringPaymentPortlet)

    @property
    def title(self):
        """Title shown in @@manage-portlets.
        """
        return _(u"Recurring Payment")


class AddForm(base.NullAddForm):

    def create(self):
        return Assignment()


class Renderer(GetPaidRenderer):
    marker = IRecurringPaymentMarker
    render = ViewPageTemplateFile('../templates/portlet-content-recurringpayment.pt')
    
    def currency(self):
        context = self.context.aq_inner
        formatter = getUtility(ICurrencyFormatter)
        return formatter.currency(context)
