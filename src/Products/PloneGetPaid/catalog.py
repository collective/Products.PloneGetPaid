# Make sure that catalog brains can have a 'price' attribute.

from getpaid.core.interfaces import IPayable
from Products.CMFPlone import CatalogTool
from Products.PloneGetPaid.interfaces import IPayableMarker


def get_price(object, portal, **kw):
    if not IPayableMarker.providedBy(object):
        return None
    adapted = IPayable(object, None)
    if adapted is not None:
        return adapted.price
    return None

CatalogTool.registerIndexableAttribute('price', get_price)
