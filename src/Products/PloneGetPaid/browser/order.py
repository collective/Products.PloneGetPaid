"""
Order Admin and Customer History

$Id$
"""
import os

from Products.Five.browser import BrowserView
from Products.Five.viewlet.manager import ViewletManager
from Products.Five.traversable import FiveTraversable
from OFS.SimpleItem import SimpleItem

from Products.PloneGetPaid import interfaces as ipgp

from zope import component, interface
from zope.app.traversing.interfaces import ITraversable

from getpaid.core.order import query
from getpaid.core import interfaces as igpc

from Products.PloneGetPaid.i18n import _

# from getpaid.core.interfaces import IOrderManager
from AccessControl import getSecurityManager

_marker = object()


class UserOrderHistory( BrowserView ):
    """ browser view for a user's order history """
    def __call__( self ):
        uid = getSecurityManager().getUser().getId()
        if not uid:
            self.request.response.redirect("login_form?came_from=@@getpaid-order-history")
            return ""
        self.manager = OrderHistoryManager( self.context, self.request, self )
        self.manager.update()
        return super( UserOrderHistory, self ).__call__()
        
# viewlet manager for the same
class ViewletManagerOrderHistory(object):
    """ Order History Viewlet Manager """

    def sort (self, viewlets):
        """ Sort by name """
        return sorted(viewlets)


OrderHistoryManager = ViewletManager("OrderHistory",
                                     ipgp.IOrderHistoryManager,
                                     os.path.join( os.path.dirname( __file__ ),
                                                   "templates",
                                                   "viewlet-manager.pt"),
                                     bases=(ViewletManagerOrderHistory,)
                                     )

class UserOrderHistoryComponent:
    """ order history listing...  """
    def history( self ):
        #  - does this really benefit from the additional complexity
        #    of being a viewlet?
        uid = getSecurityManager().getUser().getId()
        orders = []
        for order in query.search(user_id=uid):
            orders.append({'id': order.order_id,
                           'date': order.creation_date.strftime('%Y-%m-%d %H:%M'),
                           'finance_state': order.finance_state,
                           'fulfillment_state': order.fulfillment_state,
                           'log': tuple(igpc.IOrderWorkflowLog( order ))})
        return orders


#################################
# Views for looking at a single order, we do some traversal tricks to make the
# the orders exposeable ttw.

OrderDetailsManager = ViewletManager(
    "OrderDetails",
    ipgp.IOrderDetailsManager,
    os.path.join( os.path.dirname( __file__ ),
                  "templates",
                  "viewlet-manager.pt")
    )


class OrderDetails( BrowserView ):
    """ an order view
    """
    
    def __call__( self ):
        self.manager = OrderDetailsManager( self.context, self.request, self )
        self.manager.update()
        return super( OrderDetails, self).__call__()
    

class OrderRoot( BrowserView, FiveTraversable ):
    """ a view against the store which allow us to expose individual order objects
    """
    interface.implements( ITraversable )
    
    def __init__( self, context, request ):
        self.context = context
        self.request = request

    def __bobo_traverse__( self, request, name ):
        value = getattr( self, name, _marker )
        if value is not _marker:
            return value
        manager = component.getUtility( igpc.IOrderManager )
        order = manager.get( name )
        if order is None:
            raise AttributeError( name )
        return TraversableWrapper( order ).__of__( self.context )


class TraversableWrapper( SimpleItem ):
    """ simple indeed, a zope2 transient wrapper around a persistent order so we can
    publish them ttw.
    """
    
    interface.implements( igpc.IOrder )

    id = title = _(u"Order Details")
    
    def Title( self ):
        return self.title
    
    def __init__( self, object ):
        self._object = object

    def __getattr__( self, name ):
        value =  getattr( self._object, name, _marker )
        if value is not _marker:
            return value
        return super( TraversableWrapper, self).__getattr__( name )

