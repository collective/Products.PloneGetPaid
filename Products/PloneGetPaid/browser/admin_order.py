"""
order administration
"""

import datetime, os, inspect, StringIO, csv
import time

from zope import component, schema, interface
from zope.app import zapi
from zope.schema.interfaces import IContextSourceBinder
from zope.schema import vocabulary
from zope.viewlet.interfaces import IViewlet
from zope.formlib import form

from zExceptions import Unauthorized
from zc.table import table, column
from ore.viewlet import core

from getpaid.core import interfaces
from getpaid.core.order import OrderQuery as query
from getpaid.core.interfaces import IOrderManager
from hurry.workflow.interfaces import IWorkflowInfo

from Products.CMFCore.utils import getToolByName

from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from Products.Five.viewlet import viewlet, manager as viewlet_manager

from Products.PloneGetPaid import interfaces as ipgp
from Products.PloneGetPaid.i18n import _
from Products.PloneGetPaid.interfaces import ICountriesStates
from Products.PloneGetPaid.vocabularies import TitledVocabulary

from yoma.batching import BatchingMixin, RenderNav

from order import OrderRoot


def renderOrderId( order, formatter ):
    return '<a href="@@admin-manage-order/%s/@@admin">%s</a>'%( order.order_id, order.order_id )

class AttrColumn( object ):

    def __init__(self, name):
        self.name = name

    def __call__( self, item, formatter ):
        value = getattr( item, self.name, '')
        if callable( value ):
            return value()
        return value

class DateColumn( AttrColumn ):

    def __call__( self, item, formatter ):
        value = super( DateColumn, self).__call__( item, formatter )
        return value.isoformat()

class PriceColumn( AttrColumn ):

    def __call__( self, item, formatter ):
        value = super( PriceColumn, self).__call__( item, formatter )
        return "%0.2f"%value

class MyRenderNav (RenderNav):
    def renderPrev(self):
        # is '*-batch' the right name for these classes?
        print >> self.out, '<span class="prev-batch">'
        super(MyRenderNav, self).renderPrev()
        print >> self.out, '</span><span class="next-batch">'
        super(MyRenderNav, self).renderNext()
        print >> self.out, '</span><span class="current-batch">'
    def renderNext(self):
        print >> self.out, '</span>'

class MyBatchingMixin (BatchingMixin):
    rendernav_factory = MyRenderNav

class BatchingFormatter( MyBatchingMixin, table.StandaloneFullFormatter ):
    pass

class OrderListingComponent( core.EventViewlet ):

    template = ZopeTwoPageTemplateFile('templates/orders-listing.pt')
    
    columns = [
        column.GetterColumn( title=_(u"Order Id"), getter=renderOrderId ),
        column.GetterColumn( title=_(u"Customer Id"), getter=AttrColumn("user_id" ) ),        
        column.GetterColumn( title=_(u"Status"), getter=AttrColumn("finance_state") ),
        column.GetterColumn( title=_(u"Fulfillment"), getter=AttrColumn("fulfillment_state") ),
        column.GetterColumn( title=_(u"Price"), getter=PriceColumn("getTotalPrice") ),
        column.GetterColumn( title=_(u"Created"), getter=DateColumn("creation_date") )
        ]

    order = 2
    
    def render( self ):
        return self.template()
    
    def listing( self ):
        columns = self.columns
        values = self.manager.get('orders-search').results
        if not values:
            message = u'No orders found for your filter.'
            return self.context.utranslate(msgid=message, default=message, domain='plonegetpaid')
        
        formatter = BatchingFormatter( self.context,
                                      self.request,
                                      values,
                                      prefix="form",
                                      batch_size=10,
                                      visible_column_names = [c.name for c in columns],
                                      #sort_on = ( ('name', False)
                                      columns = columns )
        
        formatter.cssClasses['table'] = 'listing'
        return formatter()
    
class OrderCSVComponent( core.ComponentViewlet ):

    template = ZopeTwoPageTemplateFile('templates/orders-export-csv.pt')
    
    order = 3

    def render( self ):
        return self.template()

    @form.action(_(u"Export Search"))
    def export_search( self, action, data ):

        search = self.manager.get('orders-search')
        listing = self.manager.get('order-listing')

        io = StringIO.StringIO()
        writer = csv.writer( io )
        writer.writerow( [c.name for c in listing.columns ] )

        field_getters = []
        for column in listing.columns:
            if column.name == 'Order Id':
                field_getters.append( lambda x,y: x.order_id )
            else:
                field_getters.append( column.getter )

        for order in search.results:
            writer.writerow( [getter( order, None ) for getter in field_getters ] )

        # um.. send to user, we need to inform our view, to do the appropriate thing
        # since we can't directly control the response rendering from the viewlet
        self._parent._download_content = ('text/csv',  io.getvalue(), 'OrderSearchExport')
        
class OrderEmailsCSVComponent(core.ComponentViewlet):

    template = ZopeTwoPageTemplateFile('templates/orders-emails-export-csv.pt')
    
    order = 4

    def render(self):
        return self.template()

    @form.action(_(u"Export All"))
    def export_all(self, action, data):
        columns = ['User Id', 
                   'Contact Name', 
                   'Contact Email', 
                   'Marketing Preference', 
                   'Email Html Format']
        
        io = StringIO.StringIO()
        writer = csv.writer(io)
        writer.writerow([cname for cname in columns ])
        unique_emails = set()
        
        manager = zapi.getUtility(IOrderManager)
        for order in manager.storage.values():
            email = order.contact_information.email.lower()
            if email not in unique_emails:
                writer.writerow((order.user_id,
                                 order.contact_information.name,
                                 email,
                                 order.contact_information.marketing_preference,
                                 order.contact_information.email_html_format))
                unique_emails.add(email)

        # um.. send to user, we need to inform our view, to do the appropriate thing
        # since we can't directly control the response rendering from the viewlet
        self._parent._download_content = ('text/csv',  io.getvalue(), 'OrderEmailsExport')

def define( **kw ):
    kw['required'] = False
    return kw

class OrderSearchComponent( core.ComponentViewlet ):

    form_template = ZopeTwoPageTemplateFile('templates/form.pt')
    template = ZopeTwoPageTemplateFile('templates/orders-search-filter.pt')

    order = 1

    date_search_order = (
        ("last 7 days", datetime.timedelta( 7 )),
        ("last month", datetime.timedelta( 30 )),
        ("last 3 months", datetime.timedelta( 90 )),
        ("last year", datetime.timedelta( 365 )),
        )

    date_search_map = dict( date_search_order )

    results = None
    filtered = False
    _finance_values = [ m[1] for m in inspect.getmembers( interfaces.workflow_states.order.finance ) if m[0].isupper() ]
    _fulfillment_values = [ m[1] for m in inspect.getmembers( interfaces.workflow_states.order.fulfillment ) if m[0].isupper() ]
    
    form_fields = form.Fields( 
        schema.Choice( **define( title=u"Created", __name__=u"creation_date",
                                 values=( [ d[0] for d in date_search_order ] ),
                                 default="last 7 days") ),
        schema.Choice( **define( title=u"Status", __name__=u"finance_state", values= _finance_values ) ),
        schema.Choice( **define( title=u"Fulfillment", __name__=u"fulfillment_state", values= _fulfillment_values ) ),
        schema.TextLine( **define( title=u"User Id", __name__=u"user_id") ),
        )

    def setUpWidgets(self, ignore_request=False):
        self.adapters = {}
        self.widgets = form.setUpDataWidgets(
            self.form_fields, self.prefix, self.context, self.request,
            ignore_request=ignore_request
            )

    @form.action(_(u"Filter"), condition=form.haveInputWidgets)
    def handle_filter_action( self, action, data ):
        if data.get('creation_date'):
            data['creation_date'] = self.date_search_map.get( data['creation_date'] )
        self.filtered = True
        self.results = query.search( data )

    def update( self ):
        super( OrderSearchComponent, self).update()
        if not self.filtered:
            self.results = query.search( {'creation_date' : datetime.timedelta(7) } )
            self.request.set('form.creation_date', 'last 7 days')
        if self.results is None:
            self.results = []
            
    def render( self ):
        return self.template()

    def renderSearch( self ):
        return self.form_template()


class OrderAdminManagerBase( object ):

    viewlets_map = ()

    def sort (self, viewlets ):
        viewlets.sort( lambda x, y: cmp(x[1].order, y[1].order ) )
        return viewlets

    def get( self, name ):
        if name in self.viewlets_map:
            return self.viewlets_map[ name ]
        return None

    def update(self):
        """See zope.contentprovider.interfaces.IContentProvider"""
        self.__updated = True

        # Find all content providers for the region
        viewlets = component.getAdapters(
            (self.context, self.request, self.__parent__, self),
            IViewlet)

        viewlets = self.filter(viewlets)
        viewlets = self.sort(viewlets)
        self.viewlets_map = dict( viewlets )

        # Just use the viewlets from now on
        self.viewlets = [viewlet for name, viewlet in viewlets]

        # Update all viewlets
        [viewlet.update() for viewlet in self.viewlets]


OrdersAdminManager = viewlet_manager.ViewletManager(
    "OrdersAdmin",
    ipgp.IOrdersAdminManager,
    os.path.join( os.path.dirname( __file__ ),
                  "templates",
                  "viewlet-manager.pt"),
    bases=( OrderAdminManagerBase, )
    )


class ManageOrders( BrowserView ):
    # admin the collection of orders
    _download_content = None
    
    def __call__( self ):
        self.manager = OrdersAdminManager( self.context, self.request, self )
        self.manager.update()
        if self._download_content is not None:
            self.request.response.setHeader('Content-Type', self._download_content[0] )
            self.request.RESPONSE.setHeader('Content-Disposition','inline;filename=%s-%s.csv' % (self._download_content[2], time.strftime("%Y%m%d",time.localtime())))
            return self._download_content[1]
        return super( ManageOrders, self).__call__()

class AdminOrderRoot ( OrderRoot ):
    pass

class AdminOrderManagerBase( OrderAdminManagerBase ):
    
    items_by_state = None
    
    def itemsByStates( self, states ):
        # cache results, so we don't have to lookup adapters for each
        if self.items_by_state is None:
            # XXX todo.. orders become line item containers
            items = [(i.fulfillment_state, i) for i in self.__parent__.context.shopping_cart.values()]
            self.items_by_state = d = {}
            for k, v in items:
                d.setdefault(k,[]).append( v )
        results = []            
        for s in states:
            results.extend( self.items_by_state.get( s, () ) )
        return results

    def filter( self, viewlets ):
        res = []

        order_finance_state = self.__parent__.context.finance_state
        order_fulfillment_state = self.__parent__.context.fulfillment_state
        
        for vid, v in viewlets:
            if not v.show( order_finance_state = order_finance_state,
                           order_fulfillment_state = order_fulfillment_state ):
                continue
            res.append( (vid,v) )
        return res

AdminOrderManager = viewlet_manager.ViewletManager(
    "AdminOrder",
    ipgp.IAdminOrderManager,
    os.path.join( os.path.dirname( __file__ ),
                  "templates",
                  "viewlet-manager.pt"),
    bases=( AdminOrderManagerBase, )
    )


#################################
# Order Workflow Log Viewlet
class OrderWorkflowLogBase( object ):

    def iterRecords( self ):
        wf_log = interfaces.IOrderWorkflowLog( self.__parent__.context._object )
        return iter( wf_log )

    def render( self ):
        return self.__of__( self.__parent__ ).index()                 

    def show( self, **kw ):
        return True
    
OrderWorkflowLog = viewlet.SimpleViewletClass(
    template = os.path.join( os.path.dirname( __file__ ), 'templates/order-workflow-log.pt'),
    bases = (OrderWorkflowLogBase,),    
    attributes = { 'order' : 12 },
    name = "order-workflow-log"
    )

#################################
# workflow transition 2 formlib action bindings
class TransitionHandler( object ):

    def __init__( self, transition_id, wf_name=None):
        self.transition_id = transition_id
        self.wf_name = wf_name

    def __call__( self, form, action, data ):
        context = getattr( form.context, '_object', form.context )

        if self.wf_name:
            info = component.getAdapter( context, IWorkflowInfo, self.wf_name )
        else:
            info = IWorkflowInfo( context )
        info.fireTransition( self.transition_id )
        form.setupActions()

class CollectionTransitionHandler( object ):

    def __init__( self, transition_id ):
        self.transition_id = transition_id

    def __call__( self, form, action, data ):
        nodes = form.getSelected( action, data )
        for n in nodes:
            IWorkflowInfo( n ).fireTransition( self.transition_id )
            form.line_items.remove( n )

        # reset the form manager cache,
        # XXX we really need to broadcast a message to invalidate any states already stored
        form.__parent__.manager.items_by_state = None
    

def bindTransitions( form_instance, transitions, wf_name=None, collection=False, wf=None ):
    """ bind workflow transitions into formlib actions """

    assert not (collection and wf_name )
    if collection:
        success_factory = CollectionTransitionHandler
    elif wf_name:
        success_factory = lambda tid: TransitionHandler( tid, wf_name )
    else:
        success_factory = TransitionHandler

    actions = []
    for tid in transitions:
        d = {}
        if success_factory:
            d['success'] = success_factory( tid )
        if wf is not None:
            action = form.Action( _(unicode(wf.getTransitionById( tid ).title) ) )
        else:
            action = form.Action( tid, **d )
        action.form = form_instance
        action.__name__ = "%s.%s"%(form_instance.prefix, action.__name__)
        actions.append( action )
    return actions


class OrderFinanceComponent( core.ComponentViewlet ):
    """ workflow actions and details on order finance status
    """
    order = 2

    template = ZopeTwoPageTemplateFile('templates/order-finance.pt')
    prefix = "orderfinance"

    def render( self ):
        return self.__of__( self.__parent__ ).template()

    def show( self, **kw):
        return True

    def update( self ):
        self.setupActions()
        return super(OrderFinanceComponent, self).update()

    def setupActions( self ):
        wf = self.__parent__.context.finance_workflow
        transitions = wf.getManualTransitionIds()
        self.actions = bindTransitions( self, transitions, wf_name='order.finance') #, wf=wf.workflow() )

    def finance_status( self ):
        return self.__parent__.context.finance_state


class OrderFulfillmentComponent( core.ComponentViewlet ):
    """ workflow actions and details on order fulfillment status
    """

    order = 5

    template = ZopeTwoPageTemplateFile('templates/order-fulfillment.pt')
    prefix = "orderfulfillment"

    def render( self ):
        return self.__of__( self.__parent__ ).template()

    def show( self, **kw):
        return True

    def update( self ):
        self.setupActions()
        return super( OrderFulfillmentComponent, self).update()

    def setupActions( self ):
        wf = self.__parent__.context.fulfillment_workflow
        transitions = wf.getManualTransitionIds()
        self.actions = bindTransitions( self, transitions, wf_name='order.fulfillment') #, wf=wf.workflow() )

    def fulfillment_status( self ):
        return self.__parent__.context.fulfillment_state

class OrderSummaryComponent( viewlet.ViewletBase ):
    """ workflow actions and details on order summary
    """
    order = 1

    template = ZopeTwoPageTemplateFile('templates/order-summary.pt')
    prefix = "ordersummary"

    def render( self ):
        
        # pull out the real order object from the traversable wrapper
        self.order = self.context._object
        
        pm = getToolByName(self.context, "portal_membership")

        # this check really shouldn't be hardcoded here.. -kapilt
        user = pm.getAuthenticatedMember()
        if not user.has_permission('PloneGetPaid: Manage Orders',self.context):
            user_id = user.getId()
            if 'Anonymous' in user.getRoles() or user_id != self.getUserId():
                raise Unauthorized, "Arbitrary Order Access Only for Managers"
            
        utility = zapi.getUtility(ICountriesStates)
        self.vocab_countries = TitledVocabulary.fromTitles(utility.countries)
        self.vocab_states = TitledVocabulary.fromTitles(utility.states())
        return self.__of__( self.__parent__ ).template()

    def show( self, **kw):
        return True

    def getTotalPrice( self ):
        total_price = "%0.2f" % self.order.getTotalPrice()
        return total_price

    def getOrderId( self ):
        return self.order.order_id

    def getUserId( self ):
        return self.order.user_id

    def getCreationDate( self ):
        return self.order.creation_date

    def fulfillment_status( self ):
        return self.order.fulfillment_state

    def finance_status( self ):
        return self.order.finance_state
        
    def getContactInformation(self):
        contact = self.order.contact_information
        contact ={'name': contact.name,
                  'email': contact.email,
                  'phone': contact.phone_number}
        return contact
    
    def getShippingService(self):
        if not hasattr(self.order,"shipping_service"):
            return "N/A"
        infos = self.order.shipping_service
        if infos:
            return infos

    def getShippingMethod(self):
        # check the traversable wrrapper
        if not interfaces.IShippableOrder.providedBy( self.order ):
            return _(u"N/A")
        
        service = component.queryUtility( interfaces.IShippingRateService,
                                          self.order.shipping_service )
        
        # play nice if the a shipping method is removed from the store
        if not service: 
            return _(u"N/A")
        
        return service.getMethodName( self.order.shipping_method )
    
    def getShipmentWeight(self):
        """
        Lets return the weight in lbs for the moment
        """
        # check the traversable wrrapper
        if not interfaces.IShippableOrder.providedBy( self.order ):
            return _(u"N/A")

        totalShipmentWeight = 0
        for eachProduct in self.order.shopping_cart.values():
            if interfaces.IShippableLineItem.providedBy( eachProduct ):
                weightValue = eachProduct.weight * eachProduct.quantity
                totalShipmentWeight += weightValue
        return totalShipmentWeight
       
    def getShimpentTrackNumbers(self):
        """
        Returns a list of tracking numbers for the shipment, if not available
        it will return a one element list with the N/A string, just to maintain
        consistency on the value being iterable
        """
        if not interfaces.IShippableOrder.providedBy( self.order ):
            return None
        shipments = []
        for shipment in self.order.shipments.values():
            service = component.queryUtility( interfaces.IShippingRateService,
                                          self.order.shipping_service )
        
            if service: 
                tracking_url = service.getTrackingUrl( shipment.tracking_code ) 
                displayable_service = """<a href="%s">%s</a>""" % (tracking_url,shipment.tracking_code)
            else:
                displayable_service = "%s" % shipment.tracking_code

            shipments.append(displayable_service)

        if len(shipments) == 0:
            shipments = None
        return shipments

    def getShippingAddress(self):
        infos = self.order.shipping_address
        if infos.ship_same_billing:
            return
        for fieldname in schema.getFieldNamesInOrder(infos.schema):
            yield getattr(infos,fieldname)
        
    def getBillingAddress(self):
        infos = self.order.billing_address
        for fieldname in schema.getFieldNamesInOrder(infos.schema):
            yield getattr(infos,fieldname)

###############################################
# context vocabularies for workflow transitions

def AvailableOrderFinanceTransitions( context ):
    info = component.getAdapter( (context,), IWorkflowInfo, "order.finance")
    return vocabulary.SimpleVocabulary.fromValues(
        info.getManualTransitionIds()        
        )

interface.directlyProvides( AvailableOrderFinanceTransitions, IContextSourceBinder )

def AvailableOrderFulfillmentTransitions( context ):
    info = component.getAdapter( (context,), IWorkflowInfo, "order.fulfillment")
    return vocabulary.SimpleVocabulary.fromValues(
        info.getManualTransitionIds()
        )

interface.directlyProvides( AvailableOrderFulfillmentTransitions, IContextSourceBinder )


def AvailableGenericTransitions( context ):
    return vocabulary.SimpleVocabulary.fromValues( 
        IWorkflowInfo( context ).getManualTransitionIds()
        )

interface.directlyProvides( AvailableGenericTransitions, IContextSourceBinder )

def renderItemId( item, formatter ):
    return item.product_code

def renderItemName( item, formatter ):
    content = item.resolve()
    if not content:
        return item.name
    content_url = content.absolute_url()
    return '<a href="%s">%s</a>'%( content_url, item.name )

def renderItemCost( item, formatter ):
    return "%0.2f" % ( item.cost )

def renderItemPrice( item, formatter ):
    return "%0.2f"%( item.quantity * item.cost )

## class FieldEditColumn( column.FieldEditColumn ):
##     def renderCell(self, item, formatter):
##         id = self.makeId(item)
##         request = formatter.request
##         field = self.field
##         if self.bind:
##             field = field.bind(item)
##         widget = component.getMultiAdapter((field, request), IInputWidget)
##         widget.setPrefix(self.prefix + '.' + id)
##         if self.widget_extra is not None:
##             widget.extra = self.widget_extra
##         if self.widget_class is not None:
##             widget.cssClass = self.widget_class
##         ignoreStickyValues = getattr(formatter, 'ignoreStickyValues', False)
##         if ignoreStickyValues or not widget.hasInput():
##             widget.setRenderedValue(self.get(item))
##         return widget()
    

## Experiment with inline table edits as workflow triggers
##  part of order contents component class def
##    _of = WorkflowColumn( "fulfillment" )
##    _of.field = schema.Choice( **define(title=u"Status", source=AvailableGenericTransitions) )
##
##         column.FieldEditColumn( title="Status",
##                                 prefix="items",
##                                 idgetter = lambda ob: ob.item_id,
##                                 getter=_of.get,
##                                 setter=_of.set,
##                                 field=_of.field,
##                                 bind=True),    

## class WorkflowColumn( object ):

##     def __init__( self, name):
##         self.name = name

##     def get( self, item ):
##         return getattr( item, "%s_state"%self.name ) or "N/A"

##     def set( self, item, v ):
##         info = getattr( item, "%_workflow"%self.name )
##         info.fireTransition( info )

class OrderContentsComponent( core.ComponentViewlet ):
    """ an item listing used to group items by workflow state and present
    relevant workflow actions """

    interface.implements( )
    
    template = ZopeTwoPageTemplateFile('templates/order-item-listing.pt')
    
    columns = [
        column.SelectionColumn( lambda item: item.item_id, name="selection"),
        column.GetterColumn( title=_(u"Quantity"), getter=AttrColumn("quantity" ) ),
        column.GetterColumn( title=_(u"Item Id"), getter=renderItemId ),
        column.GetterColumn( title=_(u"Name"), getter=renderItemName ),
        column.GetterColumn( title=_(u"Price"), getter=renderItemCost ),        
        column.GetterColumn( title=_(u"Total"), getter=renderItemPrice ),        
        column.GetterColumn( title=_(u"Status"), getter=AttrColumn("fulfillment_state" ) ),
        ]
    
    selection_column = columns[0]
    order = 10 # position in the viewlet stack
    states = None # tuple of item fulfillment states that we use to get items we display
    show_finance_states = () # which order finance states we display in
    show_fulfillment_states = () # which order fulfillment states we display in

    collection_name = _(u"Contents")
    
    def render( self ):
        return self.__of__( self.__parent__ ).template() 

    def show( self, **kw):
        if self.show_fulfillment_states and kw['order_fulfillment_state']:
            return kw['order_fulfillment_state'] in self.show_fulfillment_states
        if self.show_finance_states and kw['order_finance_state']:
            return kw['order_finance_state'] in self.show_finance_states
        if self.states:
            self.line_items = self.managerItemsByStates( self.states )
            if not self.line_items:
                return False
        return True
    
    def update( self ):
        # we need a better way of binding multiple states and associated transitions, such
        # that we can chain them together.
        info = IWorkflowInfo( self.line_items[0] )
        transitions = info.getManualTransitionIds()
        self.actions = bindTransitions( self, transitions, collection=True )
        
        return super( OrderContentsComponent, self).update()

    def getSelected( self, action, data ):
        selected = self.selection_column.getSelected( self.line_items, self.request)
        return selected        
        
    def listing( self ):
        columns = self.columns
        formatter = table.StandaloneFullFormatter( self.context,
                                                   self.request,
                                                   self.line_items,
                                                   prefix=self.prefix,
                                                   visible_column_names = [c.name for c in columns],
                                                   #sort_on = ( ('name', False)
                                                   columns = columns )
        formatter.cssClasses['table'] = 'listing'
        return formatter()

    @staticmethod
    def makeGrouping( *states, **kw ):
        kw.update(  { 'states' : states } )
        return type(
            "Item%sContents"%states[0],
            (OrderContentsComponent,),
            kw
            )



# Item Listing Viewlets By State
NewItems = OrderContentsComponent.makeGrouping(
    None,
    interfaces.workflow_states.item.NEW,
    interfaces.workflow_states.item.PROCESSING,
    prefix = "newitems"
    )

DeliveredItems = OrderContentsComponent.makeGrouping(
    interfaces.workflow_states.item.SHIPPED,
    prefix = "delivereditems"
    )

RefundedItems = OrderContentsComponent.makeGrouping(
    interfaces.workflow_states.item.REFUNDED,
    interfaces.workflow_states.item.REFUNDING,
    prefix = "refundeditems"
    )

CancelledItems = OrderContentsComponent.makeGrouping(
    interfaces.workflow_states.item.CANCELLED,
    prefix = "cancelleditems"
    )

VirtualItems = OrderContentsComponent.makeGrouping(
    interfaces.workflow_states.item.DELIVER_VIRTUAL,
    prefix = "virtualitems"
    )


# for use when we're still reviewing workflow state
class AllItems( OrderContentsComponent ):

    actions = form.Actions()

    columns = list( OrderContentsComponent.columns )
    columns.remove( OrderContentsComponent.selection_column )

    def update( self ):
        self.line_items = self.__parent__.context.shopping_cart.values()
        return super( OrderContentsComponent, self).update()
        
class AdminOrder( BrowserView ):
    """ an order view
    """
    
    def __init__( self, context, request ):
        self.context = context
        self.request = request
    
    def __call__( self ):
        self.manager = AdminOrderManager( self.context, self.request, self )
        self.manager.update()
        return super( AdminOrder, self).__call__()
