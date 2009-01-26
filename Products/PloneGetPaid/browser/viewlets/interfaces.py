from zope.viewlet.interfaces import IViewletManager

class IBelowCartListing(IViewletManager):
    """A viewlet manager that sits below the cart listing
    """
    
class IBelowCartResume(IViewletManager):
    """A viewlet manager that sits below the cart resume
    """

class IBelowCartThankYou(IViewletManager):
    """A viewlet manager that sits below the cart thank you page
    """
