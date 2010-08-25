"""
plone.z3cform + plone.z3ctable based shopping cart edit form and content provider
"""

__version__ = "$Revision$"
# $Id$
# $URL$

import math

from zope import component, event, interface, lifecycleevent, schema

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.Five.browser import BrowserView
from Products.CMFCore.utils import getToolByName

from z3c.form import button, field, group, form
from z3c.form.interfaces import IFormLayer, IFieldsForm, INPUT_MODE, DISPLAY_MODE, HIDDEN_MODE

from z3c.table import column, table
from z3c.table.interfaces import IColumn

# @view.memoize cache values for the lifespan of request
# from plone.memoize import view 

from getpaid.core import interfaces

from Products.PloneGetPaid.interfaces import ICurrencyFormatter
from Products.PloneGetPaid.browser.interfaces import IDontShowGetPaidPortlets
from Products.PloneGetPaid import _


class ILineItemDisplayAdapter(interface.Interface):
    """
    Adapter interface for GetAdaptedAttrColumn to get
    regular, formatted and computed properties for ILineItem.
    """
    uid = schema.TextLine(
        title = _(u"Unique Item Id"))
    title = schema.TextLine(
        title = _(u"Title"))
    description = schema.TextLine(
        title = _(u"Description"))
    price = schema.Float(
        title = _(u"Unit price"))
    quantity = schema.Int(
        title = _(u"Quantity"))
    total = schema.Float(
        title = _(u"Total price"))


class GetAdaptedAttrColumn(column.GetAttrColumn):
    """
    GetAttrColumn with ILineItemsDisplayAdapter support. This
    allows us to use the same column setup for both read-only
    tables and form tables.
    """
    def renderCell(self, item):
        adapted_item = component.getMultiAdapter(
            (self.context, self.request, item), ILineItemDisplayAdapter)
        return super(GetAdaptedAttrColumn, self).renderCell(adapted_item)


class LineItemDisplayAdapter(object):
    """ Adapter for regular ILineItems """
    interface.implements(ILineItemDisplayAdapter)
    def __init__(self, context, request, item):
        self.context = context
        self.request = request
        self.item = item

    @property
    def uid(self):
        return getattr(self.item, "item_id")

    @property
    def title(self):
        return getattr(self.item, "name")

    @property
    def description(self):
        return getattr(self.item, "description")

    @property
    def quantity(self):
        return getattr(self.item, "quantity")

    @property
    def price(self):
        cost = getattr(self.item, "cost")
        currency = component.getUtility(ICurrencyFormatter)
        return currency.format(cost)

    @property
    def total(self):
        cost = getattr(self.item, "cost")
        quantity = getattr(self.item, "quantity")
        currency = component.getUtility(ICurrencyFormatter)
        return currency.format(cost * quantity)


class LineItemFormDisplayAdapter(LineItemDisplayAdapter):
    """ Adapter for ILineItems bundled as line_item property on IFieldsForm """
    def __init__(self, context, request, group):
        self.context = context
        self.request = request
        self.item = group.line_item # (!)


class WidgetColumn(GetAdaptedAttrColumn):
    """ an abstract z3c.form widget column for z3c.table with fallback to GetAdaptedAttrColumn """
    attrName = None
    editable = False

    template = ViewPageTemplateFile("templates/z3c-table-form-field.pt")

    def renderCell(self, item):
        if IFieldsForm.providedBy(item):
            item.widgets[self.attrName].mode = self.editable and INPUT_MODE or DISPLAY_MODE
            return self.template(self.table, widget=item.widgets[self.attrName])
        return super(WidgetColumn, self).renderCell(item)


class LineItemFormGroup(group.Group):
    """ a z3c.form group.Group representing a single ILineItem """
    fields = field.Fields(interfaces.ILineItem).select(u"quantity")
    line_item = None

    @property
    def __name__(self):
        return self.line_item.item_id

    @property
    def prefix(self):
        return self.line_item.item_id

    def __init__(self, context, request, parentForm, line_item):
        super(LineItemFormGroup, self).__init__(context, request, parentForm)
        self.line_item = line_item
        
    def update(self):
        super(LineItemFormGroup, self).update()
        self.widgets[u"quantity"].size = 3

    def getContent(self):
        return self.line_item


class LinkColumn(column.LinkColumn):
    weight = 20
    header = _(u"Title")

    def getLinkContent(self, item):
        adapted_item = component.getMultiAdapter(
            (self.context, self.request, item), ILineItemDisplayAdapter)
        return getattr(adapted_item, "title")

    def getLinkURL(self, item):
        adapted_item = component.getMultiAdapter(
            (self.context, self.request, item), ILineItemDisplayAdapter)
        return "reference_catalog/lookupObject?uuid=%s" % (getattr(adapted_item, "uid"))


class QuantityColumn(WidgetColumn):
    weight = 30
    header = _(u"Quantity")
    attrName = u"quantity"
    editable = True


class PriceColumn(GetAdaptedAttrColumn):
    weight = 40
    header = _(u"Price")
    attrName = u"price"


class TotalColumn(GetAdaptedAttrColumn):
    weight = 50
    header = _(u"Total")
    attrName = u"total"


class RemovableColumn(column.CheckBoxColumn):
    weight = 100
    header = _(u"Remove")

    def isSelected(self, item):
        if self.table.ignoreRequest:
            return False
        else:
            return super(RemovableColumn, self).isSelected(item)


class LineItemContainerTable(table.SequenceTable):
    """ a z3c.table for rendering line item container """

    cssClasses = {'table': u"listing", 'th': u"nosort", 'td': u"notDraggable"}
    cssClassEven = u"even"
    cssClassOdd = u"odd"

    container = None
            
    def __init__(self, context, request):
        super(LineItemContainerTable, self).__init__(context, request)

    @property        
    def values(self):
        return self.container and self.container.values() or tuple()

    def update(self):
        if self.container:
            super(LineItemContainerTable, self).update()

    def setUpColumns(self):
        cols = list(component.getAdapters(
            (self.container, self.request, self), IColumn))
        # use the adapter name as column name                                                
        return [table.nameColumn(col, name) for name, col in cols if col.weight < 100]


class LineItemContainerEditForm(LineItemContainerTable, group.GroupForm, form.EditForm):
    """ a z3c.form for container's ILineItems using z3c.table
    
    NOTE: form.EditForm provides 'apply'-@buttonAndHandler and this class could be
    used to update ILineItemContainer's contents as it is, but it doesn't do anything
    with selection data provided by SelectionColumn in cooperation with z3c.table,
    if it's enabled (it's disabled, because it's more confusing than simply setting
    product quantity to zero or making a JavaScript "x"-link for doing it).
    """
    interface.implements(IDontShowGetPaidPortlets)

    groups = None
    groupClass = LineItemFormGroup

    # An example template, which is overriden in ShoppingCartEditForm-class.
    render = ViewPageTemplateFile("templates/z3c-table-form.pt")

    def __init__(self, context, request, container=None):
        super(LineItemContainerEditForm, self).__init__(context, request)
        if interfaces.ILineItemContainer.providedBy(container):
            self.container = container
        # Adds IFormLayer for request to support z3c.form
        interface.alsoProvides(self.request, IFormLayer)

    @property
    def values(self):
        return self.groups

    def setUpColumns(self):
        cols = list(component.getAdapters(
            (self.container, self.request, self), IColumn))
        # use the adapter name as column name                                                
        return [table.nameColumn(col, name) for name, col in cols]

    def getContent(self):
        return self.container and self.container.values() or tuple()

    def update(self):
        self.updateWidgets()
        if self.groups is None:
            self.groups = tuple([self.groupClass(self.context, self.request, self, line_item)
                                 for line_item in self.getContent()])
        for group in self.groups:
            group.update()
        self.updateActions()
        self.actions.execute()
        if self.refreshActions:
            self.updateActions()
        table.SequenceTable.update(self)

    def extractData(self, setErrors=True):
        """See interfaces.IEditForm and group.GroupForm's implementation """
        data, errors = form.EditForm.extractData(self, setErrors=setErrors)
        for group in self.groups:
            groupData, groupErrors = group.extractData(setErrors=setErrors)
            data.update({group.prefix: groupData}) # (!)
            if groupErrors:
                if errors:
                    errors += groupErrors
                else:
                    errors = groupErrors
        return data, errors

    def applyChanges(self, data):
        """See interfaces.IEditForm and group.GroupForm's implementation """
        content = self.getContent()
        changes = {}
        for group in self.groups:
            groupData = data.has_key(group.prefix) and data[group.prefix] or {}
            groupChanges = group.applyChanges(groupData) # (!)
            groupContent = group.getContent()
            for interface, names in groupChanges.items():
                if not changes.has_key(groupContent):
                    changes[groupContent] = {}
                changes[groupContent][interface] = changes[groupContent].get(interface, []) + names
        if changes:
            for groupContent, groupChanges in changes.items():
                descriptions = []
                for interface, names in groupChanges.items():
                    descriptions.append(
                        lifecycleevent.Attributes(interface, *names))
                # Send out a detailed object-modified event for every modified ILineItem      
                event.notify(
                    lifecycleevent.ObjectModifiedEvent(groupContent,
                        *descriptions))
        content = self.getContent()
        changes.update(form.applyChanges(self, content, data))
        return changes


class EmptyShoppingCart(object):
    render = ViewPageTemplateFile("templates/shopping-cart-empty.pt")
    def __init__(self, context, request, view):
        self.context = context
        self.request = request
        self.__parent__ = view
    def update(self):
        pass


class IOrderId(interface.Interface):
    order_id = schema.Text(title=_(u"Order Id"), required=False)


class IShowEditLink(interface.Interface):
    show_edit_link = schema.Text(title=_(u"Show Edit Link"), required=False)


class ShoppingCart(LineItemContainerTable):
    interface.implements(IOrderId, IShowEditLink)
    render = ViewPageTemplateFile("templates/shopping-cart.pt")

    def __init__(self, context, request, view=None):
        super(ShoppingCart, self).__init__(context, request)
        if view is not None:
            self.__parent__ = view

    @property
    def cart(self):
        """ Shopping cart """
        return self.container

    @property
    def container(self):
        if hasattr(self, "order_id") and self.order_id:
            manager = component.getUtility(interfaces.IOrderManager)
            return self.order_id in manager and manager.get(self.order_id).shopping_cart or None
        else:
            manager = component.getUtility(interfaces.IShoppingCartUtility )
            return manager.get(self.context, create=False) or None

    @property
    def totals(self):
        totals = interfaces.ILineContainerTotals(self.container)
        currency = component.getUtility(ICurrencyFormatter)
        return {
            'subtotal': currency.format(totals.getSubTotalPrice()),
            'taxes': [{'value': currency.format(math.fabs(t['value'])),
                       'id': t['id'], 'name': t['name']} for t in totals.getTaxCost()],
            'shipping': currency.format(totals.getShippingCost()),
            'total': currency.format(totals.getTotalPrice())
            }


class ShoppingCartForm(ShoppingCart, LineItemContainerEditForm):
    render = ViewPageTemplateFile("templates/shopping-cart-form.pt")

    successMessage = _(u"Shopping cart successfully updated.")

    @property
    def refererURL(self):
        portal_url = getToolByName(self.context, "portal_url")
        site = portal_url.getPortalObject()
        referer = self.request.get('GETPAID_REFERER', self.request.environ.get('HTTP_REFERER', None))
        return referer or site.absolute_url()

    def _updateForm(self):
        self.updateWidgets()
        for group in self.groups:
            group.update()
 
    @button.buttonAndHandler(_("Cancel"), name='cancel')
    def handleCancel(self, action):
        self.request.response.redirect(self.refererURL)
#        self.ignoreRequest = True
#        self._updateForm()
        
    @button.buttonAndHandler(_("Save changes"), name='save')
    def handleApply(self, action):
        form.EditForm.handleApply(self, action)
        # Remove items with zero quantity from the shopping cart
        removables = [g for g in self.groups if g.line_item.quantity == 0]
        # Remove items marked as removables from the shopping cart
        table.SequenceTable.update(self)
        removables.extend(self.selectedItems)
        if removables:
            for group in removables:
                del self.container[group.getContent().item_id]
            self.groups = [g for g in self.groups if g not in removables]
            self.status = self.successMessage
            self._updateForm()
        # Redirect to referer when if the has been emptied
        if not self.cart:
            utils = getToolByName(self.context, 'plone_utils')
            utils.addPortalMessage(_(u"Your shopping cart is now empty."))
            self.request.response.redirect(self.refererURL)

    @button.buttonAndHandler(_("Continue shopping"), name='continue')
    def handleContinue(self, action):
        self.request.response.redirect(self.refererURL)

    @button.buttonAndHandler(_("Checkout"), name='checkout')
    def handleCheckout(self, action):
        portal_url = getToolByName(self.context, "portal_url")
        site = portal_url.getPortalObject()
        self.request.response.redirect(site.absolute_url() + "/@@checkout")
