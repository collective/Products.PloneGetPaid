"""
Paid Content Support

Any piece of content can be integrated with getpaid, either on a content type basis or for
any individual piece of content. [ XXX currently we only support individual pieces of content ]

The applied zope3 interface allows us to use an adapter to add the component architecture to
create views and adapters for the content. BuyableContent is delivered virtually, such as
electronic PDF or simply viewing the content on the site.

ShippableContent describes a physical, tangible item that must be shipped to an address. 
Gift cards, products like T-Shirts, or paper-based content that goes into an envelope are 
all examples of ShippableContent. This allows a content object to be added to a shopping cart, 
shipped, etc.

PremiumContent implies that the consumer of the content has a local role of Premium Member for the
content.  This role is granted if the consumer has a certain subscription level (set in the product
configuration.) *** this section needs to be explained better ***

DonateContent implies that the content is a donation.

To allow for per instance application of content types, we provide an action for archetypes
under the content actions drop down to apply getpaid integration, the condition for this action
invokes a premium content control view which in turn checks the control panel configuration
for this content, by interface or content type.

content security, we want to set local roles for users who buy content, we do this via

content view snippets.. we still need to figure out if we can override the default view
of a content object via applying an interface to it.

$Id$
"""

from zope import interface, component
from zope.app.intid.interfaces import IIntIds

from getpaid.core import interfaces, item
from getpaid.core import options

from interfaces import IDonationLevel, IPayableMarker
from Products.PloneGetPaid import sessions

class LineItemFactory( object ):
    """
    adapts to cart and content (payable marker marked), and creates a line item
    from said item for cart.
    """
    
    def __init__( self, cart, content ):
        self.cart = cart
        self.content = content

    def create( self, quantity=1 ):
        
        if self.checkIncrementCart( self.content, quantity=quantity ):
            return
        
        payable = self.checkPayable( self.content )
        nitem = self.createLineItem( payable, quantity)
        self.cart[ nitem.item_id ] = nitem
        sessions.set_came_from_url(self.content)
        return nitem
        
    def checkIncrementCart( self, content, quantity=1 ):
        item_id = content.UID()
        if item_id in self.cart:
            self.cart[ item_id ].quantity += quantity
            return True
        
    def checkPayable( self, content):
        if not IPayableMarker.providedBy( content ):
            raise RuntimeError("Invalid Context For Cart Add")
        return interfaces.IPayable( content )
        
    def createLineItem( self, payable, quantity ):
        nitem = item.PayableLineItem()
        nitem.item_id = self.content.UID() # archetypes uid
        
        # we use intids to reference content that we can dereference cleanly
        # without access to context.
        nitem.uid = component.getUtility( IIntIds ).register( self.content )
        
        def getUnicodeString( s ):
            """Try to convert a string to unicode from utf-8, as this is what Archetypes uses"""
            if type( s ) is type( u'' ):
                # this is already a unicode string, no need to convert it
                return s
            elif type( s ) is type( '' ):
                # this is a string, let's try to convert it to unicode
                try:
                    return s.decode( 'utf-8' )
                except UnicodeDecodeError, e:
                    # not utf-8... return as is and hope for the best
                    return s

        # copy over information regarding the item
        nitem.name = getUnicodeString( self.content.Title() )
        nitem.description = getUnicodeString( self.content.Description() )
        nitem.cost = payable.price
        nitem.quantity = int( quantity )
        nitem.product_code = payable.product_code
        
        return nitem
 
class ShippableItemFactory( LineItemFactory ):
    
    def createLineItem( self, payable, quantity ):
        
        nitem = item.PayableShippableLineItem()
        nitem.item_id = self.content.UID() # archetypes uid
        
        # we use intids to reference content that we can dereference cleanly
        # without access to context.
        nitem.uid = component.getUtility( IIntIds ).register( self.content )
        
        # copy over information regarding the item
        nitem.name = self.content.Title()
        nitem.description = self.content.Description()
        nitem.cost = payable.price
        nitem.quantity = int( quantity )
        nitem.product_code = payable.product_code
        nitem.weight = float( payable.weight )
        
        return nitem
                

#################################
# Buyable Content

"""
when buyable content is deleted, we still want to be able to keep a reference to it
for those who have paid, or at least replace any shopping cart / transaction references
with information.
"""

BuyableContentStorage = options.PersistentOptions.wire( "BuyableContentStorage", "getpaid.content.buyable", interfaces.IBuyableContent )

class BuyableContentAdapter( BuyableContentStorage ):
    """
    Default Adapter between Content and IBuyable. This implementation stores attributes
    of a buyable in an annotation adapter
    """
    interface.implements( interfaces.IBuyableContent )
    
    def __init__( self, context ):
        self.context = context
    

#################################
# Shippable Content
"""
shippable deletions need to track orders not shipped 
"""

ShippableContentStorage = options.PersistentOptions.wire( "ShippableContentStorage", "getpaid.content.shippable", interfaces.IShippableContent )

class ShippableContentAdapter( ShippableContentStorage ):

    interface.implements( interfaces.IShippableContent )
    
    def __init__( self, context ):
        self.context = context

#################################
# Premium Content

PremiumContentStorage = options.PersistentOptions.wire( "PremiumContentStorage", "getpaid.content.buyable", interfaces.IPremiumContent )

class PremiumContentAdapter( PremiumContentStorage ):

    interface.implements( interfaces.IPremiumContent )
    
    def __init__( self, context ):
        self.context = context

#################################
# Donatable Content

"""
"""

DonatableContentStorage = options.PersistentOptions.wire( "DonatableContentStorage", "getpaid.content.donate", interfaces.IDonationContent )

class DonationLevel( object ):

    interface.implements( IDonationLevel )

    title = ''
    amount = 0

class DonatableContentAdapter( DonatableContentStorage ):
    """
    Default Adapter between Content and IDonationContent. This implementation stores attributes
    of a donate-able in an annotation adapter
    """
    interface.implements( interfaces.IDonationContent )

    def __init__( self, context ):
        self.context = context

