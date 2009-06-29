"""
admin setting and preferences

$Id$
"""

import os

from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from Products.Five.browser import BrowserView
from Products.Five.formlib import formbase
from Products.Five.viewlet import manager
from Products.PloneGetPaid import interfaces

from zope import component
from zope.formlib import form
from zope.viewlet.interfaces import IViewlet

import getpaid.core.interfaces as igetpaid
from getpaid.paymentprocessors.registry import paymentProcessorRegistry

from Products.PloneGetPaid.interfaces import ISettingsShipmentManager
from Products.PloneGetPaid.i18n import _

from Products.CMFCore.utils import getToolByName

from base import BaseView, FormViewlet
from widgets import SelectWidgetFactory, CountrySelectionWidget, StateSelectionWidget


class Overview( BrowserView ):
    """ overview of entire system
    """
    def __call__( self ):
        self.settings = interfaces.IGetPaidManagementOptions( self.context )
        return super( Overview, self).__call__()

    def getVersion( self ):
        qi = getToolByName(self.context, 'portal_quickinstaller')
        return qi.getProductVersion('PloneGetPaid')

class BaseSettingsForm( formbase.EditForm, BaseView ):

    options = None
    template = ZopeTwoPageTemplateFile("templates/settings-page.pt")

    def __init__( self, context, request ):
        self.context = context
        self.request = request
        self.setupLocale( request )
        self.setupEnvironment( request )

    def update( self ):
        try:
            interface = iter( self.form_fields ).next().field.interface
        except StopIteration:
            interface = None
        if interface is not None:
            self.adapters = { interface : interfaces.IGetPaidManagementOptions( self.context ) }
        super( BaseSettingsForm, self).update()

class Identification( BaseSettingsForm ):
    """
    get paid management interface
    """
    form_fields = form.Fields(interfaces.IGetPaidManagementIdentificationOptions)
    form_fields['contact_country'].custom_widget = CountrySelectionWidget
    form_fields['contact_state'].custom_widget = StateSelectionWidget
    form_name = _(u'Site Profile')

class ContentTypes( BaseSettingsForm ):
    """
    get paid management interface
    """
    form_fields = form.Fields( interfaces.IGetPaidManagementContentTypes )
    form_fields = form_fields.omit('premium_types')
    #form_fields = form_fields.omit('shippable_types')
    form_name = _(u'Content Types')

    form_fields['buyable_types'].custom_widget = SelectWidgetFactory
    #form_fields['premium_types'].custom_widget = SelectWidgetFactory
    form_fields['donate_types'].custom_widget = SelectWidgetFactory
    form_fields['shippable_types'].custom_widget = SelectWidgetFactory

class SettingViewletManager( object ):
    """ Viewlet Manager for Plugin Configuration"""

    def _getNames( self ):
        raise NotImplemented

    def update(self):
        """See zope.contentprovider.interfaces.IContentProvider"""
        self.__updated = True

        # Find all content providers for the region
        viewlets = component.getAdapters(
            (self.context, self.request, self.__parent__, self),
            IViewlet)

        #  update the setting viewlet first, as that determines
        #  which viewlets we end up filtering
        viewlets = list( viewlets )

        setting_viewlet = [v for n,v in viewlets if n == 'settings'][0]
        setting_viewlet.update()


        viewlets = self.filter(viewlets)
        viewlets = self.sort(viewlets)

        # Just use the viewlets from now on
        self.viewlets = [viewlet for name, viewlet in viewlets]

        # Update all viewlets
        for viewlet in self.viewlets:
            if viewlet == setting_viewlet:
                continue
            viewlet.update()


    def filter( self, viewlets ):
        # filter only active plugins to the ui
        viewlets = super( SettingViewletManager, self).filter( viewlets )
        services = self._getNames()
        for n,v in viewlets[:]:
            if n == 'settings':
                continue
            if n not in services:
                viewlets.remove( ( n, v ) )
        return viewlets

    def sort (self, viewlets ):
        """ sort by name """
        viewlets.sort( lambda x,y: cmp( int(x[1].weight), int(y[1].weight) ) )
        return viewlets

_prefix = os.path.dirname( __file__ )

PluginSettingsManagerTemplate = os.path.join( _prefix, "templates", "viewlet-manager.pt")

class _ShippingViewletManager( SettingViewletManager ):

    def _getNames( self ):
        settings = interfaces.IGetPaidManagementShippingMethods( self.context )
        return settings.shipping_services

ShippingViewletManager = manager.ViewletManager( "ShippingViewletManager",
                                                 ISettingsShipmentManager,
                                                 PluginSettingsManagerTemplate,
                                                 bases=(_ShippingViewletManager,)
                                                 )
# class _PaymentViewletManager( SettingViewletManager ):
#
#     def _getNames( self ):
#         return ()
#
# PaymentViewletManager = manager.ViewletManager( "ShippingViewletManager",
#                                                  ISettingsShipmentManager,
#                                                  PluginSettingsManagerTemplate
#                                                  bases=(ShippingViewletManager,)
#                                                  )




class ShippingSettings( BrowserView ):
    """
    container view for all shipping settings (shipment plugin config ui gets
    pulled in to this view as well).
    """
    template = ZopeTwoPageTemplateFile('templates/settings-shipping.pt')

    def __call__( self ):
        return self.template()

class ShippingServices( FormViewlet, formbase.EditForm ):
    """
    viewlet for selecting shipping services
    """
    form_fields = form.Fields(interfaces.IGetPaidManagementShippingMethods)
    form_fields['shipping_methods'].custom_widget = SelectWidgetFactory
    form_fields['shipping_services'].custom_widget = SelectWidgetFactory
    form_name = _(u'Shipping Methods')

    template = ZopeTwoPageTemplateFile('templates/form.pt')

    def setUpWidgets( self, ignore_request=False ):
        self.adapters = self.adapters or {}
        self.widgets = form.setUpEditWidgets(
            self.form_fields, self.prefix, self.context, self.request,
            adapters=self.adapters, ignore_request=ignore_request
            )

    def update( self ):
        try:
            interface = iter( self.form_fields ).next().field.interface
        except StopIteration:
            interface = None
        if interface is not None:
            self.adapters = { interface : interfaces.IGetPaidManagementOptions( self.context ) }
        super( ShippingServices, self).update()

    def render( self ):
        return self.template()

class PaymentOptions( BaseSettingsForm ):
    """
    get paid management interface
    """
    form_fields = form.Fields(interfaces.IGetPaidManagementPaymentOptions)
    form_fields['accepted_credit_cards'].custom_widget = SelectWidgetFactory
    form_name = _(u'Payment Options')
    """
    def __init__( self, context, request ):
        " Used to force an initial value of 'Payment processor' option; no need to click 'Apply'
            button to get payment process work
        "
        self.
    """

class PaymentProcessors(BrowserView):
    """ The user goes to payment processor settings in GetPaid setup.

    Print available payment processors and see if they are enabled. Allow users
    to choose which processors to enable. Print links to individual processor setting
    pages.

    Payment processors are stored in portal_properties.payment_processor_properties.

    TODO: This form is not protected against XSS attacks and takes some shortcuts
    to bypass zope.formlib. I am not experienced enough zope.formlib user.
    """

    template = ZopeTwoPageTemplateFile('templates/settings-payment-processors.pt')

    def getCheckedForProcessor(self, processor):
        """

        @param processsor: Processor class instance
        """

        # See profiles/default/propertiestool.xml
        if processor.name in self.context.portal_properties.payment_processor_properties.enabled_processors:
            return "CHECKED"
        else:
            return None

    def getProcessors(self):
        """ Called from the template.

        @return: Iterable of Processor objects
        """
        return paymentProcessorRegistry.getProcessors()

    def processForm(self):
        """ Manage HTTP post """
        actived = self.request["active-payment-processors"]

        # Add some level of safety
        for a in actived:
            if not a in paymentProcessorRegistry.getNames():
                raise RuntimeError("Tried to enable unsupported processor %s" % a)

        self.context.portal_properties.payment_processor_properties.enabled_processors = actived

        from Products.statusmessages.interfaces import IStatusMessage
        statusmessages = IStatusMessage(self.request)
        statusmessages.addStatusMessage(u"Active payment processors updated", "info")


    def __call__(self):

        if self.request["REQUEST_METHOD"] == "GET":
            return self.template() # render page
        else:
            # Assume POST, user is changing active payment methods
            self.processForm()
            return self.template() # render page


class PaymentProcessor( BaseSettingsForm ):
    """
    get paid management interface, slightly different because our form fields
    are dynamically set based on the store's setting for a payment processor.
    """

    form_fields = form.Fields()
    form_name = _(u'Payment Processor Settings')

    def __call__( self ):
        self.setupProcessorOptions()
        return super( PaymentProcessor, self).__call__()


    def getPaymentProcessorName(self):
        """ Processor specific setting screen

        @return: String, getpaid.core.interfaces.IPaymentProcessor name
        """

        # BBB
        # This returns the active payment processor from old style getpaid
        manage_options = interfaces.IGetPaidManagementOptions( self.context )

        processor_name = manage_options.payment_processor
        return processor_name

    def setupProcessorOptions( self ):

        processor_name = self.getPaymentProcessorName()

        if not processor_name:
            self.status = _(u"Please Select Payment Processor in Payment Options Settings")
            return

        #NOTE: if a processor name is saved in the configuration but the corresponding payment method package
        # doesn't exist anymore, a corresponding adapter will not be found.
        try:
            processor = component.getAdapter( self.context,
                                              igetpaid.IPaymentProcessor,
                                              processor_name )
        except:
            self.status = _(u"The currently configured Payment Processor cannot be found; please check if the corresponding package is installed correctly.")
            return

        self.form_fields = form.Fields( processor.options_interface )

# Order Management
class CustomerInformation( BaseSettingsForm ):
    """
    get paid management interface
    """
    form_fields = form.Fields(interfaces.IGetPaidManagementCustomerInformation)

class PaymentProcessing( BaseSettingsForm ):
    """
    get paid management interface
    """
    form_fields = form.Fields(interfaces.IGetPaidManagementPaymentProcessing)

class WeightUnits( BaseSettingsForm ):
    """
    get paid management interface
    """
    form_fields = form.Fields(interfaces.IGetPaidManagementWeightUnits)

class SessionTimeout( BaseSettingsForm ):
    """
    get paid management interface
    """
    form_fields = form.Fields(interfaces.IGetPaidManagementSessionTimeout)

class SalesTax( BaseSettingsForm ):
    """
    get paid management interface
    """
    form_fields = form.Fields(interfaces.IGetPaidManagementSalesTaxOptions)
    form_name = _(u'Sales Tax Configuration')

#Currency
class Currency( BaseSettingsForm ):
    """
    get paid management interface
    """
    form_fields = form.Fields(interfaces.IGetPaidManagementCurrencyOptions)

#Emails
class Email( BaseSettingsForm ):
    """
    get paid management interface
    """
    form_fields = form.Fields(interfaces.IGetPaidManagementEmailOptions)
    form_name = _(u'Email Notifications')

#Customize Header/Footer
class LegalDisclaimers( BaseSettingsForm ):
    """
    get paid management interface
    """
    form_fields = form.Fields(interfaces.IGetPaidManagementLegalDisclaimerOptions)
    form_name = _(u'Legal Disclaimers')

#Customize Checkout Options
class CheckoutOptions( BaseSettingsForm ):
    """
    get paid management interface
    """
    form_fields = form.Fields(interfaces.IGetPaidManagementCheckoutOptions)
    form_name = _(u'Checkout Options')




