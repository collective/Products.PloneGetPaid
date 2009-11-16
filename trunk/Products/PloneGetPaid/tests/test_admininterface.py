"""Unit tests for setting admin interface options.
"""

from unittest import TestSuite, makeSuite
from base import PloneGetPaidTestCase
from getpaid.core.payment import CREDIT_CARD_TYPES
from Products.PloneGetPaid import interfaces, vocabularies
from Products.CMFCore.utils import getToolByName
from zope.interface import alsoProvides

class testAdminInterface(PloneGetPaidTestCase):
    
    def afterSetUp(self):
        super(testAdminInterface, self).afterSetUp()
        self.manage_options = interfaces.IGetPaidManagementOptions( self.portal )
        self.setRoles(('Manager',))

    def testSetupPaymentProcessor( self ):
        """Test setting a payment processor."""
        #get the list of payment processors and get the first processor in the list
        our_payment_processor = "Google Checkout"
        self.manage_options.payment_processor = [our_payment_processor]
        self.failUnless(our_payment_processor in self.manage_options.payment_processor)


    def testSetupCurrency( self ):
        """Test setting a currency."""
        #set the currency in the GetPaid admin options to US
        our_currency = "US"
        self.manage_options.currency = [our_currency]
        #test to see if it was set properly
        self.failUnless(our_currency in self.manage_options.currency)


    def testSetupDisclaimer( self ):
        """Test setting a disclaimer."""
        our_disclaimer = "This is a disclaimer"
        self.manage_options.disclaimer = [our_disclaimer]
        #test to see if it was set properly
        self.failUnless(our_disclaimer in self.manage_options.disclaimer)

    def testSetupShipping( self ):
        """Test setting a shipping method."""
        our_shipping_method = "UPS"
        self.manage_options.shipping_method = [our_shipping_method]
        #test to see if it was set properly
        self.failUnless(our_shipping_method in self.manage_options.shipping_method)

    def testSetupTax( self ):
        """Test setting tax rate."""
        our_tax_method = "Flat Rate"
        self.manage_options.tax_method = [our_tax_method]
        #test to see if it was set properly
        self.failUnless(our_tax_method in self.manage_options.tax_method)

    def testSetupDiscounts( self ):
        """Test setting up discounts."""
        our_discounts = "10%"
        self.manage_options.discounts = [our_discounts]
        #test to see if it was set properly
        self.failUnless(our_discounts in self.manage_options.discounts)

    def testSetupCreditcards( self ):
        """Test setting acceptable credit cards."""
        # Test default value
        self.assertEqual(
            self.manage_options.getProperty('credit_cards'), CREDIT_CARD_TYPES)
        our_credit_card = u"Visa"
        self.manage_options.setProperty('credit_cards', [our_credit_card])
        #test to see if it was set properly
        self.assertEqual([our_credit_card], 
            self.manage_options.getProperty('credit_cards'))

def test_suite():
    suite = TestSuite()
    suite.addTest(makeSuite(testAdminInterface))
    return suite
