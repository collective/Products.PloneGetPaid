"""

    Multiple payment processors test cases.

"""
import os, sys
import unittest
import datetime

from zope import component
from zope.configuration.exceptions import ConfigurationError
from Products.Five import zcml

from base import PloneGetPaidTestCase
from getpaid.paymentprocessors.registry import BadViewConfigurationException, paymentProcessorRegistry
from getpaid.core.interfaces import IStore
from getpaid.core.order import Order
import getpaid.core.interfaces
import dummy_processors

from getpaid.paymentprocessors.interfaces import IPaymentMethodInformation
from zope.app.intid.interfaces import IIntIds

class TestPaymentMethods(PloneGetPaidTestCase):
    """ Test ZCML directives """

    def afterSetUp(self):
        PloneGetPaidTestCase.afterSetUp(self)
        paymentProcessorRegistry.clear()

        from Products.PloneGetPaid.interfaces import IGetPaidManagementOptions
        options = IGetPaidManagementOptions(self.portal)
        options.accepted_credit_cards = [ "visa" ]


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

        self.assertEqual(len(paymentProcessorRegistry.getProcessors()), 1)

    def enable_multiple_processors(self):
        """ Enable two dummy payment processor for testing.

        This means that there will be payment method selection.
        """
        self.loadDummyZCML(dummy_processors.configure_zcml)
        self.loadDummyZCML(dummy_processors.configure_zcml_2)
        self.portal.portal_properties.payment_processor_properties.enabled_processors = [ "Dummy Processor", "dummy2"]

        self.assertEqual(len(paymentProcessorRegistry.getProcessors()), 2)

    def render_admin(self):
        """ Test rendering admin interface views with the current paymentprocessor configuration. """

        # Render the page where you can choose which payment processor settings are managed

        self.loginAsPortalOwner()
        view = self.portal.restrictedTraverse("@@manage-getpaid-payment-processor")
        view()
        self.logout()


    def get_payment_method_selection_screen(self):
        """ Get the checkout payment method selection view via checkout wizard.

        Note you need to access view through wizard.update() so that
        data storages are updated properly.
        """

        # Force in checkout wizard step
        step = "checkout-payment-method"
        self.portal.REQUEST["cur_step"] = step # See _wizard.pt
        wizard = self.portal.restrictedTraverse("@@getpaid-checkout-wizard")

        view = wizard.controller.getCurrentStep()
        return wizard, view

    def render_payment_method_selection_screen(self, assertedProcessorCount):
        """ Test rendering payment method selection page in checkout wizard """

        wizard, view = self.get_payment_method_selection_screen()

        processors = view.getProcessors()
        self.assertEqual(len(processors), assertedProcessorCount)

        # Render payment method selection HTML - see that template doesn't raise an error
        # TODO: Check HTML output validy using functional tests
        return self.render_wizard_current_page(wizard)

    def render_wizard_current_page(self, wizard):
        """ Shortcut wizard to rendering the current wizard step.

        This bypasses security checks in browser.checkout.CheckoutWizard.__call__()

        """

        from getpaid.wizard.interfaces import IWizard
        assert IWizard.providedBy(wizard)

        from getpaid.wizard import Wizard
        return Wizard.__call__(wizard)

    def create_cart(self):
        """ Create a dummy shopping cart object filled with one item """
        from getpaid.core.item import PayableLineItem
        item = PayableLineItem()

        item.item_id = "event-devtalk-2007-1"
        item.name = "Event Registration"
        item.cost = 25.00
        item.quantity = 5
        item.description = "Development Talk"

        # need this reference ... needed by hacks in workflows

        iids = component.getUtility( IIntIds )

        iids.register(self.portal)
        item.uid = iids.getId(self.portal)

        cart = component.getUtility(getpaid.core.interfaces.IShoppingCartUtility).get(self.portal, create=True)
        cart[ item.item_id ] = item

        return cart

    def test_selection_screen_no_processor(self):
        """ See that the payment method selection screen fails if there is no payment methods available """

        # Go to checkout process point where the payment method is selected
        try:
            self.render_payment_method_selection_screen(0)
            raise AssertionError("This should be never reached")
        except RuntimeError:
            pass


    def xxx_test_selection_screen_one_processor(self):
        """ Test different count of site payment processors

        TODO: Payment method screen is not shown if there is only one processor.
        """
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
        """ Try refering non-existing browser:page in payment processor button configuration """

        bad_button_configure_zcml = '''
        <configure
            xmlns="http://namespaces.zope.org/zope"
            xmlns:five="http://namespaces.zope.org/five"
            xmlns:paymentprocessors="http://namespaces.plonegetpaid.com/paymentprocessors"
            xmlns:browser="http://namespaces.zope.org/browser"
            i18n_domain="foo">

            <paymentprocessors:registerProcessor
               name="Bad Dummy Processor"
               i18n_name="Foobar"
               review_pay_view="checkout-review-pay"
               selection_view="BAD_ENTRY_HERE"
               thank_you_view="dummy_payment_processor_thank_you_page"
               />

            <paymentprocessors:registerProcessor
               name="Bad Dummy Processor 2"
               i18n_name="Foobar 2"
               review_pay_view="checkout-review-pay"
               selection_view="BAD_ENTRY_HERE"
               thank_you_view="dummy_payment_processor_thank_you_page"
               />


        </configure>'''
        zcml.load_string(bad_button_configure_zcml)
        self.portal.portal_properties.payment_processor_properties.enabled_processors = [ "Bad Dummy Processor", "Bad Dummy Processor 2" ]
        try:
            html = self.render_payment_method_selection_screen(2)
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

    def xxx_test_skip_choose_payment_method_if_one_processor(self):
        """ When only one payment processor is active, the checkout wizard should skip the payment processor selection screen. """

        # TODO: getNextStep() logic is broken in getpaid.wizard

        self.enable_processor()

        # Now we should contain the payment data in the wizard
        step = "checkout-select-shipping"
        self.portal.REQUEST["cur_step"] = step # See _wizard.pt
        wizard = self.portal.restrictedTraverse("@@getpaid-checkout-wizard")

        print "Checking the step"
        after_shipping = wizard.controller.getNextStepName(step)
        self.assertEqual(after_shipping, 'checkout-review-pay')

    def xxx_test_show_payment_methods_if_multiple_processors(self):


        # TODO: getNextStep() logic is broken in getpaid.wizard

        self.enable_multiple_processors()
        return
        # Now we should contain the payment data in the wizard
        step = "checkout-review-pay"
        self.portal.REQUEST["cur_step"] = step # See _wizard.pt
        wizard = self.portal.restrictedTraverse("@@getpaid-checkout-wizard")

        after_shipping = wizard.controller.getNextStepName("checkout-select-shipping")
        self.assertEqual(after_shipping, 'checkout-review-pay')

    def test_register_review_pay_page(self):
        """ Test review and pay page look up
        """

        self.enable_multiple_processors()
        wizard, view = self.get_payment_method_selection_screen()

        # Raises ComponentLookUpError if fails
        step = component.getMultiAdapter((wizard.context, wizard.request), name="dummy_payment_processor_review_pay")

    def choose_payment(self):
        """ Use wizard to choose and store active payment method """
        self.enable_multiple_processors()

        wizard, view = self.get_payment_method_selection_screen()

        html = self.render_wizard_current_page(wizard)

        self.assertTrue('value="Dummy Processor"' in html) # Check that payment processor button is rendered there

        # Payment method should be None until it is set for the first time
        # - we are arriving for the page so currently it should be unset
        entry = wizard.getActivePaymentProcessor()
        self.assertEqual(entry, None)

        # Now simulate POST
        request = self.portal.REQUEST
        request["REQUEST_METHOD"] = "POST"
        request.form["form.payment_processor"] = 'Dummy Processor' # radio button selection
        request.form["form.actions.continue"] = "Continue" # The user wants to proceed

        wizard, view = self.get_payment_method_selection_screen()

        html = self.render_wizard_current_page(wizard) # Simulate the form POST

        for error in view.errors:
            raise AssertionError("Form submit had error:" + str(error))

        return wizard

    def test_choose_payment_method(self):
        """ Walk through payment processor.

        Open wizard payment method selection page and simulate payment method selection.
        """

        wizard = self.choose_payment()

        # Check that transient bag got updated
        storage = wizard.data_manager.adapters[IPaymentMethodInformation]
        entry = storage.payment_processor
        self.assertEqual(entry, u"Dummy processor")

        # Now we should contain the payment data in the wizard
        step = "checkout-review-pay"
        self.portal.REQUEST["cur_step"] = step # See _wizard.pt
        wizard = self.portal.restrictedTraverse("@@getpaid-checkout-wizard")
        html = self.render_wizard_current_page(wizard) # Simulate the form POST

        # Check that we have payment method as a stored value
        entry = wizard.getActivePaymentProcessor()
        self.assertEqual(entry, u"Dummy processor")

        # Check that we are rendering paymeny processor specific review and pay View
        step = wizard.controller.getCurrentStep()
        self.assertTrue(isinstance(step, dummy_processors.DummyReviewAndPay))

        # Check that input is as a hidden <input> field on the page
        self.assertTrue('value="Dummy Processor"' in html) # Check that payment processor button is rendered there

        # See that we have rendered the dummy payment processor view
        self.assertTrue("This is a dummy payment method, can't pay anything here" in html) # Check that payment processor button is rendered there


    def test_make_payment(self):
        """ """

        wizard = self.choose_payment()

        # Now we should contain the payment data in the wizard
        step = "checkout-review-pay"
        self.portal.REQUEST["cur_step"] = step # See _wizard.pt
        wizard = self.portal.restrictedTraverse("@@getpaid-checkout-wizard")

        request = self.portal.REQUEST

        request["REQUEST_METHOD"] = "POST"

        # Hidden inputs
        request.form["form.payment_processor"] = 'Dummy Processor'

        # Active inputs - see getpaid.core.interfaces.IUserPaymentInformation
        request.form["form.name_on_card"] = "Foo" # The user wants to proceed
        request.form["form.credit_card"] = "4024007132557926" # spoofed
        request.form["form.credit_card_type"] = "visa" # The user wants to proceed
        request.form["form.cc_expiration"] = datetime.datetime.now()
        request.form["form.cc_cvc"] = "123"

        # Actions
        request.form["form.actions.make-payment"] = "Make Payment"

        # TODO: Not sure which order/cart initialization steps are necessary
        # Create fake order
        order_manager = component.getUtility(getpaid.core.interfaces.IOrderManager)
        order = Order()
        order.order_id = order_manager.newOrderId()

        #
        self.create_cart()

        #order_manager.store( order )
        request.form["order_id"] = order.order_id

        # Simulate POST
        # This should trigger makePayment()
        html = self.render_wizard_current_page(wizard) # Simulate the form POST

        view = wizard.controller.getCurrentStep()
        for error in view.errors:
            # Check that form validation did not fail
            raise AssertionError("Form submit had error:" + str(error))

        self.assertEqual(dummy_processors.DummyProcessor.authorized, 1) # One makePayment completed

def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestPaymentMethods))
    return suite
