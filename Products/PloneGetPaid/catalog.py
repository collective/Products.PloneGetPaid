# Make sure that catalog brains can have a 'price' attribute.

from getpaid.core.interfaces import IPayable
from Products.CMFPlone import CatalogTool
from Products.PloneGetPaid.interfaces import IPayableMarker

try:
    # Plone 3.3*
    from plone.indexer.decorator import indexer


    @indexer(IPayable)
    def get_price(object):
        if not IPayableMarker.providedBy(object):
            return None
        adapted = IPayable(object, None)
        if adapted is not None:
            return adapted.price
        return None

except ImportError:
    # Plone 3.2.x code

    def get_price(object, portal, **kw):
        if not IPayableMarker.providedBy(object):
            return None
        adapted = IPayable(object, None)
        if adapted is not None:
            return adapted.price
        return None

    CatalogTool.registerIndexableAttribute('price', get_price)
