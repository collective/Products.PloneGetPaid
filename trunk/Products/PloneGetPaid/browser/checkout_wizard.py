"""
collective.z3cform.wizard based checkout wizard
"""

__version__ = "$Revision$"
# $Id$
# $URL$

import types
import hashlib
import cPickle
import ZTUtils

from zope import component, exceptions, interface, schema, viewlet

from zope.schema.vocabulary import SimpleVocabulary

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.Five.viewlet.manager import ViewletManagerBase
from Products.Five.viewlet.viewlet import ViewletBase

from Products.CMFCore.utils import getToolByName

from z3c.form import button, field, group, form
from z3c.form.interfaces import IFormLayer, IDisplayForm, DISPLAY_MODE, HIDDEN_MODE
from z3c.form.browser import radio

# @view.memoize cache values for the lifespan of request
from plone.memoize import view 

from getpaid.core import interfaces
from getpaid.core.order import Order
from getpaid.core.interfaces import workflow_states as wf

from Products.PloneGetPaid.interfaces import IGetPaidManagementOptions
from Products.PloneGetPaid.browser.interfaces import IDontShowGetPaidPortlets
from Products.PloneGetPaid import _

from collective.z3cform.wizard.interfaces import IWizard, IStep
from collective.z3cform.wizard import wizard, utils


class ICheckoutContinuationKey(interface.Interface):
    """ Adapts Order to Checkout Wizard Continuation Key """

class CheckoutContinuationKeyAdapter(object):
    """ Adapts Order to Checkout Wizard Continuation Key """

    interface.implements(ICheckoutContinuationKey)

    _key = None

    def __repr__(self):
        return self._key

    def __init__(self, order):
        key = hashlib.md5()
        key.update(str(order.order_id))
        key.update(str(order.processor_order_id))
        key.update(str(order.creation_date))
        self._key = key.hexdigest()


class IPaymentProcessorButtonManager(viewlet.interfaces.IViewletManager):
    """ Viewlet manager for rendering payment buttons for payment processors """


class PaymentProcessorButtonManager(ViewletManagerBase):
    """ Viewlet manager for rendering payment buttons for payment processors """

    def sort (self, viewlets ):
        """ sort by weight """
        return sorted(viewlets, lambda x,y: cmp(int(getattr(x[1], 'weight', 100)), int(getattr(y[1], 'weight', 100))))

    def filter(self, viewlets):
        viewlets = super(PaymentProcessorButtonManager, self).filter(viewlets)
        portal = getToolByName(self.context, 'portal_url').getPortalObject()
        results = []
        for name, viewlet in viewlets:
            if name in IGetPaidManagementOptions(portal).payment_processors:
                results.append((name, viewlet))
        return results

    def render(self):
        return '<div id="payment-buttons">%s</div>' % "".join([b.render() for b in self.viewlets])


class IPaymentProcessorButton(interface.Interface):
    """ Checkout Wizard Payment button """
    # wizard = ...


class PaymentProcessorButtonBase(ViewletBase):
    """ Checkout Wizard Payment button base """

    interface.implements(IPaymentProcessorButton)

    def __init__(self, context, request, view, manager):
        self.wizard = view
        super(PaymentProcessorButtonBase, self).__init__(context, request, view, manager)


class SchemaGroup(group.Group):
    """ z3c.form.group, which extracts its fields from getpaid FormSchemas """
    label = _(u"Abstract Schema Group")
    section = None # see getpaid.core.interfaces.IFormSchemas for options

    def __init__(self, context, request, parentForm):
        assert self.section is not None,\
            "Inherit SchemaGroup and overwrite section with getpaid schema section."
        self.prefix = self.section
        schemas = component.getUtility(interfaces.IFormSchemas)
        schema_fields = []

        # FIXME: collective.z3cform.wizard doesn't support interface bound fields
        # and therefore, we must clone fields and detach the clones form interfaces:
        for name, iface_field in schema.getFieldsInOrder(schemas.getInterface(self.section)):
            schema_field = iface_field.__class__.__new__(iface_field.__class__)
            schema_field.__dict__.update(iface_field.__dict__)
            schema_field.interface = None
            schema_fields.append(schema_field)

        self.fields = field.Fields(*schema_fields)
        super(SchemaGroup, self).__init__(context, request, parentForm)
   
    def getContent(self):
        return self.parentForm.getContent()


class ContactGroup(SchemaGroup):
    label = _(u"Contact Information")
    section = 'contact_information'


class BillingGroup(SchemaGroup):
    label = _(u"Billing Information")
    section = 'billing_address'


class ShippingGroup(SchemaGroup):
    label = _(u"Shipping Information")
    section = 'shipping_address'


class PaymentGroup(SchemaGroup):
    label = _(u"Payment Information")
    section = 'payment'

#class IOrderId(interface.Interface):
#    order_id = schema.Text(title=_(u"Order Id"), required=False)
#
#class OrderDetails(form.DisplayForm, form.GroupForm):
#    interface.implements(IOrderId)
#
#    groups = (ContactGroup, BillingGroup, ShippingGroup, PaymentGroup)
#    fields = field.Fields()
#    render = ViewPageTemplateFile("templates/order-details.pt")
#
#    def update(self):
#        super(OrderDetails, self).update()
#       
#    def getContent(self):
#        content = {}

class Customer(wizard.GroupStep):
    prefix = 'details'
    label  = _(u"Customer details")
    description = _(u"Please, enter Your contact and billing information")
    weight = 20

    groups = None
    fields = field.Fields()
    template = ViewPageTemplateFile("templates/checkout-wizard-step-customer.pt")

    @property
    def available(self):
        return super(Customer, self).available and not self.wizard.isOrderAvailable
    
    def __init__(self, context, request, wizard):
        """ Filter required FormSchema sections """
        # No groups when cart is empty
        if not wizard.isCartAvailable:
            self.groups = ()
        # Include shipping information only, when cart
        # contains shippable items
        elif len([i for i in wizard._cart.values() \
                  if interfaces.IShippableLineItem.providedBy(i)]):
            self.groups = (ContactGroup, BillingGroup, ShippingGroup)
        # By default, include
        else:
            self.groups = (ContactGroup, BillingGroup)
        super(Customer, self).__init__(context, request, wizard)


class Review(Customer):
    prefix = 'review'
    label  = _(u"Review order")
    description = _(u"Please, review Your order information")
    weight = 40

    interface.implements(IDisplayForm)
    mode = DISPLAY_MODE
    ignoreRequest = True

    template = ViewPageTemplateFile("templates/checkout-wizard-step-review.pt")

    @property
    def available(self):
        return self.request.SESSION[self.wizard.sessionKey].get('details', None) \
            and not self.wizard.isOrderAvailable

    def getContent(self):
        return self.request.SESSION[self.wizard.sessionKey].get('details')


class Method(wizard.Step):
    prefix = 'method'
    label  = _(u"Payment method")
    description = _(u"Please, select Your payment method to pay the order")
    weight = 60

    fields = field.Fields(
       schema.Choice(__name__='processor_id', title=_(u"Other payment method"),
                     values=[], required=True))
    template = ViewPageTemplateFile("templates/checkout-wizard-step-method.pt")

    @property
    def available(self):
        finance_state = self.wizard.isOrderAvailable \
            and self.wizard._order.finance_workflow.state().getState() or None
        return super(Method, self).available \
            and finance_state in [None, wf.order.finance.REVIEWING] 

    def update(self):
        """ Setup widget for stepful payment processors, when processor spesific steps found """
        # FIXME: We cannot use IContextSourceBinder, because its context
        # would be wizard's data container (a dict from session) with no
        # way to get the wizard object.
        sm = component.getSiteManager()
        descriptions = {} # Processor's description should be stored as its registration info
        for registration in [r for r in sm.registeredUtilities() if r.name and r.info]:
            descriptions[registration.name] = registration.info
        stepful_processors = [SimpleVocabulary.createTerm(name, name, descriptions.get(name, _(name))) \
                                   for name in self.wizard._stepful_processors]
        if stepful_processors:
            self.fields["processor_id"].field.vocabulary = SimpleVocabulary(stepful_processors)
            self.fields["processor_id"].widgetFactory = radio.RadioFieldWidget
        else:
            self.fields["processor_id"].mode = HIDDEN_MODE

        # Now, when all order details should be collected (and only processor specific 
        # steps left), create an order and attach it to the session
        if not self.wizard.isOrderAvailable:
            self.wizard.session['order_id'] = self.wizard._createOrder()
        super(Method, self).update()

    @property
    def order_id(self):
        return self.wizard._order.order_id


class Payment(wizard.GroupStep):
    """ A default payment information step, must be explicitly included by payment processor """
    prefix = 'payment'
    label  = _(u"Payment details")
    description = _(u"Please, enter your payment information")
    weight = 70

    groups = (PaymentGroup,)
    fields = field.Fields()
    template = ViewPageTemplateFile("templates/checkout-wizard-step-payment.pt")

    @property
    def available(self):
        finance_state = self.wizard.isOrderAvailable \
            and self.wizard._order.finance_workflow.state().getState() or None
        return super(Payment, self).available \
            and finance_state == wf.order.finance.REVIEWING

    @property
    def order_id(self):
        return self.wizard._order.order_id


class Confirmation(wizard.GroupStep):
    """ Order confirmation view """
    prefix = 'confirmation'
    label  = _(u"Confirmation")
    description = _(u"Here's the confirmation for your order")
    weight = 80

    interface.implements(IDisplayForm)
    mode = DISPLAY_MODE
    ignoreRequest = True

    groups = None
    fields = field.Fields()
    template = ViewPageTemplateFile("templates/checkout-wizard-step-confirmation.pt")

    @property
    def available(self):
        return super(Confirmation, self).available \
            and self.wizard.isOrderAvailable

    def __init__(self, context, request, wizard):
        """ Filter required FormSchema sections """
        if  wizard.isVerifiedCheckoutContinuation \
                and wizard.session.has_key("order_id"):
            # Include shipping information only, when cart
            # contains shippable items
            if len([i for i in wizard._order.shopping_cart.values() \
                        if interfaces.IShippableLineItem.providedBy(i)]):
                self.groups = (ContactGroup, BillingGroup, ShippingGroup)
            # By default, include
            else:
                self.groups = (ContactGroup, BillingGroup)
        else:
            self.groups = ()
        super(Confirmation, self).__init__(context, request, wizard)

    def getContent(self):
        return self.request.SESSION[self.wizard.sessionKey].get('details')

    @property
    def order_id(self):
        return self.wizard._order.order_id

    @property
    def finance_state(self):
        return self.wizard._order.finance_state

    @property
    def fulfillment_state(self):
        return self.wizard._order.fulfillment_state

    def update(self):
        # For not yet authorized order
        if self.wizard._order.finance_state == wf.order.finance.REVIEWING \
                and self.wizard._authorizeOrder() != interfaces.keys.results_success:
            utils = getToolByName(self.context, 'plone_utils')
            utils.addPortalMessage(_(u"Your payment information couldn't be verified."))
            self.wizard.jump(self.wizard.currentIndex - 1)
        # For orders in other state
        else:
            super(Confirmation, self).update()
            self.wizard._resetSession()


class ICheckoutWizard(IWizard):
    """ Marker interface for wizard steps """


class CheckoutWizard(wizard.Wizard):
    """ Payment checkout wizard """
    interface.implements(ICheckoutWizard, IDontShowGetPaidPortlets)

    buttons = wizard.Wizard.buttons.copy()
    handlers = wizard.Wizard.handlers.copy()

    label = _(u"Online Checkout")

    # the overwritten collective.z3cform.wizard is found at self.index
    template = ViewPageTemplateFile("templates/checkout-wizard.pt")

    def __init__(self, context, request):
        super(CheckoutWizard, self).__init__(context, request)
        # Add IFormLayer for request to support z3c.form
        interface.alsoProvides(self.request, IFormLayer)

        # Request login, when anonymous user and anonymous checkouts has not been allowed
        mtool = getToolByName(self.context, 'portal_membership')
        site = getToolByName(self.context, 'portal_url').getPortalObject()
        if mtool.isAnonymousUser() and not IGetPaidManagementOptions(site).allow_anonymous_checkout:
            self.request.response.redirect('login_form?came_from=@@getpaid-checkout-wizard')

        # Redirect http:// to https:// when required
        url = self.request.getURL()
        if IGetPaidManagementOptions(site).use_ssl_for_checkout and not "https://" in url:
            url = url.replace("http://", "https://")
            querystring = ZTUtils.make_query(self.request.form)
            self.request.response.redirect('%(url)?%(querystring)s' % vars())

        # Tune z3cform.wizard's default buttons
        self.buttons["back"].title = _(u"Back")
        self.buttons["back"].condition = lambda form: form.isBackAvailable
        self.buttons["continue"].title = _(u"Continue")
        self.buttons["continue"].condition = lambda form: form.isContinueAvailable
        # Hide Finish button until we find use for z3cform.wizards "finish-action"
        self.buttons["finish"].title = _(u"Finish")
        self.buttons["finish"].condition = lambda form: False

    def update(self):
        """ See: collective.z3cform.wizard.Wizard.update() """
        # Had to overwrite whole update to get more control on 
        # initialization of steps, particularly, to enable
        # declarative configuration of steps via zcml/adapters

        # Initialize session
        sessionKey = self.sessionKey
        if not self.request.SESSION.has_key(sessionKey):
            self.request.SESSION[sessionKey] = {}

        # Reset session if we came from a URL different from that of the wizard,
        # unless it's the URL that's used during z3cform inline validation.
        referer = self.request.environ.get('HTTP_REFERER', "").replace("@@", "")
        url = self.request.get('ACTUAL_URL', "").replace("@@", "")
        if not self.isOrderAvailable and referer.startswith('http') \
                and 'kss_z3cform_inline_validation' not in url \
                and not utils.location_is_equal(url, referer):
            self.request.SESSION[sessionKey] = {}
        self.session = self.request.SESSION[sessionKey]

        # Get all payment processors (to filter possible processors steps)
        # Query and initialize steps, include processor step if processor selected
        self.activeSteps = []
        for name, step in component.getAdapters((self.context, self.request, self), IStep):
            if name not in self._processor_names or name == self._selected_processor:
                step.__name__ = name
                self.activeSteps.append(step)
        self.activeSteps.sort(lambda x,y: cmp(int(getattr(x, 'weight', 100)), int(getattr(y, 'weight', 100))))

        # Init the session sata, if this wizard hasn't been loaded yet in this session
        if not len(self.session):
            self.initialize()
            self.sync()

        # Select the current step
        # a) If paid order exist, go to the final step
        if self.isOrderAvailable \
                and self._order.finance_state != wf.order.finance.REVIEWING:
            self.updateCurrentStep(len(self.activeSteps) - 1)
        # b) or look for explicit (available) step from request
        elif 'step' in self.request.form:
            self.jump(self.request.form['step'])
        # c) or read the step from the session
        else:
            self.updateCurrentStep(self.session.setdefault('step', 0))

        self.updateActions()
        self.actions.execute()
        self.updateWidgets()

    @button.buttonAndHandler(_(u"Cancel"), name="cancel",
                             condition=lambda form: not form.onLastStep)
    def handleCancel(self, action):
        self._cancelOrder()
        self._destroyCart()
        self._resetSession()
        utils = getToolByName(self.context, 'plone_utils')
        utils.addPortalMessage(_(u"Your order has been cancelled."))
        portal = getToolByName(self.context, 'portal_url').getPortalObject()
        self.request.response.redirect(portal.absolute_url() + "/@@checkout-wizard")

    @property
    def onLastStep(self):
        return self.currentIndex == len(self.activeSteps) - 1

    @property
    def isBackAvailable(self):
        return not self.onFirstStep \
            and self.activeSteps[self.currentIndex - 1].available
    
    @property
    def isContinueAvailable(self):
        return not self.onLastStep \
            and (not self._order or self._stepful_processors)

    @property
    def isCartAvailable(self):
        return self._cart and True or False

    @property
    def isOrderAvailable(self):
        return self._order and True or False

    @property
    def isVerifiedCheckoutContinuation(self):
        if hasattr(self, "session") and self.session.get("order_id", None):
            return True
        elif self.isOrderAvailable and self.request.form.has_key("key"):
            key = str(component.getAdapter(self._order, ICheckoutContinuationKey))
            return self.request.form.get("key") == key
        return False

    @property
    def canPaymentButtonsBeShown(self):
        finance_state = self.isOrderAvailable \
            and self._order.finance_workflow.state().getState() or None
        return self.isOrderAvailable and not self.isBackAvailable \
            and finance_state in [None, wf.order.finance.REVIEWING]

    @property
    def _cart(self):
        manager = component.getUtility( interfaces.IShoppingCartUtility )
        return manager.get(self.context, create=False) or None

    @property
    def _order(self):
        manager = component.getUtility(interfaces.IOrderManager)
        order_id = hasattr(self, "session") and self.session.get("order_id", None) \
            or self.request.form.get("order_id", None)
        return order_id and order_id in manager and manager.get(order_id) or None

    @property
    def _selected_processor(self):
        """ selected payment processor, when selected """
        return self.request.form.get('method.widgets.processor_id', [None])[0] \
            or self.session.has_key('method') and self.session['method'].get('processor_id', None) or None

    @property
    @view.memoize
    def _processor_names(self):
        """ selected payment processor, when selected """
        processor_names = [processor.value for processor in
                           component.getUtility(schema.interfaces.IVocabularyFactory,
                                                "getpaid.payment_methods")(self.context)]
        # Append also uninstalled processors, since their adapters are registered anyway
        for plugin_id, plugin_manager in component.getAdapters((self.context,), interfaces.IPluginManager):
            if plugin_id not in processor_names:
                processor_names.append(plugin_id)
        return processor_names

    @property
    @view.memoize
    def _stepful_processors(self):
        site = getToolByName(self.context, 'portal_url').getPortalObject()
        enabled_processors = IGetPaidManagementOptions(site).payment_processors
        return [processor for processor in enabled_processors \
                    if component.queryMultiAdapter((self.context, self.request, self), IStep, name=processor)]

    def _resetSession(self):
        self.request.SESSION[self.sessionKey] = {}
        self.sync()

    def _createOrder(self):
        # FIXME: currently, this is oversimplication of order creation process and
        # doesn't include shipping or any other "special" cases
        order = Order()
        
        mtool = getToolByName(self.context, "portal_membership")
        if mtool.isAnonymousUser():
            order.user_id = "anonymous"
        else:
            order.user_id = mtool.getAuthenticatedMember().getId()

        # Fill in the order by searching the wizard's session for
        # field names defined by getpaid form schemas.
        schemas = component.getUtility(interfaces.IFormSchemas)
        for section in ("billing_address", "shipping_address", "contact_information"):
            bag = schemas.getBagClass(section)()
            for field_name, field in schema.getFieldsInOrder(bag.schema):
                for step in self.session.keys():
                    if type(self.session[step]) is types.DictType \
                            and self.session[step].has_key(field_name):
                        setattr(bag, field_name, self.session[step][field_name])
            setattr(order, section, bag)
        order.name_on_card = order.billing_address.bill_name
        order.bill_phone_number = order.contact_information.phone_number

        # Shopping cart is attached to the session, but we want to                                                     
        # switch the storage to the persistent zodb, we pickle to get a                                                
        # clean copy to store.                                                                                         
        order.shopping_cart = cPickle.loads(cPickle.dumps(self._cart))

        # Store the order
        manager = component.getUtility(interfaces.IOrderManager)
        while True:
            order.order_id = manager.newOrderId()
            try:
                manager.store(order)
                break
            except exceptions.DuplicationError:
                # the id was taken, try again
                pass

        # Fire transition, destroy cart and return id
        order.finance_workflow.fireTransition('create')
        self._destroyCart()
        return order.order_id
    
    def _authorizeOrder(self):
        """ Simple authorization for onsite (stepful) payment processors """

        order = self._order
        processor_id = self._selected_processor
        processor = component.getUtility(interfaces.IPaymentProcessor, name=processor_id)

        # Fill in the payment information
        schemas = component.getUtility(interfaces.IFormSchemas)
        payment_information = schemas.getBagClass("payment")(self.session)
        for field_name, field in schema.getFieldsInOrder(payment_information.schema):
            for step in self.session.keys():
                if type(self.session[step]) is types.DictType \
                        and self.session[step].has_key(field_name):
                    setattr(payment_information, field_name, self.session[step][field_name])

        # FIXME: This doesn't currently store anything from payment_information
        # to order, if processor doesn't do it
        if processor.authorize(order, payment_information) == interfaces.keys.results_success:
            order.processor_id = processor_id
            if order.finance_state == wf.order.finance.REVIEWING:
                order.finance_workflow.fireTransition("authorize")
            if order.fulfillment_state == None:
                order.fulfillment_workflow.fireTransition("create")
            return interfaces.keys.results_success
        else:
            return False

    def _cancelOrder(self):
        if self.isOrderAvailable:
            order = self._order

            if order.finance_state is None:
                order.finance_workflow.fireTransition("create")
            if order.finance_state is wf.order.finance.REVIEWING:
                order.finance_workflow.fireTransition("reviewing-declined")
            if order.finance_state is wf.order.finance.PAYMENT_DECLINED:
                order.finance_workflow.fireTransition("cancel-declined")

            if order.fulfillment_state is None:
                order.fulfillment_workflow.fireTransition("create")
            if order.fulfillment_state is wf.order.fulfillment.NEW:
                order.fulfillment_workflow.fireTransition("cancel-new-order")

    def _destroyCart(self):
        component.getUtility(interfaces.IShoppingCartUtility).destroy(self.context)