from getpaid.core.interfaces import IPayableCreationEvent


def payable_created(object, event):
    # Reindex the object.  Particularly, in Plone 3 this means that
    # the object_provides index gets updated, so you can search for
    # the marker interfaces with something like:
    # portal_catalog.searchResults(
    #      object_provides=IShippableMarker.__identifier__)
    object.reindexObject()
