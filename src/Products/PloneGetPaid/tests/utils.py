import doctest
from zope.app.tests import placelesssetup
from zope.configuration.xmlconfig import XMLConfig
from Products.PloneGetPaid.config import PLONE3

# Standard options for DocTests
optionflags =  (doctest.ELLIPSIS |
                doctest.NORMALIZE_WHITESPACE |
                doctest.REPORT_ONLY_FIRST_FAILURE)


def configurationSetUp(self):
    """Set up Zope 3 test environment
    """
    
    placelesssetup.setUp()
    
    # Ensure that the ZCML registrations in CMFonFive and PloneGetPaid are in effect
    # Also ensure the Five directives and permissions are available
    
    import Products.Five
    if not PLONE3:
        import Products.CMFonFive
    import Products.PloneGetPaid
    
    XMLConfig('configure.zcml', Products.Five)()
    XMLConfig('meta.zcml', Products.Five)()
    
    XMLConfig('configure.zcml', Products.PloneGetPaid)()
    
def configurationTearDown(self):
    """Tear down Zope 3 test environment
    """
    
    placelesssetup.tearDown()
