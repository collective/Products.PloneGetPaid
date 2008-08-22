"""

cart-review checkout

$Id$
"""


import decimal,operator
import cgi
from cPickle import loads, dumps
from datetime import timedelta

from zope.event import notify
from zope.formlib import form
from zope import schema, interface
from zope.app.event.objectevent import ObjectCreatedEvent
from zope.app.renderer.plaintext import PlainTextToHTMLRenderer

from zope import component

from zope.schema.interfaces import IField
from zope.app.apidoc import interface as apidocInterface

from zc.table import column
from getpaid.wizard import Wizard, ListViewController, interfaces as wizard_interfaces
from getpaid.core import interfaces, options, payment, cart
from getpaid.core.order import Order

import Acquisition
from AccessControl import getSecurityManager
from ZTUtils import make_query as mq
from ZTUtils.Zope import complex_marshal

from Products.Five.formlib import formbase
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile,ViewPageTemplateFile
from Products.CMFCore.utils import getToolByName

from Products.PloneGetPaid.interfaces import IGetPaidManagementOptions, IAddressBookUtility
from Products.PloneGetPaid.i18n import _


from base import BaseFormView
import cart as cart_core
from widgets import CountrySelectionWidget, StateSelectionWidget, CCExpirationDateWidget


def null_condition( *args ):
    return ()

def named( klass ):
    return "%s.%s"%(klass.__module__, klass.__name__)
    
def make_hidden_input(*args, **kwargs):
    '''Construct a set of hidden input elements, with marshalling markup.

    If there are positional arguments, they must be dictionaries.
    They are combined with the dictionary of keyword arguments to form
    a dictionary of query names and values.

    Query names (the keys) must be strings.  Values may be strings,
    integers, floats, or DateTimes, and they may also be lists or
    namespaces containing these types.  All arguments are marshalled with
    complex_marshal().
    '''

    d = {}
    for arg in args:
        d.update(arg)
    d.update(kwargs)

    hq = lambda x:cgi.escape(x, quote=True)
    qlist = complex_marshal(d.items())
    for i in range(len(qlist)):
        k, m, v = qlist[i]
        try:
            # try to convert to unicode first, because str() of the unicode string may fail
            v = unicode(v)
        except UnicodeDecodeError:
            v = str(v)
        qlist[i] = ('<input type="hidden" name="%s%s" value="%s">'
                    % (hq(k), m, hq(v)))

    return '\n'.join(qlist)
    
class BaseCheckoutForm( BaseFormView ):

    template = None # must be overridden

    sections = ()
    
    hidden_form_vars = None
    adapters = None
    next_step_name = None # next step in wizard
    _next_url = None # redirect url
    wizard = None  # wizard
    
    interface.implements( wizard_interfaces.IWizardFormStep )
    
    def __init__( self, context, request ):
        self.context = context
        self.request = request
        self.setupLocale( request )
        self.setupEnvironment( request )

    @property
    def form_fields(self):
        fields = getattr(self,'__form_fields',None)
        if fields:
            return fields
        args = []
        formSchemas = component.getUtility(interfaces.IFormSchemas)
        for section in self.sections:
            args.append(formSchemas.getInterface(section))
        fields = form.Fields(*args)
        customise_widgets = getattr(self,'customise_widgets',None)
        if customise_widgets is not None:
            customise_widgets(fields)
        self.__form_fields = fields
        return fields
    
    def hidden_inputs( self ):
        if not self.hidden_form_vars: return ''
        return make_hidden_input( **self.hidden_form_vars )
        
    hidden_inputs = property( hidden_inputs )

    def setExportedVariables( self, mapping ):
        assert isinstance( mapping, dict )
        self.hidden_form_vars = mapping
        
    def getSchemaAdapters( self ):
        adapters = {}        
        user = getSecurityManager().getUser()
        formSchemas = component.getUtility(interfaces.IFormSchemas)
        for section in self.sections:
            interface = formSchemas.getInterface(section)
            adapter = component.queryAdapter(user,interface)
            if adapter is None:
                adapter = formSchemas.getBagClass(section)()
            adapters[interface]=adapter
        return adapters
    
    def invariantErrors( self ):
        errors = []
        for error in self.errors:
            if isinstance( error, interface.Invalid ):
                errors.append( error )
        return errors
    
    def getWidgetsBySectionName(self,name):
        formSchemas = component.getUtility(interfaces.IFormSchemas)
        return self._getWidgetsByInterface(formSchemas.getInterface(name))
        
    def getWidgetsByIName( self, name ):
        for iface in self.wizard.data_manager.adapters.keys():
            if name == named( iface ):
                return self._getWidgetsByInterface( iface )

    def _getWidgetsByInterface( self, interface ):
        return [w for w in self.widgets if w.context.interface == interface ]
        
    def render( self ):
        if self._next_url:
            self.request.RESPONSE.redirect( self._next_url )
            return ""
        return super( BaseCheckoutForm, self).render()

    def createTransientOrder( self ):
        order = Order()

        shopping_cart = component.getUtility( interfaces.IShoppingCartUtility ).get( self.context )
        formSchemas = component.getUtility(interfaces.IFormSchemas)

        # shopping cart is attached to the session, but we want to switch the storage to the persistent
        # zodb, we pickle to get a clean copy to store.
        adapters = self.wizard.data_manager.adapters
        order.shopping_cart = loads( dumps( shopping_cart ) )

        for section in ('contact_information','billing_address','shipping_address'):
            interface = formSchemas.getInterface(section)
            bag = formSchemas.getBagClass(section).frominstance(adapters[interface])
            setattr(order,section,bag)

        order.order_id = self.wizard.data_manager.get('order_id')
        order.user_id = getSecurityManager().getUser().getId()

        return order
        
##############################
# Some Property Bags - transient adapters

class BillingInfo( options.PropertyBag ):
    title = "Billing Information"

    def __init__(self, context):
        # need a context to be able to get the current available credit
        # cards. purge state afterwards
        self.context = context

    def __getstate__( self ):
        # don't store persistently
        raise RuntimeError("Storage Not Allowed")

BillingInfo = BillingInfo.makeclass( interfaces.IUserPaymentInformation )

class ImmutableBag( object ):
    
    def initfrom( self, other, iface ):
        for field_name, field in schema.getFieldsInOrder( iface ):
            setattr( self, field_name, field.get( other ) )
        return self

class CheckoutWizard( Wizard ):
    """
    a bidirectional checkout wizard, using getpaid.wizard. See the CheckoutController
    class if you want to customize the sequence of steps. The Wizard itself is mostly
    a coordination gatekeeper, that enforces checkout constraints transparently
    to any individual step. 
        
    steps should export all form variables not from themselves as hidden inputs, to 
    allow for prepopulated forms from previous inputs on that step. 
    
    steps are specified in order and by view name. a step view must minimally have a
    an update/render cycle ala content_provider or formlib views.
    
    forms are processed as normal, we depend on a _next_url attribute being present
    and set to the either a url or one of the marker values for next or previous steps.
    
    the form must specify handlers for next / previous / finished steps.
    
    steps can't override call methods, as such logic won't be processed, since we call
    update / render methods directly.
    """
    
    def checkShoppingCart(self):
        cart = component.getUtility(interfaces.IShoppingCartUtility).get( self.context )
        if cart is None or not len(cart):
            self.request.response.redirect('@@empty-cart')
            return False
        return True
    
    def checkAuthenticated( self ):
        membership = getToolByName( self.context, 'portal_membership')
        if membership.isAnonymousUser():
            portal = getToolByName( self.context, 'portal_url').getPortalObject()
            if IGetPaidManagementOptions( portal ).allow_anonymous_checkout:
                return True
            self.request.response.redirect('login_form?came_from=@@getpaid-checkout-wizard')
            return False
        return True
    
    def checkOrderId( self ):
        """ get the current order id out of the request,
            and verify it"""
        
        order_id = self.request.get('order_id', None)
        order_manager = component.getUtility( interfaces.IOrderManager )
        
        # if invalid order id, or no order id present 
        # set to first step and give new order id
        if ( order_id is None and not self.controller.hasPreviousStep() ) or \
            not order_manager.isValid( order_id ):
            self.controller.reset()
            self.request['order_id'] = order_id = order_manager.newOrderId()
            self.data_manager['order_id'] = order_id
            return True
            
        # if the order id is already in use check to see if its the same user that
        # owns it    
        if order_id in order_manager:
            # check for already existing order belonging to the same user from the
            # last day, and redirect them to it, else restart them in the wizard
            # all anonymous get restarted.
            user_id = getSecurityManager().getUser().getId()
            if user_id != 'Anonymous':
                results = order_manager.query( user_id = user_id,
                                               order_id = order_id,
                                               creation_date = timedelta(1) )
                if len(results) == 1:
                    order = list( results )[0]
                    base_url = self.context.absolute_url()
                    url = base_url + '/@@getpaid-thank-you?order_id=%s' %(order_id)
                        
                    if not 'http://' in url:
                        url = url.replace("https://", "http://")
                    
                    self.request.response.redirect( url )
                    self.data_manager.reset()
                    return False
                    
            # redirect and reset form variables
            self.data_manager.reset()
            self.request.response.redirect('@@getpaid-checkout-wizard')

            return False
            
        self.data_manager['order_id'] = order_id
        return True
    
    def checkUseSSL(self):
        portal = getToolByName(self.context, 'portal_url').getPortalObject()
        if IGetPaidManagementOptions(portal).use_ssl_for_checkout:
            # we need to become https if we are not already
            # unless we are cancelling or on the thank you page
            url = self.request.getURL()
            if not 'https://' in url:
                url = url.replace("http://", "https://")
                self.request.response.redirect('%s?%s' % (url, mq(self.request.form)))
        return True
    
    def __call__( self ):
        # if we don't have a shopping cart redirect browser to empty cart view
        if not self.checkShoppingCart():
            return
        
        # if we're not authenticated redirect to login page with camefrom
        # which points back to the checkout wizard, bypassed by admin 
        # option to allow anonymous checkout
        if not self.checkAuthenticated():
            return
        
        # check to make sure we have a valid unused order id associated throughout
        # the checkout process. also stores the order id in the data mangaer for
        # use by other components.
        if not self.checkOrderId():
            return
            
        if not self.checkUseSSL():
            return
        
        return super( CheckoutWizard, self).__call__()
    

class CheckoutController( ListViewController ):
    
    conditions = {'checkout-select-shipping' : 'checkShippableCart'}
    steps = ['checkout-address-info', 'checkout-select-shipping', 'checkout-review-pay']    

    def getStep( self, step_name ):
        step = component.getMultiAdapter( 
                    ( self.wizard.context, self.wizard.request ),
                    name=step_name
                    )
        return step.__of__( Acquisition.aq_inner( self.wizard.context ) )
        
    def checkShippableCart( self ):
        cart_utility = component.getUtility( interfaces.IShoppingCartUtility )
        cart = cart_utility.get( self.wizard.context )
        return bool( filter(  interfaces.IShippableLineItem.providedBy, cart.values() ) )

    def checkStep( self, step_name ):
        condition_method = self.conditions.get( step_name )
        if not condition_method:
            return step_name
        condition = getattr( self, condition_method )
        if condition():
            return True
        return False
        
    # overridden icontroller methods        
    def getNextStepName( self, step_name ):
        step_name = super( CheckoutController, self).getNextStepName( step_name )
        if self.checkStep( step_name ):
            return step_name
        return self.getNextStepName( step_name )    
    
    def getTraversedFormSteps( self ):
        steps = super( CheckoutController, self ).getTraversedFormSteps()
        steps = filter( self.checkStep, steps )
        return steps
        
    def getStep( self, step_name ):
        step = component.getMultiAdapter(
                    ( self.wizard.context, self.wizard.request ),
                    name=step_name
                    )
        return step.__of__( Acquisition.aq_inner( self.wizard.context ) )
            

class CheckoutAddress( BaseCheckoutForm ):
    """
    browser view for collecting credit card information and submitting it to
    a processor.
    """
    
    sections = ('billing_address','shipping_address','contact_information')
    
    def customise_widgets(self,fields):
        fields['ship_country'].custom_widget = CountrySelectionWidget
        fields['bill_country'].custom_widget = CountrySelectionWidget
        fields['ship_state'].custom_widget = StateSelectionWidget
        fields['bill_state'].custom_widget = StateSelectionWidget
    
    template = ZopeTwoPageTemplateFile("templates/checkout-address.pt")
    
    def update( self ):
        formbase.processInputs( self.request )
        self.adapters = self.wizard.data_manager.adapters
        super( CheckoutAddress, self).update()
    
    def hasAddressBookEntries(self):
        """
        Do we have any entry?
        """
        book = component.getUtility(IAddressBookUtility).get(getSecurityManager().getUser().getId())
        return len(book.keys())

    def save_address(self, data):
        """
        store the address in the addressbook of the user
        """
        book_key = 'addressbook_entry_name'
        entry = self.wizard.data_manager.get( book_key )
        del self.wizard.data_manager[ book_key ]
        # if the user fill the name of the entry mean that we have to save the address
        if not entry:
            return
        elif isinstance( entry, list):
            entry = filter( None, entry)
            if not entry:
                return
            entry = entry[-1]
        
        uid = getSecurityManager().getUser().getId()
        if uid == 'Anonymous':
            return
                        
        book  = component.getUtility(IAddressBookUtility).get( uid )
        if entry in book:
            return
            
        # here we get the shipping address
        formSchemas = component.getUtility(interfaces.IFormSchemas)
        ship_address_info = formSchemas.getBagClass('shipping_address')()
        if data['ship_same_billing']:
            for field in data.keys():
                if field.startswith('bill_'):
                    ship_address_info.__setattr__(field.replace('bill_','ship_'), data[field])
        else:
            for field in data.keys():
                if field.startswith('ship_'):
                    ship_address_info.__setattr__(field, data[field])
        book[entry] = ship_address_info
        self.context.plone_utils.addPortalMessage(_(u'A new address has been saved'))
    
    @form.action(_(u"Cancel"), name="cancel", validator=null_condition)
    def handle_cancel( self, action, data):
        url = self.context.portal_url.getPortalObject().absolute_url()
        url = url.replace("https://", "http://")
        return self.request.response.redirect(url)
        
    @form.action(_(u"Continue"), name="continue")
    def handle_continue( self, action, data ):
        self.save_address(data)
        self.next_step_name = wizard_interfaces.WIZARD_NEXT_STEP

def copy_field( field ):
    # copies a field dropping custom widgets
    return field.__class__( 
        field = field.field,
        name = field.__name__,
        prefix = field.prefix,
        for_display = field.for_input,
        for_input = field.for_input,
        get_rendered = field.get_rendered,
        render_context = field.render_context
        )
        
def sanitize_custom_widgets( fields ):
    # we need to drop custom edit widgets so we get default display widgets
    # this method makes inplace copies of fields with custom widgets without
    # the custom widget
    custom_fields = []
    for field in fields:
        if field.custom_widget is not None:
            custom_fields.append( field )
    if not custom_fields:
        return fields
    
    for field in custom_fields:
        field_copy = copy_field( field )
        idx = fields.__FormFields_seq__.index( field )
        fields.__FormFields_seq__.pop(idx)
        fields.__FormFields_seq__.insert( idx, field_copy )
        fields.__FormFields_byname__[ field.__name__] = field
        
    return fields
    
class CheckoutReviewAndPay( BaseCheckoutForm ):
    
    sections = ('payment',)

    def customise_widgets(self,fields):
        fields['cc_expiration'].custom_widget = CCExpirationDateWidget

    template = ZopeTwoPageTemplateFile("templates/checkout-review-pay.pt")
    
    columns = [
        column.GetterColumn( title=_(u"Quantity"), getter=cart_core.LineItemColumn("quantity") ),
        column.GetterColumn( title=_(u"Name"), getter=cart_core.lineItemURL ),
        column.GetterColumn( title=_(u"Price"), getter=cart_core.lineItemPrice ),
        column.GetterColumn( title=_(u"Total"), getter=cart_core.lineItemTotal ),
       ]

    def getSchemaAdapters( self ):
        formSchemas = component.getUtility(interfaces.IFormSchemas)
        adapters = {}
        adapters[formSchemas.getInterface('payment')] = formSchemas.getBagClass('payment')(self.context)
        return adapters
        
    def setUpWidgets( self, ignore_request=False ):
        self.adapters = self.adapters is not None and self.adapters or {}
        
        # grab all the adapters and fields from the entire wizard form sequence (till the current step)
        adapters = self.wizard.data_manager.adapters
        fields   = self.wizard.data_manager.fields
        
        formSchemas = component.getUtility(interfaces.IFormSchemas)
        # edit widgets for payment info
        self.widgets = form.setUpEditWidgets(
            self.form_fields.select( *schema.getFieldNames(formSchemas.getInterface('payment'))),
            self.prefix, self.context, self.request,
            adapters=adapters, ignore_request=ignore_request
            )
        
        # display widgets for bill/ship address
        bill_ship_fields = []
        for i in (formSchemas.getInterface('billing_address'),
                  formSchemas.getInterface('shipping_address')):
            bill_ship_fields.append(fields.select(*schema.getFieldNamesInOrder(i)))
        # make copies of custom widgets.. (typically for edit, we want display)
        bill_ship_fields = sanitize_custom_widgets(
            reduce(operator.__add__,bill_ship_fields)
            )
        
        self.widgets += form.setUpEditWidgets(
            bill_ship_fields,  self.prefix, self.context, self.request,
            adapters=adapters, for_display=True, ignore_request=ignore_request
            )
    
    def renderCart( self ):
        cart = component.getUtility( interfaces.IShoppingCartUtility ).get( self.context )
        if not cart:
            return _(u"N/A")
        
        # create an order so that tax/shipping utilities have full order information
        # to determine costs (ie. billing/shipping address ).
        order = self.createTransientOrder()
        formatter = OrderFormatter( order,
                                    self.request,
                                    cart.values(),
                                    prefix=self.prefix,
                                    visible_column_names = [c.name for c in self.columns],
                                    #sort_on = ( ('name', False)
                                    columns = self.columns )
        
        formatter.cssClasses['table'] = 'listing'
        return formatter()
        
    @form.action(_(u"Cancel"), name="cancel", validator=null_condition )
    def handle_cancel( self, action, data):
        url = self.context.portal_url.getPortalObject().absolute_url()
        url = url.replace("https://", "http://")
        return self.request.response.redirect(url)
        
    @form.action(_(u"Back"), name="back", validator=null_condition )
    def handle_back( self, action, data):
        self.next_step_name = wizard_interfaces.WIZARD_PREVIOUS_STEP                
        
    @form.action(_(u"Make Payment"), name="make-payment", condition=form.haveInputWidgets )
    def makePayment( self, action, data ):
        """ create an order, and submit to the processor
        """
        manage_options = IGetPaidManagementOptions( self.context )
        processor_name = manage_options.payment_processor
        
        if not processor_name:
            raise RuntimeError( "No Payment Processor Specified" )
        
        processor = component.getAdapter( self.context,
                                          interfaces.IPaymentProcessor,
                                          processor_name )
        
        adapters = self.wizard.data_manager.adapters
        
        order = self.createOrder()
        order.processor_id = processor_name
        order.finance_workflow.fireTransition( "create" )
        
        # extract data to our adapters
        
        formSchemas = component.getUtility(interfaces.IFormSchemas)
        result = processor.authorize( order, adapters[formSchemas.getInterface('payment')] )
        if result is interfaces.keys.results_async:
            # shouldn't ever happen, on async processors we're already directed to the third party
            # site on the final checkout step, all interaction with an async processor are based on processor
            # adapter specific callback views.
            pass
        elif result is interfaces.keys.results_success:
            order_manager = component.getUtility( interfaces.IOrderManager )
            order_manager.store( order )
            order.finance_workflow.fireTransition("authorize")
            # kill the cart after we create the order
            component.getUtility( interfaces.IShoppingCartUtility ).destroy( self.context )
        else:
            order.finance_workflow.fireTransition('reviewing-declined')
            self.status = result
            self.form_reset = False
        
        self._next_url = self.getNextURL( order )
        
    def createOrder( self ):
        order_manager = component.getUtility( interfaces.IOrderManager )

        order = self.createTransientOrder()

        shipping_code = self.wizard.data_manager.get('shipping_method_code')
        if shipping_code is not None:
            # get the names of the selected shipping service
            shipping_service, shipping_method = decodeShipping( shipping_code )
            
            # get the cost
            shipping_method_obj = getShippingMethod( order, shipping_code )
            interface.directlyProvides( order, interfaces.IShippableOrder )
            
            order.shipping_service = shipping_service
            order.shipping_method = shipping_method
            order.shipping_cost = shipping_method_obj.cost
            
        notify( ObjectCreatedEvent( order ) )
        
        return order
    
    def getNextURL(self, order):
        state = order.finance_state
        f_states = interfaces.workflow_states.order.finance
        base_url = self.context.absolute_url()
        if not 'http://' in base_url:
            base_url = base_url.replace("https://", "http://")

        if state in (f_states.CANCELLED,
                     f_states.CANCELLED_BY_PROCESSOR,
                     f_states.PAYMENT_DECLINED):
            return base_url + '/@@getpaid-cancelled-declined'
        
        if state in (f_states.CHARGEABLE,
                     f_states.CHARGING,
                     f_states.REVIEWING,
                     f_states.CHARGED):
            return base_url + '/@@getpaid-thank-you?order_id=%s&finance_state=%s' %(order.order_id, state)
        
class ShippingRate( options.PropertyBag ):
    title = "Shipping Rate"

ShippingRate.initclass( interfaces.IShippingMethodRate )

class CheckoutSelectShipping( BaseCheckoutForm ):
    """
    browser view for selecting a shipping option and setting it as the shipping total for the order.
    """

    template = ZopeTwoPageTemplateFile("templates/checkout-shipping-method.pt")
    ship_service_names = ()

    def setupShippingOptions( self ):
        """
        Queries shipping utilities and adapters to get the available shipping methods
        and returns a list of them for the template to display and the user to choose among.
        
        """
        ship_service_names = IGetPaidManagementOptions( self.context ).shipping_services
        
        if not ship_service_names:
            self.status =  "Misconfigured Store - No Shipping Method Activated"
            return
            
        order = self.createTransientOrder()
        
        service_options = {}
        for service_name in ship_service_names:
            service = component.getUtility( interfaces.IShippingRateService, name=service_name )
            rates = service.getRates( order )
            if rates.error is not None:
                self.status = '%(name)s Error: %(error)s.' % {'name':service_name, 'error':rates.error}
            service_options[ service_name ] = rates.shipments
            
        self.ship_service_names = ship_service_names
        self.service_options = service_options
        
    def setShippingMethods( self ):
        """
        Set the shipping methods chosen by the user
        """
        
    def update( self ):
        self.setupShippingOptions()
        super( CheckoutSelectShipping, self).update()


    @form.action(_(u"Cancel"), name="cancel", validator=null_condition)
    def handle_cancel( self, action, data):
        url = self.context.portal_url.getPortalObject().absolute_url()
        url = url.replace("https://", "http://")
        return self.request.response.redirect(url)

    @form.action(_(u"Back"), name="back")
    def handle_back( self, action, data, validator=null_condition):
        self.next_step_name = wizard_interfaces.WIZARD_PREVIOUS_STEP

    @form.action(_(u"Continue"), name="continue")
    def handle_continue( self, action, data ):
        self.next_step_name = wizard_interfaces.WIZARD_NEXT_STEP

class OrderFormatter( cart_core.CartFormatter ):

    def getTotals( self ):
        return OrderTotals( self.context, self.request)
        
class OrderTotals( cart.CartItemTotals ):

    interface.implements( interfaces.ILineContainerTotals )
    
    def __init__( self, context, request ):
        self.context = context
        self.shopping_cart = context.shopping_cart
        self.request = request

    def getShippingCost( self ):
        service_code = self.request.get('shipping_method_code')
        method = getShippingMethod( self.context, service_code )        
        if method is None:
            return 0
        return method.cost

def getShippingMethod( order, service_code ):
    """ decode a shipping code, and return the shipping method to be used or None """
    if not service_code:
        return None
    if isinstance( service_code, list):
        service_code = service_code[-1]    
    service_name, service_method = service_code.split('.', 1)
    service = component.getUtility( interfaces.IShippingRateService, service_name )
    methods = service.getRates( order )
    for m in methods.shipments:
        if m.service_code == service_method:
            return m
                
def decodeShipping( service_code ):
    if isinstance( service_code, list):
        service_code = service_code[-1]
    service_name, service_method = service_code.split('.', 1)
    return service_name, service_method
      
class StorePropertyView(BrowserView):
    
    def _getProperty(self, name ):
        portal = getToolByName(self.context, 'portal_url').getPortalObject()
        settings = IGetPaidManagementOptions(portal)
        value = getattr( settings, name, '')
        if value:
            renderer = PlainTextToHTMLRenderer(value, self.request)
            value = renderer.render().strip()
        return value

class DisclaimerView( StorePropertyView ):
    """ Shows the disclaimer text from the getpaid settings.
    """
    @property
    def disclaimer( self ):
        return self._getProperty( 'disclaimer' )
    
class PrivacyPolicyView( StorePropertyView ):
    """ Shows the privacy policy text from the getpaid settings.
    """
    @property
    def privacy_policy(self):
        return self._getProperty('privacy_policy')

class AddressBookView(BrowserView):
    
    __call__ = ZopeTwoPageTemplateFile("templates/addressbook-listing.pt")
        
    def getEntryNames(self):
        """
        get a list of entry names
        """
        uid = getSecurityManager().getUser().getId()
        if uid == 'Anonymous':
            return ()
        book = component.getUtility(IAddressBookUtility).get( uid )
        entry_names = list( book.keys() )
        entry_names.sort()
        entry_dict = {}
        for entry_name in entry_names:
            second_line = ""
            if book[entry_name].ship_second_line:
                second_line = book[entry_name].ship_second_line + "<br />"
            entry_dict[entry_name] = """%s<br />%s%s<br />""" % (book[entry_name].ship_first_line,second_line, book[entry_name].ship_city + " " + book[entry_name].ship_postal_code + " " + book[entry_name].ship_state )

        return entry_dict


    def getEntryScripts(self):
        """
        Returns javascript function that fill the fields with the data
        """
        addressBookUsr = component.getUtility(IAddressBookUtility).get(getSecurityManager().getUser().getId())
         
        
        jstemplate = \
        """ 
         function doWaitUntilStatesAreLoaded(theStateValue){
           window.opener.parent.document.getElementById('form.ship_state').value = theStateValue
        window.close();
        }
        
        function assign_variables(contact_name,contact_link){
        contact_link.innerHTML="Please wait, retrieving data..."
        %s
        }
        """
        field_assign_template = \
        """
        window.opener.parent.document.getElementById('form.%s').value = '%s' ;
        """
        javaScript = ''
        field_assignations = ''
        for entry in self.getEntryNames().keys():
            
            field_assignations += "if (contact_name == '%s') {\n" % entry
            for name in apidocInterface.getElements(interfaces.IShippingAddress, type=IField).keys():
                try:
                    if name == "ship_state":
                        field_assignations += """\n setTimeout("doWaitUntilStatesAreLoaded('%s')",2000);""" %  getattr(addressBookUsr[entry],name) or ''
                    elif name == "ship_country":
                        field_assignations += field_assign_template % (name,getattr(addressBookUsr[entry],name) or '')
                        field_assignations += "window.opener.parent.document.getElementById('form.%s').onchange();\n"%name
                    else:
                        field_assignations += field_assign_template % (name,getattr(addressBookUsr[entry],name) or '')
                    
                except KeyError:
                    pass
            field_assignations += "}"
        javaScript += jstemplate % field_assignations
            
        return javaScript
