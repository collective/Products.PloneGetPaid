from zope import component, schema, interface
from zope.location.interfaces import ILocation
from getpaid.core import options, interfaces
#from Products.CMFPlone.utils import getSiteEncoding


class ContactInfo(options.PersistentBag):
    title = "Contact Information"
    interface.implements(ILocation)
    __parent__ = None
    __name__ = None


ContactInfo.initclass(interfaces.IUserContactInformation)


class ShipAddressInfo(options.PersistentBag):
    title = "Shipping Information"
    interface.implements(ILocation)
    __parent__ = None
    __name__ = None


ShipAddressInfo.initclass(interfaces.IShippingAddress)


class BillAddressInfo(options.PersistentBag):
    title = "Payment Information"
    interface.implements(ILocation)
    __parent__ = None
    __name__ = None

BillAddressInfo.initclass(interfaces.IBillingAddress)


def lastShipAddress(user):
    order_manager = component.getUtility(interfaces.IOrderManager)
    orders = order_manager.query(user_id=user.getId())
    if not orders:
        return
    last_info = orders[0].shipping_address
    info = ShipAddressInfo()
    field_map = schema.getFields(interfaces.IShippingAddress)
    for n, f in field_map.items():
        f.set(info, f.query(last_info, f.default))
    return info


def lastBillAddress(user):
    order_manager = component.getUtility(interfaces.IOrderManager)
    orders = order_manager.query(user_id=user.getId())
    if not orders:
        return
    last_info = orders[0].billing_address
    info = BillAddressInfo()
    field_map = schema.getFields(interfaces.IBillingAddress)
    for n, f in field_map.items():
        f.set(info, f.query(last_info, f.default))
    return info


def lastOrderContactInfo(user):
    order_manager = component.getUtility(interfaces.IOrderManager)
    orders = order_manager.query(user_id=user.getId())
    if not orders:
        return
    last_info = orders[0].contact_information
    info = ContactInfo()
    field_map = schema.getFields(interfaces.IUserContactInformation)
    for n, f in field_map.items():
        f.set(info, f.query(last_info, f.default))
    return info


def memberContactInformation(user):
    """
    adapt a member to contact information, based on thier settings
    we assume a default user from a plone site, and check first
    if they have any previous orders, and use the last values, else
    we try to fetch from member properties
    """
    info = lastOrderContactInfo(user)
    if info:
        return info

    # go from the user to the site via a user containment acquisition
    # (user, userfolder, container)
    store = user.aq_inner.aq_parent.aq_parent
    if not interfaces.IStore.providedBy(store):
        return None

    order_manager = component.getUtility(interfaces.IOrderManager)
    orders = order_manager.query(user_id=user.getId())
    if not orders:
        return
    last_info = orders[0].contact_information
    info = ContactInfo()
    field_map = schema.getFields(interfaces.IUserContactInformation)
    for n, f in field_map.items():
        f.set(info, f.query(last_info, f.default))

    # get a member which will properly wrap up a user in a member object
    member = store.portal_membership.getMemberById(user.getId())

    # get contact information for default members from settings
    email = member.getProperty('email')
    name = member.getProperty('fullname')

    info = ContactInfo()
    info.email = unicode(email, "utf-8")
    info.name = unicode(name, "utf-8")
    return info


def memberBillAddressInfo(user):
    info = lastBillAddress(user)
    if info:
        return info
    return memberBillAndShipAddressInfo(user, BillAddressInfo, 'bill')


def memberShipAddressInfo(user):
    info = lastShipAddress(user)
    if info:
        return info
    return memberBillAndShipAddressInfo(user, ShipAddressInfo, 'ship')


def memberBillAndShipAddressInfo(user, BillOrShipAddressInfo, objectName):
    """
    adapt a member to billing and shipping address information, based on their
    settings we assume a default user from a plone site
    """
    # go from the user to the site via a user containment acquisition
    # (user, userfolder, container)
    store = user.aq_inner.aq_parent.aq_parent
    if not interfaces.IStore.providedBy(store):
        return None

    # get a member which will properly wrap up a user in a member object
    member = store.portal_membership.getMemberById(user.getId())

    # get contact information for default members from settings
    address = member.getProperty('location')

    AddressInfo = BillOrShipAddressInfo()
    AddressInfo.__setattr__('%s_first_line' % objectName,
                            unicode(address, "utf-8"))

    return AddressInfo

#EOF
