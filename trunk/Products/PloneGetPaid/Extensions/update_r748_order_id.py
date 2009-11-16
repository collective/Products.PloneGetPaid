"""
only use this as upgrade to revision 748 if your experiencing key errors
when looking at the order management screens
"""

import random
from getpaid.core import interfaces
from zope import component

def generate_oid( ):
    return random.randint( 2**10, 2**30 ) 

def order_id_upgrade( self ):
    manager = component.getUtility( interfaces.IOrderManager )    
    orders = list( manager.storage.items() )
    for oid,o in orders:
        n_oid = generate_oid()
        o._order_id = str( n_oid )
        del manager.storage[ oid ]
        manager.store( o )

    return "Updated %s Order Ids "%( len( manager.storage) )
 
        
