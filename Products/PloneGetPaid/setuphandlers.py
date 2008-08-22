from StringIO import StringIO

from Products.PloneGetPaid.Extensions.install import install_dependencies
from Products.PloneGetPaid.Extensions.install import install_cart_portlet 
from Products.PloneGetPaid.Extensions.install import install_contentwidget_portlet
from Products.PloneGetPaid.Extensions.install import notify_install
from Products.PloneGetPaid.Extensions.install import notify_uninstalled
from Products.PloneGetPaid.Extensions.install import setup_site
from Products.PloneGetPaid.Extensions.install import setup_store
from Products.PloneGetPaid.Extensions.install import setup_software_generation
from Products.PloneGetPaid.Extensions.install import setup_order_manager
from Products.PloneGetPaid.Extensions.install import add_intids
from Products.PloneGetPaid.Extensions.install import install_plone3_portlets
from Products.PloneGetPaid.Extensions.install import setup_payment_options
from Products.PloneGetPaid.Extensions.install import register_shopping_cart_utility

from Products.PloneGetPaid.Extensions.install import setup_addressbook
from Products.PloneGetPaid.Extensions.install import setup_settings
from Products.PloneGetPaid.Extensions.install import register_shopping_cart_utility

from Products.PloneGetPaid.config import PLONE3

def setupVarious(context):
    """Import steps that are not handled by GS import/export handlers can be
    defined in the setupVarious() function.
    See Products.GenericSetup.context.BaseContext to see what you can do with
    ``context`` (the function argument).
    For instance, it is possible to get the Plone Site object:
    ``site = context.getSite()``
    """
    if context.readDataFile('PloneGetPaid.setupVarious.txt') is None:
        return

    # Now do something useful
    site = context.getSite()

    logger = context.getLogger("PloneGetPaid")
    out = StringIO()

    print >> out, "Installing Cart Portlet"
    install_cart_portlet(site)

    print >> out, "Installing Content Widget Portlet"
    install_contentwidget_portlet(site)

    if PLONE3:
        print >> out, "Installing Plone 3 Portlets"
        install_plone3_portlets(site)
    
    print >> out, "Installing Local Site"
    setup_site(site)
    
    print >> out, "Installing Store Marker Interface"
    setup_store(site)
    
    print >> out, "Installing Store Settings Utility"
    setup_settings(site)
    
    print >> out, "Configure default payment options"
    setup_payment_options( site )
    
    print >> out, "Installing Order Local Utility"
    setup_order_manager(site)
    
    print >> out, "Installing Address Book Utility"
    setup_addressbook( site )        
    
    print >> out, "Configure default payment options"
    setup_payment_options(site)
    
    print >> out, "Installing IntId Utility"
    add_intids(site)
    
    print >> out, "Setting up update facility"
    setup_software_generation( site )
    
    print >> out, "Registering shopping cart utility"
    register_shopping_cart_utility(site)
    
    print >> out, "Notifying Installation"
    notify_install( site )
    
    logger.info(out.getvalue())
    
    return "Setup various finished"

