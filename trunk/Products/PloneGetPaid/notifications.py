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

customer_new_order_template = '''\
To: ${to_email}
From: "${from_name}" <${from_email}>
Subject: New Order Notification

Thank you for you order.

Total Amount to be Charged : ${total_price}

You can view the status of your order here

${store_url}/@@getpaid-order/${order_id}

Order Contents

${order_contents}

'''

anonymous_customer_new_order_template = '''\
To: ${to_email}
From: "${from_name}" <${from_email}>
Subject: New Order Notification

Thank you for you order.

Total Amount to be Charged : ${total_price}

Order Contents

${order_contents}

'''

class CustomerOrderNotificationMessage(object):

    interface.implements(interfaces.INotificationMailMessage)

    __call__ = customer_new_order_template

    def __call__(self, settings, store_url, order_contents):
        kwargs = {'to_email': self.order.contact_information.email,
                  'from_name': settings.store_name,
                  'from_email': settings.contact_email,
                  'total_price': u"%0.2f" % self.order.getTotalPrice(),
                  'store_url': store_url,
                  'order_id': self.order.order_id,
                  'order_contents': order_contents,
                 }
        portal = getPortal()
        pm = getToolByName(portal, 'portal_membership')
        user = pm.getAuthenticatedMember()
        if 'Anonymous' in user.getRoles():
            msg = _(anonymous_customer_new_order_template, mapping=kwargs)
        else:
            msg = _(customer_new_order_template, mapping=kwargs)
        return translate(msg)

    def __init__( self, order ):
        self.order = order

merchant_new_order_template = '''\
To: ${to_email}
From: "${from_name}" <${from_email}>
Subject: New Order Notification

A New Order has been created

Total Cost: ${total_price}

To continue processing the order follow this link:
${store_url}/@@admin-manage-order/${order_id}/@@admin

Order Contents

${order_contents}

'''


class MerchantOrderNotificationMessage( object ):

    interface.implements(interfaces.INotificationMailMessage)

    __call__ = merchant_new_order_template
    
    def __call__(self, settings, store_url, order_contents):
        kwargs = {'to_email': settings.contact_email,
                  'from_name': settings.store_name,
                  'from_email': settings.contact_email,
                  'total_price': u"%0.2f" % self.order.getTotalPrice(),
                  'store_url': store_url,
                  'order_id': self.order.order_id,
                  'order_contents': order_contents,
                 }
        msg = _(merchant_new_order_template, mapping=kwargs)
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

    For now we only send out notifications when an order initially becomes
    chargeable. We may not raise or pass exceptions: the payment has already
    happened and everything else is our, not the customer's fault.
    """
    portal = getPortal()
    mailer = getToolByName(portal, 'MailHost')
    
    if event.destination != workflow_states.order.finance.CHARGEABLE:
        return
    
    if not event.source in ( workflow_states.order.finance.REVIEWING,
                             workflow_states.order.finance.PAYMENT_DECLINED ):
        return 
    
    settings = interfaces.IGetPaidManagementOptions( portal )
    store_url = portal.absolute_url()
    order_contents = u'\n'.join([u' '.join((str(cart_item.quantity),
                                  cart_item.name,
                                  u"@%0.2f" % (cart_item.cost,),
                                  'total: US$%0.2f' % (cart_item.cost*cart_item.quantity,),
                                )) for cart_item in order.shopping_cart.values()])
    if settings.merchant_email_notification == 'notification' \
       and settings.contact_email:

        template = component.getAdapter(order, interfaces.INotificationMailMessage, "merchant-new-order")
        message = template(settings, store_url, order_contents)
        try:
            mailer.send(str(message))
        except:
            # Something happened and most probably we weren't able to send the
            # message. That's bad, but we got the money already and really
            # should do the shipment
            # XXX: somebody should be notified about that
            pass


    if settings.customer_email_notification == 'notification':
        email = order.contact_information.email
        if email:
            template = component.getAdapter( order, interfaces.INotificationMailMessage, "customer-new-order")
            message = template(settings, store_url, order_contents)
            try:
                mailer.send(str(message))
            except:
                # Something happened and most probably we weren't able to send the
                # message. That's bad, but we got the money already and really
                # should do the shipment
                # XXX: somebody should be notified about that
                pass

    

