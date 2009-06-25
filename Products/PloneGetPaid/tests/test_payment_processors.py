"""

    Multiple payment processors test cases.

"""
import os, sys
import unittest

from Products.Five import zcml
from zope.configuration.exceptions import ConfigurationError

from base import PloneGetPaidTestCase
from getpaid.paymentprocessors.registry import BadViewConfigurationException, paymentProcessorRegistry
import dummy_processors

from getpaid.paymentprocessors.interfaces import IPaymentMethodInformation

class TestPaymentMethods(PloneGetPaidTestCase):
    """ Test ZCML directives """

    def afterSetUp(self):
        PloneGetPaidTestCase.afterSetUp(self)
        paymentProcessorRegistry.clear()

    def loadDummyZCML(self, string):
        """ Load ZCML as a string and set the folder so that template references are related correctly. """
        module = sys.modules[__name__]
        dir = os.path.dirname(module.__file__)
        os.chdir(dir)
        zcml.load_string(string)

    def enable_processor(self):
        """ Enable one dummy payment processor for testing """
        self.loadDummyZCML(dummy_processors.configure_zcml)
        self.portal.portal_properties.payment_processor_properties.enabled_processors = [ "Dummy Processor"]

    def render_admin(self):
        """ Test rendering admin interface views with the current paymentprocessor configuration. """

        # Render the page where you can choose which payment processor settings are managed

        self.loginAsPortalOwner()
        view = self.portal.restrictedTraverse("@@manage-getpaid-payment-processor")
        view()
        self.logout()


    def get_payment_method_selection_screen(self):
        """ Get the checkout payment method selection view via checkout wizard """

        # Force in checkout wizard step
        step = "checkout-payment-method"
        self.portal.REQUEST["cur_step"] = step # See _wizard.pt
        wizard = self.portal.restrictedTraverse("@@getpaid-checkout-wizard")

        view = wizard.controller.getCurrentStep()
        return view

    def render_payment_method_selection_screen(self, assertedProcessorCount):
        """ Test rendering payment method selection page in checkout wizard """

        view = self.get_payment_method_selection_screen()

        processors = view.getProcessors()
        self.assertEqual(len(processors), assertedProcessorCount)

        # Render payment method selection HTML - see that template doesn't raise an error
        # TODO: Check HTML output validy using functional tests
        view()


    def test_selection_screen_no_processor(self):
        """ Test different count of site payment processors """

        # Go to checkout process point where the payment method is selected
        self.render_payment_method_selection_screen(0)

        self.portal.portal_properties.payment_processor_properties.enabled_processors = []

        # Test rendering related admin interface pages and hope to catch all raised exceptions
        self.render_admin()

    def test_selection_screen_one_processor(self):
        """ Test different count of site payment processors """
        self.loadDummyZCML(dummy_processors.configure_zcml)

        self.portal.portal_properties.payment_processor_properties.enabled_processors = [ "Dummy Processor"]

        # Go to checkout process point where the payment method is selected
        self.render_payment_method_selection_screen(1)

        # Test rendering related admin interface pages and hope to catch all raised exceptions
        self.render_admin()


    def test_selection_screen_n_processors(self):
        """ Test different count of site payment processors """
        self.loadDummyZCML(dummy_processors.configure_zcml)
        self.loadDummyZCML(dummy_processors.configure_zcml_2)

        self.portal.portal_properties.payment_processor_properties.enabled_processors = [ "Dummy Processor", "dummy2"]

        # Go to checkout process point where the payment method is selected
        self.render_payment_method_selection_screen(2)

        # Test rendering related admin interface pages and hope to catch all raised exceptions
        self.render_admin()

    def test_bad_view_definition(self):
        """ Try refering non-existing browser:page in payment processor """
        bad_button_configure_zcml = '''
        <configure
            xmlns="http://namespaces.zope.org/zope"
            xmlns:five="http://namespaces.zope.org/five"
            xmlns:paymentprocessors="http://namespaces.plonegetpaid.com/paymentprocessors"
            xmlns:browser="http://namespaces.zope.org/browser"
            i18n_domain="foo">

            <paymentprocessors:registerProcessor
               name="Dummy Processor"
               pay_view="dummy_payment_processor_thank_you_page"
               selection_view="BAD_ENTRY_HERE"
               thank_you_view="dummy_payment_processor_thank_you_page"
               />

        </configure>'''
        zcml.load_string(bad_button_configure_zcml)
        self.portal.portal_properties.payment_processor_properties.enabled_processors = [ "Dummy Processor" ]
        try:
            self.render_payment_method_selection_screen(1)
            raise AssertionError("Should not be never reached")
        except BadViewConfigurationException:
            pass

    def test_choose_available_payment_processors(self):
        """ Test admin page where you can enabled different payment processors on the site """
        self.loadDummyZCML(dummy_processors.configure_zcml)
        self.loginAsPortalOwner()

        # Do fake POST
        request = self.portal.REQUEST
        request["REQUEST_METHOD"] = "POST"
        request["active-payment-processors"] =["Dummy Processor"]

        view = self.portal.restrictedTraverse("@@manage-getpaid-payment-processor")
        view()
        self.assertEqual(self.portal.portal_properties.payment_processor_properties.enabled_processors, ["Dummy Processor"])

    def test_settings_view(self):
        """ Render settings view for an payment processor. """
        self.loadDummyZCML(dummy_processors.configure_zcml)
        self.loginAsPortalOwner()
        self.portal.restrictedTraverse("@@dummy_payment_processor_settings")

    def test_payment(self):
        """ Walk through payment processor.

        Open wizard payment method selection page and simulate payment method selection.
        """
        self.enable_processor()

        view = self.get_payment_method_selection_screen()
        html = view()

        self.assertTrue('<input name="payment-method" type="radio" value="Dummy Processor">' in html) # Check that payment processor button is rendered there

        # Now simulate POST
        request = self.portal.REQUEST
        request["REQUEST_METHOD"] = "POST"
        request["payment_method"] = 'Dummy Processor' # <button> submit

        view = self.get_payment_method_selection_screen()

        # Now we should contain the payment data in the wizard
        step = "checkout-review-pay"
        self.portal.REQUEST["cur_step"] = step # See _wizard.pt
        wizard = self.portal.restrictedTraverse("@@getpaid-checkout-wizard")
        view = wizard.controller.getCurrentStep()

        # Check that input is as a hidden field on the page
        html = view()
        print html

        storage = wizard.data_manager.adapters[IPaymentMethodInformation]

        import pdb ; pdb.set_trace()
        entry = wizard.data_manager.get("payment_method")
        self.assertEqual(entry, "Dummy Processor")

def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestPaymentMethods))
    return suite
