
import random, string
from getpaid.core import cart, order, interfaces, item
from Products.PloneGetPaid.interfaces import IGetPaidManagementOptions
from zope import component

def createOrders( self ):

    manager = component.getUtility( interfaces.IOrderManager )

    # make sure we don't accidentally create notifications for sample orders

    settings = IGetPaidManagementOptions( self )
    m_a_value = settings.send_merchant_auth_notification
    c_a_value = settings.send_customer_auth_notification

    m_c_value = settings.send_merchant_charge_notification
    c_c_value = settings.send_customer_charge_notification

    m_d_value = settings.send_merchant_decline_notification
    c_d_value = settings.send_customer_decline_notification

    settings.send_merchant_auth_notification = False
    settings.send_customer_auth_notification = False

    settings.send_merchant_charge_notification = False
    settings.send_customer_charge_notification = False

    settings.send_merchant_decline_notification = False
    settings.send_customer_decline_notification = False

    for i in range(40, 60):
        o = order.Order()
        o.order_id = str(i)

        o.shopping_cart = sc = cart.ShoppingCart()

        for i in range(0, 10):
            myItem = item.LineItem()
            myItem.name = "p%s"%random.choice( string.letters )
            myItem.quantity = random.randint(1,25)
            myItem.cost = random.randint(30, 100)
            myItem.item_id = "i%s"%random.choice( string.letters )
            if myItem.item_id in sc:
                continue
            sc[myItem.item_id] = myItem

        o.user_id = "u%s"%random.choice( string.letters )
        o.finance_workflow.fireTransition('create')
        o.fulfillment_workflow.fireTransition('create')

        manager.store( o )

    settings.send_merchant_auth_notification = m_a_value
    settings.send_customer_auth_notification = c_a_value

    settings.send_merchant_charge_notification = m_c_value
    settings.send_customer_charge_notification = c_c_value

    settings.send_merchant_decline_notification = m_d_value
    settings.send_customer_decline_notification = c_d_value

    return "Created 20 Orders"

