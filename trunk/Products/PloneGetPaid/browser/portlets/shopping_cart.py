import math

from zope import component, interface, formlib, schema

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.CMFCore.utils import getToolByName

from plone.portlets.interfaces import IPortletDataProvider
from plone.app.portlets.portlets import base

from getpaid.core import interfaces

from Products.PloneGetPaid.interfaces import ICurrencyFormatter
from Products.PloneGetPaid.browser.interfaces import IDontShowGetPaidPortlets

from Products.PloneGetPaid import _


class IShoppingCartPortlet(IPortletDataProvider):
    """A portlet

    It inherits from IPortletDataProvider because for this portlet, the
    data that is being rendered and the portlet assignment itself are the
    same.
    """

    omit_border = schema.Bool(
        title=_(u"Omit portlet border"),
        description=_(u"Tick this box if you want to render the list without borders and header."),
        required=True,
        default=False)

    omit_header = schema.Bool(
        title=_(u"Omit only portlet header"),
        description=_(u"Tick this box if you want to render the list only without header."),
        required=True,
        default=False)


class Assignment(base.Assignment):
    """Portlet assignment.

    This is what is actually managed through the portlets UI and associated
    with columns.
    """

    interface.implements(IShoppingCartPortlet)

    title = _(u"Shopping cart")
    description = _(u"A portlet, which displays user's shopping cart with actions")

    omit_border = False
    omit_header = False

    def __init__(self, omit_border=False, omit_header=False):
        super(Assignment, self).__init__()
        self.omit_border = omit_border
        self.omit_header = omit_header


class Renderer(base.Renderer):
    """Portlet renderer.

    This is registered in configure.zcml. The referenced page template is
    rendered, and the implicit variable 'view' will refer to an instance
    of this class. Other methods can be added and referenced in the template.
    """
    render = ViewPageTemplateFile("../templates/portlet-shopping-cart.pt")

    @property
    def available(self):
        return not IDontShowGetPaidPortlets.providedBy(self.view) \
            and self.cart and self.size > 0

    @property
    def cart(self):
        manager = component.getUtility( interfaces.IShoppingCartUtility )
        return manager.get(self.context, create=False)

    @property
    def size(self):
        return self.cart and len(self.cart)

    @property
    def totals(self):
        totals = interfaces.ILineContainerTotals(self.cart)
        currency = component.getUtility(ICurrencyFormatter)
        return {
            'subtotal': currency.format(totals.getSubTotalPrice()),
            'taxes': [{'value': currency.format(math.fabs(t['value'])),
                       'id': t['id'], 'name': t['name']} for t in totals.getTaxCost()],
            'shipping': currency.format(totals.getShippingCost()),
            'total': currency.format(totals.getTotalPrice())
            }


class AddForm(base.AddForm):
    """Portlet add form.

    This is registered in configure.zcml. The form_fields variable tells
    zope.formlib which fields to display. The create() method actually
    constructs the assignment that is being added.
    """
    form_fields = formlib.form.Fields(IShoppingCartPortlet)

    def create(self, data):
        return Assignment(**data)


class EditForm(base.EditForm):
    """Portlet edit form.

    This is registered with configure.zcml. The form_fields variable tells
    zope.formlib which fields to display.
    """
    form_fields = formlib.form.Fields(IShoppingCartPortlet)
