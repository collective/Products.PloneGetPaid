"""

    Dummy payment processor definitions.

"""

import zope.interface

from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

import getpaid.core.interfaces

from Products.PloneGetPaid.browser.checkout import BasePaymentMethodButton

class DummyButton(BasePaymentMethodButton):
    """ This piece of HTML is rendered on the payment method selection page """


class DummyThankYou(BrowserView):
    """ This piece of HTML is rendered when the payment has been completed """


class DummyProcessor:
    zope.interface.implements(getpaid.core.interfaces.IPaymentProcessor)


# Enable one dummy payment processor
configure_zcml = '''
<configure
    xmlns="http://namespaces.zope.org/zope"
    xmlns:five="http://namespaces.zope.org/five"
    xmlns:paymentprocessors="http://namespaces.plonegetpaid.com/paymentprocessors"
    xmlns:browser="http://namespaces.zope.org/browser"
    i18n_domain="foo">

    <paymentprocessors:registerProcessor
       name="dummy"
       processor="Products.PloneGetPaid.tests.dummy_processors.DummyProcessor"
       selection_view="dummy_payment_processor_button"
       thank_you_view="dummy_payment_processor_thank_you_page"
       settings_view="dummy_payment_processor_settings"
       />

    <browser:page
         for="getpaid.core.interfaces.IStore"
         name="dummy_payment_processor_button"
         class="Products.PloneGetPaid.tests.dummy_processors.DummyButton"
         permission="zope2.View"
         template="templates/button.pt"
         />

    <browser:page
         for="getpaid.core.interfaces.IStore"
         name="dummy_payment_processor_thank_you_page"
         class="Products.PloneGetPaid.tests.dummy_processors.DummyThankYou"
         permission="zope2.View"
         template="templates/thank_you.pt"
         />

    <browser:page
         for="getpaid.core.interfaces.IStore"
         name="dummy_payment_processor_settings"
         class="Products.PloneGetPaid.browser.admin.PaymentProcessor"
         permission="cmf.ManagePortal"
         />

</configure>'''

# Enable two dummy payment processors
configure_zcml_2 = '''
<configure
    xmlns="http://namespaces.zope.org/zope"
    xmlns:five="http://namespaces.zope.org/five"
    xmlns:paymentprocessors="http://namespaces.plonegetpaid.com/paymentprocessors"
    i18n_domain="foo">

    <paymentprocessors:registerProcessor
       name="dummy2"
       processor="Products.PloneGetPaid.tests.dummy_processors.DummyProcessor"
       selection_view="dummy_payment_processor_button"
       thank_you_view="dummy_payment_processor_thank_you_page"
       />

</configure>'''