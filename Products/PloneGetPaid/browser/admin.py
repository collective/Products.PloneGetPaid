"""
admin setting and preferences

$Id$
"""

import os

from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from Products.Five.browser import BrowserView
from Products.Five.formlib import formbase
from Products.Five.viewlet import manager
from Products.PloneGetPaid import interfaces, discover

from zope import component, schema
from zope.formlib import form
from zope.viewlet.interfaces import IViewlet

import getpaid.core.interfaces as igetpaid

from Products.PloneGetPaid.interfaces import ISettingsShipmentManager
from Products.PloneGetPaid.i18n import _

from Products.CMFCore.utils import getToolByName

from base import BaseView, FormViewlet
from widgets import SelectWidgetFactory, CountrySelectionWidget, StateSelectionWidget, SendDontSendWidget


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
        """Save form data the admin submits.

        The `adapters` map created here directs that each payment
        processor setting, whatever its source interface (since some
        settings will come from GetPaid core components, while others
        come from the options interfaces of currently selected payment
        processors), gets stored in the same annotation as the normal
        GetPaid management options.  Hopefully payment processor authors
        will choose attribute names that do not conflict.

        """
        self.adapters = {}
        getpaid_options = interfaces.IGetPaidManagementOptions(self.context)
        for f in self.form_fields:
            self.adapters[f.field.interface] = getpaid_options

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

class FakeFieldsetView(object):
    """An object to hold attributes for the "form.pt" view."""
    def __init__(self, **kw):
        for k, v in kw.iteritems():
            setattr(self, k, v)

class PaymentProcessor( BaseSettingsForm ):
    """
    get paid management interface, slightly different because our form fields
    are dynamically set based on the store's setting for a payment processor.
    """

    template = ZopeTwoPageTemplateFile("templates/admin-processors.pt")
    form_fields = form.Fields()
    form_name = _(u'Payment Processor Settings')

    def __call__( self ):
        self.setupProcessorOptions()
        return super( PaymentProcessor, self).__call__()

    def setupProcessorOptions( self ):
        field_lists = []
        self.fieldsets = []

        # Find the current on-site payment processor, if any.

        processor = discover.selectedOnsitePaymentProcessor()
        if processor:
            field_lists.append(form.Fields(processor.options_interface,
                                           prefix='onsite'))
            self.fieldsets.append(
                (_(u'On-site payment processor options'), 'onsite')
                )

        # Add a block of fields for any off-site processors.

        for processor in discover.selectedOffsitePaymentProcessors():
            fields = form.fields(processor.options_interface,
                                 prefix=processor.name)
            field_lists.append(fields)
            self.fieldsets.append((_(u'%s Options') % processor.title,
                                   processor.name))

        self.form_fields = form.Fields(*field_lists)

        # If we have nothing to display, let the store owner know why.

        if not field_lists:
            self.status = _(u'Neither on-site nor off-site payment processing'
                            u' is currently enabled.')

    def setUpWidgets(self, ignore_request=False):
        """After the usual setUpWidgets(), get fieldsets ready for display.

        All of the forms in this part of GetPaid get rendered by the
        'templates/form.pt' file in this directory.  The problem is that
        the form only wants to draw one form with a box around it, while
        we want to have several boxes with a fieldset inside of each
        (and the whole thing, then, is a single form).

        Fortunately, the 'form.pt' template is so thick with concentric
        macros that it is easy, via the template attached to this view,
        to re-use it but call its inner section in a loop for each of
        our fieldsets.  The problem?  Its inner loop only knows about
        the 'view' that it is rendering, and asks for a collection of
        items on the view that don't normally exist on fieldsets:

        view/form_description view/form_name view/request view/widgets

        To make it possible to re-use the inside of 'form.pt', then, we
        create a list of fake objects that look like views from the
        template's point of view, but are really bare little objects
        with four attributes stuck on them.  The HTML inside our little
        page template then passes each of these objects into the inner
        logic of 'form.pt' under the name 'view'.

        """
        r = super(PaymentProcessor, self).setUpWidgets()

        self.fieldset_views = []

        for title, name in self.fieldsets:
            widgets = [ widget for widget in self.widgets
                        if widget.name.startswith('form.%s.' % name) ]
            view = FakeFieldsetView(form_description=None, form_name=title,
                                    request=self.request, widgets=widgets)
            self.fieldset_views.append(view)

        return r


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

CUSTOMER_AUTH_NOTIFICATION_TEMPLATE = u'''\
To: ${to_email}
From: "${from_name}" <${from_email}>
Subject: New Order Notification

Thank you for you order.

Total Amount to be Charged : ${total_price}

${view_order_information}

Order Contents

${order_contents}

Shipping Cost: ${shipping_cost}

'''

MERCHANT_AUTH_NOTIFICATION_TEMPLATE = u'''\
To: ${to_email}
From: "${from_name}" <${from_email}>
Subject: New Order Notification

A New Order has been created

Total Cost: ${total_price}

To continue processing the order follow this link:
${store_url}/@@admin-manage-order/${order_id}/@@admin

Order Contents

${order_contents}

Shipping Cost: ${shipping_cost}

'''

CUSTOMER_CHARGE_NOTIFICATION_TEMPLATE = u'''\
To: ${to_email}
From: "${from_name}" <${from_email}>
Subject: New Order Notification

Thank you for you order.

Total Amount Charged : ${total_price}

${view_order_information}

Order Contents

${order_contents}

Shipping Cost: ${shipping_cost}

'''

MERCHANT_CHARGE_NOTIFICATION_TEMPLATE = u'''\
To: ${to_email}
From: "${from_name}" <${from_email}>
Subject: New Order Notification

A New Order has been charged

Total Cost: ${total_price}

To continue processing the order follow this link:
${store_url}/@@admin-manage-order/${order_id}/@@admin

Order Contents

${order_contents}

Shipping Cost: ${shipping_cost}

'''


CUSTOMER_DECLINE_NOTIFICATION_TEMPLATE = u'''\
To: ${to_email}
From: "${from_name}" <${from_email}>
Subject: Order Declined Notification

We're sorry but we were unable to charge your credit card.
'''

MERCHANT_DECLINE_NOTIFICATION_TEMPLATE = u'''\
To: ${to_email}
From: "${from_name}" <${from_email}>
Subject: Order Declined Notification

A Order was declined

Total Cost: ${total_price}

To view this order follow this link:
${store_url}/@@admin-manage-order/${order_id}/@@admin

Order Contents

${order_contents}

'''


class Email( BaseSettingsForm ):
    """
    get paid management interface
    """
    form_fields = form.Fields(interfaces.IGetPaidManagementEmailOptions)

    #
    # Auth Emails
    #
    form_fields['merchant_auth_email_notification_template'].field.default = MERCHANT_AUTH_NOTIFICATION_TEMPLATE
    form_fields['send_merchant_auth_notification'].custom_widget = SendDontSendWidget
    form_fields['customer_auth_email_notification_template'].field.default = CUSTOMER_AUTH_NOTIFICATION_TEMPLATE
    form_fields['send_customer_auth_notification'].custom_widget = SendDontSendWidget

    #
    # Charge Emails
    #
    form_fields['merchant_charge_email_notification_template'].field.default = MERCHANT_CHARGE_NOTIFICATION_TEMPLATE
    form_fields['send_merchant_charge_notification'].custom_widget = SendDontSendWidget
    form_fields['customer_charge_email_notification_template'].field.default = CUSTOMER_CHARGE_NOTIFICATION_TEMPLATE
    form_fields['send_customer_charge_notification'].custom_widget = SendDontSendWidget

    #
    # Decline Emails
    #
    form_fields['merchant_decline_email_notification_template'].field.default = MERCHANT_DECLINE_NOTIFICATION_TEMPLATE
    form_fields['send_merchant_decline_notification'].custom_widget = SendDontSendWidget
    form_fields['customer_decline_email_notification_template'].field.default = CUSTOMER_DECLINE_NOTIFICATION_TEMPLATE
    form_fields['send_customer_decline_notification'].custom_widget = SendDontSendWidget

    #
    # Refund Emails
    #
#     form_fields['merchant_refund_email_notification_template'].field.default = u"Foo"
#     form_fields['send_merchant_refund_notification'].custom_widget = SendDontSendWidget
#     form_fields['customer_refund_email_notification_template'].field.default = u"Foo"
#     form_fields['send_customer_refund_notification'].custom_widget = SendDontSendWidget


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

