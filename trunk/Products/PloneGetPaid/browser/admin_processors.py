"""
admin payment processor settings

$Id: admin_processors.py 3449 2010-04-13 14:46:04Z datakurre $
"""

from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from Products.Five.browser import BrowserView
from Products.Five.formlib import formbase
from Products.Five.viewlet import manager
from Products.PloneGetPaid import interfaces

from zope.formlib import form

from Products.PloneGetPaid.interfaces import ISettingsPaymentManager
from Products.PloneGetPaid.i18n import _

from base import FormViewlet
from widgets import SelectWidgetFactory
from admin import SettingViewletManager, PluginSettingsManagerTemplate


class _PaymentViewletManager( SettingViewletManager ):

    def _getNames( self ):
        options = interfaces.IGetPaidManagementPaymentOptions( self.context )
        return options.payment_processors


PaymentViewletManager = manager.ViewletManager( "PaymentViewletManager",
                                                ISettingsPaymentManager,
                                                PluginSettingsManagerTemplate,
                                                bases=(_PaymentViewletManager,)
                                                )

class PaymentOptions( BrowserView ):
    """
    container view for all payment options (payment plugin config ui gets
    pulled in to this view as well).
    """
    template = ZopeTwoPageTemplateFile('templates/settings-processors.pt')

    def __call__( self ):
        return self.template()


class PaymentProcessors( FormViewlet, formbase.EditForm ):
    """
    viewlet for selecting payment options
    """
    form_fields = form.Fields(interfaces.IGetPaidManagementPaymentOptions)
    form_fields['payment_processors'].custom_widget = SelectWidgetFactory
    form_name = _(u'Payment Options')

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
        super( PaymentProcessors, self).update()

    def render( self ):
        return self.template()
