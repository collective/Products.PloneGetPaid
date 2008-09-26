"""
$Id$
"""

from Products.Five.browser import BrowserView
from Products.PloneGetPaid import interfaces
from getpaid.core.interfaces import IShoppingCartUtility
from Products.PloneGetPaid.interfaces import ICountriesStates
from zope import component
from zope.app import zapi
from simplejson import JSONEncoder

class StatesAjax(BrowserView):
    def __call__(self):
        country = self.request.get('country')
        required = self.request.get('required','').lower().strip() == 'true'
        utility = zapi.getUtility(ICountriesStates)
        jsonEncoder = JSONEncoder()
        return jsonEncoder.encode(utility.states(country=country,
                                                 allow_no_values=not required))

class ShoppingCart( BrowserView ):

    _cart = None
    
    __allow_access_to_unprotected_subobjects__ = 1
    
    def getCart( self ):
        if self._cart is not None:
            return self._cart
        cart_manager = component.getUtility( IShoppingCartUtility )
        self._cart = cart = cart_manager.get( self.context, create=False )
        return cart
    
    cart = property( getCart )

    def isContextAddable( self ):
        addable = filter( lambda x, s=self.context: x.providedBy(s), interfaces.PayableMarkers )
        return not not addable 
    
    def size( self ):
        if self.cart is None:
            return 0
        return len( self.cart )

class ContentWidget( BrowserView ):
    """Content Widget Portlet"""
    
    def isPayable( self ):
        addable = filter( lambda x, s=self.context: x.providedBy(s), interfaces.PayableMarkers )
        return not not addable 

