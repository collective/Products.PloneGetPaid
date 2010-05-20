"""
email notifications for store admins and customers.
"""

from zope import component, interface
from zope.app import zapi
from getpaid.core.interfaces import workflow_states
from Products.CMFCore.utils import getToolByName

import interfaces

from DocumentTemplate.DT_HTML import HTML

from interfaces import _
from zope.i18n import translate

class MerchantOrderNotificationMessage( object ):

    interface.implements(interfaces.INotificationMailMessage)

    def __call__(self, settings, store_url, order_contents, template):
        kwargs = {'to_email': settings.contact_email,
                  'from_name': settings.store_name,
                  'from_email': settings.contact_email,
                  'total_price': u"%0.2f" % self.order.getTotalPrice(),
                  'shipping_cost': u"%0.2f" % self.order.getShippingCost(),
                  'store_url': store_url,
                  'order_id': self.order.order_id,
                  'order_contents': order_contents,
                 }
        msg = _(template, mapping=kwargs)

        return translate(msg)
    
    def __init__( self, order ):
        self.order = order

class CustomerOrderNotificationMessage(object):

    interface.implements(interfaces.INotificationMailMessage)

    def __call__(self, settings, store_url, order_contents, template):

        portal = getPortal()
        pm = getToolByName(portal, 'portal_membership')
        user = pm.getAuthenticatedMember()
        if 'Anonymous' not in user.getRoles():
            view_order = '''\
You can view the status of your order here

${store_url}/@@getpaid-order/${order_id}
'''

            kwargs = {
                     'view_order_information': view_order
                     }
            temp = _(template, 
                     mapping=kwargs)
            template = translate(temp)


        kwargs = {'to_email': self.order.contact_information.email,
                  'from_name': settings.store_name,
                  'from_email': settings.contact_email,
                  'total_price': u"%0.2f" % self.order.getTotalPrice(),
                  'shipping_cost': u"%0.2f" % self.order.getShippingCost(),
                  'store_url': store_url,
                  'order_id': self.order.order_id,
                  'order_contents': order_contents,
                  'view_order_information': ''
                 }

        msg = _(template, mapping=kwargs)

        return translate(msg)

    def __init__( self, order ):
        self.order = order


def getPortal( ):
    site = component.getSiteManager()
    try:
        portal = getToolByName(site, 'portal_url').getPortalObject()
    except AttributeError:
        # BBB for Zope 2.9
        portal = site.context
    return portal
    
def sendNotification( order, event ):
    """ sends out email notifications to merchants and clients based on settings.

    We may not raise or pass exceptions: the payment has already
    happened and everything else is our, not the customer's fault.
    """
    portal = getPortal()
    mailer = getToolByName(portal, 'MailHost')

    settings = interfaces.IGetPaidManagementOptions( portal )
    store_url = portal.absolute_url()
    properties = getToolByName(portal, 'portal_properties')
    encoding = properties.site_properties.default_charset
    order_contents = u'\n'.join([u' '.join((str(cart_item.quantity),
                                  cart_item.name.decode(encoding),
                                  u"@%0.2f" % (cart_item.cost,),
                                  'total: US$%0.2f' % (cart_item.cost*cart_item.quantity,),
                                )) for cart_item in order.shopping_cart.values()])

    # Auth
    if event.destination == workflow_states.order.finance.CHARGEABLE and \
            event.source in ( workflow_states.order.finance.REVIEWING,
                              workflow_states.order.finance.PAYMENT_DECLINED ):

        if settings.send_merchant_auth_notification and \
                settings.contact_email:
            sendMerchantEmail("merchant-new-order",
                              settings.merchant_auth_email_notification_template,
                              settings,
                              order,
                              store_url,
                              order_contents,
                              mailer)

        if settings.send_customer_auth_notification:
            sendCustomerEmail("customer-new-order",
                              settings.customer_auth_email_notification_template,
                              settings,
                              order,
                              store_url,
                              order_contents,
                              mailer)
    # Charged
    if event.destination == workflow_states.order.finance.CHARGED and \
            event.source == workflow_states.order.finance.CHARGING:

        if settings.send_merchant_charge_notification and \
                settings.contact_email:
            sendMerchantEmail("merchant-charge-order",
                              settings.merchant_charge_email_notification_template,
                              settings,
                              order,
                              store_url,
                              order_contents,
                              mailer)

        if settings.send_customer_charge_notification:
            sendCustomerEmail("customer-charge-order",
                              settings.customer_charge_email_notification_template,
                              settings,
                              order,
                              store_url,
                              order_contents,
                              mailer)

    # Decline
    if event.destination == workflow_states.order.finance.PAYMENT_DECLINED and \
            event.source in ( workflow_states.order.finance.CHARGING,
                              workflow_states.order.finance.REVIEWING ):

        if settings.send_merchant_decline_notification and \
                settings.contact_email:
            sendMerchantEmail("merchant-decline-order",
                              settings.merchant_decline_email_notification_template,
                              settings,
                              order,
                              store_url,
                              order_contents,
                              mailer)

        if settings.send_customer_decline_notification:
            sendCustomerEmail("customer-decline-order",
                              settings.customer_decline_email_notification_template,
                              settings,
                              order,
                              store_url,
                              order_contents,
                              mailer)

def sendMerchantEmail(adapterName, template, settings, order, 
                      store_url, order_contents, mailer):

    adapter = component.getAdapter(order, 
                                   interfaces.INotificationMailMessage, 
                                   adapterName)
    message = adapter(settings, store_url, order_contents, template)

    try:
        mailer.send(str(message))
    except:
        # Something happened and most probably we weren't able to send the
        # message. That's bad, but we got the money already and really
        # should do the shipment
        # XXX: somebody should be notified about that
        pass


def sendCustomerEmail(adapterName, template, settings, order, 
                      store_url, order_contents, mailer):

    email = order.contact_information.email
    if email:
        adapter = component.getAdapter( order, 
                                        interfaces.INotificationMailMessage, 
                                        adapterName)

        message = adapter(settings, store_url, order_contents, template)
        try:
            mailer.send(str(message))
        except:
            # Something happened and most probably we weren't able to send the
            # message. That's bad, but we got the money already and really
            # should do the shipment
            # XXX: somebody should be notified about that
            pass
