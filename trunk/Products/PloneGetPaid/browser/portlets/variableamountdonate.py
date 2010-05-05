from zope.interface import implements
from plone.app.portlets.portlets import base
from plone.portlets.interfaces import IPortletDataProvider

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.PloneGetPaid.browser.portlets.base import GetPaidRenderer
from Products.PloneGetPaid.i18n import _
from Products.PloneGetPaid.interfaces import IVariableAmountDonatableMarker

import donate

class IDonatablePortlet(IPortletDataProvider):
    pass


class Assignment(base.Assignment):
    implements(IDonatablePortlet)

    @property
    def title(self):
        """Title shown in @@manage-portlets.
        """
        return _(u"Variable Amount Donation")


class AddForm(base.NullAddForm):

    def create(self):
        return Assignment()


class Renderer(donate.Renderer):
    marker = IVariableAmountDonatableMarker
    render = ViewPageTemplateFile('../templates/portlet-content-variableamountdonatable.pt')
