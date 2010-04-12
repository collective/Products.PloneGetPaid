"""Integration tests for donations.
"""
from base import PloneGetPaidTestCase
import getpaid.core.interfaces as igetpaid
from zope.schema import getFieldNames, getFields
from zope.schema import Field, Set, Int

from zope.schema.interfaces import NotAContainer, RequiredMissing
from zope.schema.interfaces import WrongContainedType, WrongType, NotUnique
from zope.schema.interfaces import TooShort, TooLong

from zope import component

class TestCreateDonation(PloneGetPaidTestCase):

    def testHaveFields(self):
        """ Set and check IDonatableMarker schema """
        for f in ('product_code', 'price', 'donation_text', 'made_payable_by'):
            self.failUnless(f in getFieldNames(igetpaid.IDonationContent))

        #sample for one field
        donatable_fields = getFields(igetpaid.IDonationContent)        
        fieldDonationText = donatable_fields['donation_text']
        self.assertRaises(RequiredMissing, fieldDonationText.validate, None)
        
    def testDonationProcess(self):
        from zope.interface import alsoProvides
        from Products.Five.utilities.marker import mark
        from Products.PloneGetPaid.interfaces import IDonatableMarker
        from getpaid.core.interfaces import IDonationContent
        from zope.publisher.browser import TestRequest

        self.setRoles(('Manager',))
        id = self.portal.invokeFactory('Document', 'page-to-donate')
        donation = self.portal.restrictedTraverse('page-to-donate')
        alsoProvides(donation, IDonatableMarker)
        
        #request = TestRequest()
        payable = IDonationContent( donation ) 

        payable.setProperty('donation_text','description')
        self.failUnless(payable.donation_text == 'description')

        # XXX how do we test validation and required?
        #   for example, price should only accept a float
        payable.setProperty('price','description')
        self.failUnless(payable.donation_text == 'description')

def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestCreateDonation))
    return suite
