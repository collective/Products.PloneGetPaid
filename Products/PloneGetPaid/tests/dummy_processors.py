"""

    Dummy payment processor definitions.

"""

import zope.interface

from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile

import getpaid.core.interfaces

from Products.PloneGetPaid.browser import checkout as base

class DummyButton(base.BasePaymentMethodButton):
    """ This piece of HTML is rendered on the payment method selection page """
    
    
class DummyReviewAndPay(base.CheckoutReviewAndPay):
    template = ZopeTwoPageTemplateFile("templates/pay.pt")
    

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

    <adapter
     for="getpaid.core.interfaces.IStore"
     provides="getpaid.core.interfaces.IPaymentProcessor"
     factory="Products.PloneGetPaid.tests.dummy_processors.DummyProcessor"
     name="Dummy Processor"
     />

    <paymentprocessors:registerProcessor
       name="Dummy Processor"
       i18n_name="Dummy processor"
       selection_view="dummy_payment_processor_button"
       review_pay_view="dummy_payment_processor_review_pay"
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
         
    <browser:page
         for="getpaid.core.interfaces.IStore"
         name="dummy_payment_processor_review_pay"
         class="Products.PloneGetPaid.tests.dummy_processors.DummyReviewAndPay"
         permission="zope2.View"
         template="templates/pay.pt"
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
       i18n_name="Foobar"
       selection_view="dummy_payment_processor_button"
       thank_you_view="dummy_payment_processor_thank_you_page"
       review_pay_view="dummy_payment_processor_pay"
       />

</configure>'''