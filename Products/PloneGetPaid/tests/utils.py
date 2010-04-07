import doctest

from zope.app.testing import placelesssetup

from zope.configuration.xmlconfig import XMLConfig

# Standard options for DocTests
optionflags =  (doctest.ELLIPSIS |
                doctest.NORMALIZE_WHITESPACE |
                doctest.REPORT_ONLY_FIRST_FAILURE)


def configurationSetUp(self):
    """Set up Zope 3 test environment
    """
    
    placelesssetup.setUp()
    
    # Ensure that the ZCML registrations in PloneGetPaid are in effect
    # Also ensure the Five directives and permissions are available
    
    import Products.Five
    import Products.PloneGetPaid
    
    XMLConfig('configure.zcml', Products.Five)()
    XMLConfig('meta.zcml', Products.Five)()
    
    XMLConfig('configure.zcml', Products.PloneGetPaid)()
    
def configurationTearDown(self):
    """Tear down Zope 3 test environment
    """
    
    placelesssetup.tearDown()
