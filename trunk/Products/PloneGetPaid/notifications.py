"""
email notifications for store admins and customers.
"""

__version__ = "$Revision$"
# $Id$
# $URL$

import logging

import csv

from email import message_from_string
from email.Header import Header
from StringIO import StringIO

from zope import component, globalrequest, interface, schema

from zope.i18n import translate

from plone.memoize import forever

from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import safe_unicode

from getpaid.core import interfaces
from getpaid.core.interfaces import workflow_states as wf

from Products.PloneGetPaid.interfaces import ICurrencyFormatter
from Products.PloneGetPaid.interfaces import IGetPaidManagementOptions
from Products.PloneGetPaid.interfaces import INotificationMailMessage

from Products.PloneGetPaid import _


class NotificationDialect(csv.Dialect):
    delimiter = ','
    doublequote = True
    escapechar = None
    lineterminator = '\r\n'
    quotechar = '"'
    quoting = csv.QUOTE_ALL
    skipinitialspace = True


class OrderNotificationBase(object):
    """ Base class for order notifications """

    interface.implements(INotificationMailMessage)

    message = None

    @property
    @forever.memoize
    def site(self):
        return component.getSiteManager()

    @property
    @forever.memoize
    def portal(self):
        return getToolByName(self.site, "portal_url").getPortalObject()

    @property
    @forever.memoize
    def settings(self):
        return IGetPaidManagementOptions(self.portal)

    @property
    @forever.memoize
    def default_charset(self):
        properties = getToolByName(self.portal, "portal_properties")
        default_charset = properties.get("site_properties").default_charset
        return default_charset

    @property
    def isAnonymousUser(self):
        mtool = getToolByName(self.portal, "portal_membership")
        return mtool.isAnonymousUser()

    def __str__(self):
        if getattr(self, "message"):
            return self.message.__str__()
        return super(OrderNotificationBase, self).__str__()

    def __init__(self, template, mapping):
        super(OrderNotificationBase, self).__init__()
        message = _(template, mapping=mapping)
        message = message_from_string(translate(message).encode(self.default_charset))
        message.replace_header("Subject", Header(message["Subject"], self.default_charset))
        message.set_charset(self.default_charset)
        self.message = message

    def getFormattedArguments(self, order):
        request = globalrequest.getRequest()
        currency = self.site.getUtility(ICurrencyFormatter)

        view_order = not self.isAnonymousUser and \
            u"\n".join((
                u"You can view the status of your order here",
                u"",
                u"${store_url}/@@getpaid-order/${order_id}"
                )) or ""

        return {
            'total_price': currency.format(self.portal, request, order.getTotalPrice()),
            'shipping_cost': currency.format(self.portal, request, order.getShippingCost()),
            'store_url': self.portal.absolute_url(),
            'order_id': order.order_id,
            'order_contents': self.getFormattedContents(order),
            'view_order_information': view_order,
            'contact_information': self.getFormattedBag(order, "contact_information"),
            'contact_information_csv': self.getFormattedBag(order, "contact_information", format="csv"),
            'billing_address': self.getFormattedBag(order, "billing_address"),
            'billing_address_csv': self.getFormattedBag(order, "billing_address", format="csv"),
            'shipping_address': self.getFormattedBag(order, "shipping_address"),
            'shipping_address_csv': self.getFormattedBag(order, "shipping_address", format="csv")
            }

    def getFormattedContents(self, order):
        request = globalrequest.getRequest()
        currency = self.site.getUtility(ICurrencyFormatter)
        return u"\n".join([u" ".join((str(i.quantity),
                                      i.name,
                                      u"@ %s" % currency.format(self.portal, request, i.cost),
                                      u"%s: %s" % (_(u"Total"), currency.format(self.portal, request, i.cost*i.quantity))))
                           for i in order.shopping_cart.values()])
    
    def getFormattedBag(self, order, name, format=None):
        schemas = component.getUtility(interfaces.IFormSchemas)
        bag = schemas.getBagClass(name)()
        data = getattr(order, name)
        values = [(getattr(field, "title"), getattr(data, name) or u"") \
                      for name, field in schema.getFieldsInOrder(bag.schema)]
        if format == "csv":
            output = StringIO()
            writer = csv.writer(output, dialect=NotificationDialect)
            # csv module doesn't support unicode, therefore we have to convert
            writer.writerow([v[0].encode('utf-8') for v in values]) # unicode -> utf-8
            writer.writerow([v[1].encode('utf-8') for v in values]) # unicode -> utf-8
            return unicode(output.getvalue(), 'utf-8') # utf-8 -> unicode
        else:
            return u"\n".join([u"%s: %s" % (i[0], i[1]) for i in values])


class MerchantNewOrderNotification(OrderNotificationBase):
    """ merchant-new-order """

    def __init__(self, order):
        kwargs = self.getFormattedArguments(order)
        kwargs.update({
                'to_name': str(Header(self.settings.store_name, self.default_charset)),
                'to_email': self.settings.contact_email,
                'from_name': str(Header(order.contact_information.name, self.default_charset)),
                'from_email': order.contact_information.email,
                })
        template = self.settings.merchant_auth_email_notification_template
        super(MerchantNewOrderNotification, self).__init__(template, mapping=kwargs)


class CustomerNewOrderNotification(OrderNotificationBase):
    """ customer-new-order """

    def __init__(self, order):
        kwargs = self.getFormattedArguments(order)
        kwargs.update({
                'to_name': str(Header(order.contact_information.name, self.default_charset)),
                'to_email': order.contact_information.email,
                'from_name': str(Header(self.settings.store_name, self.default_charset)),
                'from_email': self.settings.contact_email
                })
        template = self.settings.customer_auth_email_notification_template
        super(CustomerNewOrderNotification, self).__init__(template, mapping=kwargs)


class MerchantDeclineOrderNotification(OrderNotificationBase):
    """ merchant-decline-order """

    def __init__(self, order):
        kwargs = self.getFormattedArguments(order)
        kwargs.update({
                'to_name': str(Header(order.contact_information.name, self.default_charset)),
                'to_email': order.contact_information.email,
                'from_name': str(Header(self.settings.store_name, self.default_charset)),
                'from_email': self.settings.contact_email
                })
        template = self.settings.merchant_decline_email_notification_template
        super(MerchantDeclineOrderNotification, self).__init__(template, mapping=kwargs)


class CustomerDeclineOrderNotification(OrderNotificationBase):
    """ customer-decline-order """

    def __init__(self, order):
        kwargs = self.getFormattedArguments(order)
        kwargs.update({
                'to_name': str(Header(order.contact_information.name, self.default_charset)),
                'to_email': order.contact_information.email,
                'from_name': str(Header(self.settings.store_name, self.default_charset)),
                'from_email': self.settings.contact_email
                })
        template = self.settings.customer_decline_email_notification_template
        super(CustomerDeclineOrderNotification, self).__init__(template, mapping=kwargs)


class MerchantChargeOrderNotification(OrderNotificationBase):
    """ merchant-charge-order """

    def __init__(self, order):
        kwargs = self.getFormattedArguments(order)
        kwargs.update({
                'to_name': str(Header(order.contact_information.name, self.default_charset)),
                'to_email': order.contact_information.email,
                'from_name': str(Header(self.settings.store_name, self.default_charset)),
                'from_email': self.settings.contact_email
                })
        template = self.settings.merchant_charge_email_notification_template
        super(MerchantChargeOrderNotification, self).__init__(template, mapping=kwargs)


class CustomerChargeOrderNotification(OrderNotificationBase):
    """ customer-charge-order """

    def __init__(self, order):
        kwargs = self.getFormattedArguments(order)
        kwargs.update({
                'to_name': str(Header(order.contact_information.name, self.default_charset)),
                'to_email': order.contact_information.email,
                'from_name': str(Header(self.settings.store_name, self.default_charset)),
                'from_email': self.settings.contact_email
                })
        template = self.settings.customer_charge_email_notification_template
        super(CustomerChargeOrderNotification, self).__init__(template, mapping=kwargs)


def sendNotification(order, event):
    """ Sends out email notifications to merchants and clients based on settings.

    We may not raise or pass exceptions: the payment has already
    happened and everything else is our, not the customer's fault.
    """
    site = component.getSiteManager()
    portal = getToolByName(site, "portal_url").getPortalObject()
    settings = IGetPaidManagementOptions(portal)
    mailer = getToolByName(portal, 'MailHost')

    def notify(action):
        try:
            mailer.send(str(component.getAdapter(order, INotificationMailMessage, action)),
                        charset="utf-8")
        except Exception, e:
            logging.fatal("Notification failed for order %s: %s" % (order.order_id, str(e)))
        
    # Auth
    if event.destination == wf.order.finance.CHARGEABLE and \
            event.source in (wf.order.finance.REVIEWING,
                             wf.order.finance.PAYMENT_DECLINED):

        if settings.send_merchant_auth_notification and \
                settings.contact_email:
            notify("merchant-new-order")

        if settings.send_customer_auth_notification:
            notify("customer-new-order")

    # Charged
    if event.destination == wf.order.finance.CHARGED and \
            event.source == wf.order.finance.CHARGING:

        if settings.send_merchant_charge_notification and \
                settings.contact_email:
            notify("merchant-charge-order")

        if settings.send_customer_charge_notification:
            notify("customer-charge-order")

    # Decline
    if event.destination == wf.order.finance.PAYMENT_DECLINED and \
            event.source in (wf.order.finance.CHARGING,
                             wf.order.finance.REVIEWING):

        if settings.send_merchant_decline_notification and \
                settings.contact_email:
            notify("merchant-decline-order")

        if settings.send_customer_decline_notification:
            notify("customer-decline-order")
