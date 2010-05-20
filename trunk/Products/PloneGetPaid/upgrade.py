"""
GenericSetup upgrade steps for Products.PloneGetPaid

$Id:$
"""

from zope import schema

from Products.CMFCore.utils import getToolByName

from getpaid.core import interfaces

from Products.PloneGetPaid.interfaces import IPayableMarker
from Products.PloneGetPaid.interfaces import IBuyableMarker, IPremiumMarker, IShippableMarker, IDonatableMarker, IVariableAmountDonatableMarker


def upgrade0to1(self):
    """ Upgrades Products.PloneGetPaid from profile 0.10.1 to 1."""

    ###
    # Migration for PersistentOptions with annotation key bug
    
    # Because of the nature fo the bug, we don't know the names for the
    # annotation keys e.g. "getpaid.content.buyable". Our only option is
    # to explicitly define a map with:
    #   1) Marker interface
    #   2) PersistentOption interface
    #   3) PersistentOption annotation key
    # for all the payable types we want to migrate.
    payable_map = {
        IBuyableMarker: (interfaces.IBuyableContent, "getpaid.content.buyable"),
        IPremiumMarker: (interfaces.IPremiumContent, "getpaid.content.buyable"),
        IShippableMarker: (interfaces.IShippableContent, "getpaid.content.shippable"),
        IDonatableMarker: (interfaces.IDonationContent, "getpaid.content.donate"),
        IVariableAmountDonatableMarker: (interfaces.IVariableAmountDonationContent, "getpaid.content.variableamountdonate")
        }
    
    # Retrieve all payables (content objects with IPayableMarker)
    pc = getToolByName(self, "portal_catalog")
    payables = [b.getObject() for b in pc.searchResults(object_provides=IPayableMarker.__identifier__)]
    # Iterate through all payables
    for payable in payables:
        # Select annotations starting with getpaid.*
        annotations = [{'key': key, 'size': len(payable.__annotations__[key])} \
                        for key in dict(payable.__annotations__).keys() if key.startswith("getpaid.")]
        # Sort annotations in ascending order by their size
        annotations.sort(cmp=lambda a,b: a['size'] >= b['size'] and 1 or -1)
        # Save annotated options temporarily
        options = {}
        for annotation in annotations:
            for name in payable.__annotations__[annotation['key']].keys():
                options[name] = payable.__annotations__[annotation['key']][name]
        # Select known PersistenOption interfaces for the current payable
        ifaces = [payable_map[i] for i in payable_map.keys() if i.providedBy(payable)]
        # Iterate through the interfaces and update the respective annotations
        for iface, key in ifaces:
            for name, field in schema.getFields(iface).items():
                if options.has_key(name):
                    payable.__annotations__[key][name] = options[name]

    # Execute also upgrade profile, currently only updating the installed profile version
    setup_tool = getToolByName(self, 'portal_setup')
    setup_tool.runAllImportStepsFromProfile('profile-Products.PloneGetPaid:upgrade0to1')

    return "Upgraded Products.PloneGetPaid from profile version 0.10.1 to 1."
