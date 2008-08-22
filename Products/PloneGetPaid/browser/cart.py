"""
Viewlet / Formlib / zc.table Based Shopping Cart

$Id$
"""

import os
from urllib import urlencode

from zope import component, interface
from zope.formlib import form
from zc.table import column, table

from ore.viewlet.container import ContainerViewlet
from ore.viewlet.core import FormViewlet

from getpaid.core import interfaces

from AccessControl import getSecurityManager

from Products.Five.viewlet import manager
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile

from Products.CMFCore.utils import getToolByName

from Products.PloneGetPaid.interfaces import PayableMarkers, IGetPaidCartViewletManager
from Products.PloneGetPaid.interfaces import IGetPaidManagementOptions, IConditionalViewlet
from Products.PloneGetPaid import sessions
from Products.PloneGetPaid import config

from Products.PloneGetPaid.i18n import _
from Products.CMFPlone.utils import safe_unicode

#################################
# Shopping Cart Views

class ShoppingCart( BrowserView ):

    _cart = None

    def __call__( self ):
        self.manager = ShoppingCartManager( self.context, self.request, self )
        self.manager.update()
        return super( ShoppingCart, self ).__call__()

    def getCart( self ):
        if self._cart is not None:
            return self._cart
        cart_manager = component.getUtility( interfaces.IShoppingCartUtility )
        self._cart = cart = cart_manager.get( self.context, create=True )
        return cart

    cart = property( getCart )

    def isContextAddable( self ):
        addable = filter( lambda x, s=self.context: x.providedBy(s), PayableMarkers )
        return not not addable

    def size( self ):
        if self.cart is None:
            return 0
        return self.cart.size()

class ShoppingCartAddItem( ShoppingCart ):
    """
    item we're adding is the context
    """

    def __call__( self ):
        if self.request.has_key('add_item'):
            self.addToCart()
        return super( ShoppingCartAddItem, self ).__call__()

    def addToCart( self ):
        # create a line item and add it to the cart
        item_factory = component.getMultiAdapter( (self.cart, self.context), interfaces.ILineItemFactory )
        # check quantity from request
        qty = int(self.request.get('quantity', 1))
        item_factory.create(quantity=qty)


class ShoppingCartAddItemAndGoToCheckout(ShoppingCartAddItem):
    def addToCart( self ):
        # XXX this duplicates functionality available elsewhere
        #     (in the name of simplicity -- pah)
        super(ShoppingCartAddItemAndGoToCheckout, self).addToCart()
        portal = getToolByName( self.context, 'portal_url').getPortalObject()
        url = portal.absolute_url()
        # check if anonymous checkout is allowed
        if IGetPaidManagementOptions(portal).allow_anonymous_checkout or \
            getSecurityManager().getUser().getId() is not None:
            url = url + '/@@getpaid-checkout-wizard'
        else:
            url = "%s/%s?%s"%( url,
                               'login_form',
                               urlencode([('came_from',
                                           url + '/@@getpaid-checkout-wizard')]))
        return self.request.RESPONSE.redirect( url )

def verifyItems( cart ):
    """ verify that all the objects in the cart can be resolved, removing
    items that can no longer be resolved and returning them """
    remove = []
    for item in cart.values():
        if interfaces.IPayableLineItem.providedBy( item ):
            if item.resolve() is None:
                remove.append( item )
    for item in remove:
        del cart[ item.item_id ]
    return remove

#################################
# Shopping Cart Viewlet Manager

_prefix = os.path.dirname( __file__ )

GetPaidShoppingCartTemplate = os.path.join( _prefix, "templates", "viewlet-manager.pt")

class ViewletManagerShoppingCart( object ):
    """ Shopping Cart Viewlet Manager """

    def filter( self, viewlets ):
        viewlets = super( ViewletManagerShoppingCart, self).filter( viewlets )

        for n,v in viewlets[:]:
            if IConditionalViewlet.providedBy( v ):
                if not v.condition():
                    viewlets.remove( ( n, v ) )
        return viewlets
                
    def sort (self, viewlets ):
        """ sort by name """
        viewlets.sort( lambda x,y: cmp( int(getattr(x[1],'weight',100)), int(getattr(y[1],'weight',100)) ) )
        return viewlets
        
ShoppingCartManager = manager.ViewletManager( "ShoppingCart",
                                              IGetPaidCartViewletManager,
                                              GetPaidShoppingCartTemplate,
                                              bases=(ViewletManagerShoppingCart,)
                                              )

#################################
# Shopping Cart Viewlets

class LineItemColumn( object ):

    def __init__(self, name):
        self.name = name

    def __call__( self, item, formatter ):
        value = getattr( item, self.name, '')
        if callable( value ):
            return value()
        return value

def lineItemURL( item, formatter ):
    return '<a href="reference_catalog/lookupObject?uuid=%s">%s</a>'  % (item.item_id, safe_unicode(item.name))

def lineItemTotal( item, formatter ):
    return "%0.2f" % (item.quantity * item.cost)

def lineItemPrice( item, formatter ):
    return "%0.2f" % (LineItemColumn("cost")(item, formatter))


class CartFormatter( table.StandaloneSortFormatter ):

    def getTotals( self ):
        #if interfaces.IShoppingCart.providedBy( self.context ):
        return interfaces.ILineContainerTotals( self.context )
        
    def renderExtra( self ):
        if not len( self.context ):
            return super( CartFormatter, self).renderExtra()
        
        totals = self.getTotals()

        tax_list = totals.getTaxCost()
        shipping_price = totals.getShippingCost()
        subtotal_price = totals.getSubTotalPrice()
        total_price = totals.getTotalPrice()
        
        buffer = [ '<div class="getpaid-totals"><table class="listing">']
        buffer.append( '<tr><th>SubTotal</th><td style="border-top:1px solid #8CACBB;">%0.2f</td></tr>'%( subtotal_price ) )

        buffer.append( "<tr><th>Shipping</th><td>%0.2f</td></tr>"%( shipping_price ) )

        for tax in tax_list:
            buffer.append( "<tr><th>%s</th><td>%0.2f</td></tr>"%( tax['name'], tax['value'] ) )
        buffer.append( "<tr><th>Total</th><td>%0.2f</td></tr>"%( total_price ) )
        buffer.append('</table></div>')
                       
        return u''.join( buffer) + super( CartFormatter, self).renderExtra()
    
class ShoppingCartListing( ContainerViewlet ):

    actions = ContainerViewlet.actions.copy()

    columns = [
        column.SelectionColumn( lambda item: item.item_id, name="selection"),
        column.FieldEditColumn( _(u"Quantity"), 'edit', interfaces.ILineItem['quantity'], lambda item: item.item_id ),
        #column.GetterColumn( title=_(u"Quantity"), getter=LineItemColumn("quantity") ),
        column.GetterColumn( title=_(u"Name"), getter=lineItemURL ),
        column.GetterColumn( title=_(u"Price"), getter=lineItemPrice ),
        column.GetterColumn( title=_(u"Total"), getter=lineItemTotal ),
       ]

    selection_column = columns[0]
    quantity_column = columns[1]
    template = ZopeTwoPageTemplateFile('templates/cart-listing.pt')

    formatter_factory = CartFormatter
    
    def __init__( self, *args, **kw):
        super( ShoppingCartListing, self ).__init__( *args, **kw )

    def getContainerContext( self ):
        return self.__parent__.cart

    def isOrdered( self, *args ):
        # shopping cart should not be ordered, so override this with False
        return False
    
    def isPlone3(self):
        return config.PLONE3
    
    @form.action(_("Update"), condition="isNotEmpty")
    def handle_update( self, action, data ):
        try:
            data = self.quantity_column.input(self.container.values(), self.request)
            self.form_reset = True
            self.quantity_column.update(self.container.values(), data)
            for item_id in self.container:
                if self.container[item_id].quantity == 0:
                    del self.container[ item_id ]
        except:
            raise
            self.form_reset = True
            #reset the form data in the request
            for i in self.request.form.keys():
                self.request.form.pop(i)


class ShoppingCartActions( FormViewlet ):

    template = ZopeTwoPageTemplateFile('templates/cart-actions.pt')

    def render( self ):
        return self.template()

    def doesCartContainItems( self, *args ):
        return bool(  len( self.__parent__.cart ) )

    def isLoggedIn( self, *args ):
        return getSecurityManager().getUser().getId() is not None

    def isAnonymous( self, *args ):
        return getSecurityManager().getUser().getId() is None

    @form.action(_("Continue Shopping"), name='continue-shopping')
    def handle_continue_shopping( self, action, data ):
        # redirect the user to the last thing they were viewing if there is not
        # such thing to the came_from variable and if this doesn't exist neither
        # to the portal base url, it is better than nothing
        came_from = sessions.get_came_from_url(self.context)
        if came_from:
            next_url = came_from
        else:
            last_item = getattr(self.__parent__.cart,'last_item',None)
            if not last_item:
                payable = getToolByName(self.context, 'portal_url').getPortalObject()
            else:
                payable = getToolByName( self.context, 'reference_catalog').lookupObject( last_item )
            if not self.request.get('came_from'):
                next_url = payable.absolute_url() 
            else:
                next_url = self.request.get('came_from')
        return self.request.RESPONSE.redirect(next_url)

    @form.action(_("Checkout"), condition="doesCartContainItems", name="Checkout")
    def handle_checkout( self, action, data ):
        # go to order-create
        # force ssl? redirect host? options
        portal = getToolByName( self.context, 'portal_url').getPortalObject()
        url = portal.absolute_url() + '/@@getpaid-checkout-wizard'
        return self.request.RESPONSE.redirect( url )

class OrderTemplate( FormViewlet ):
    
    form_fields = form.Fields()
    template = ZopeTwoPageTemplateFile('templates/cart-order-template.pt')
    
    form_name = _(u"Order Templates")
    form_description = _(u"Select a previous order to fill your cart.")
    
    interface.implements( IConditionalViewlet )
    
    prefix = "order-template"
    
    orders = ()
    
    def render( self ):
        return self.template()

    def condition( self ):
        uid = getSecurityManager().getUser().getId()
        if uid == 'Anonymous':
            return False
        order_manager = component.getUtility( interfaces.IOrderManager )
        self.orders = order_manager.query( user_id=uid )
        if len(self.orders):
            return True
        return False

    def condition_load_template( self, action ):
        return self.condition()
        
    @form.action(_("Fill"), condition="condition_load_template")
    def handle_load_template( self, action, data):
        
        order_id = self.request.form.get('order-template-id')
        found = False
        for o in self.orders:
            if o.order_id == order_id:
                found = True
                break
                
        if not found:
            self.status = _(u"Could not find order")
            return
        
        # fetch cart from view
        cart = self.manager.__parent__.cart
        
        for v in o.shopping_cart.values():
            content = v.resolve()
            item_factory = component.getMultiAdapter( (cart, content), 
                                     interfaces.ILineItemFactory )
            item_factory.create( quantity = v.quantity )
        
        self.status = _(u"Previous Order Loaded into Cart")        
