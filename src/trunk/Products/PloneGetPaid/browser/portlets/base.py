"""Base for PloneGetPaid portlets.

This helps in getting the current portlet templates working in a Plone
3.0 site as well.

See the other python files here for how to use it.  But since this way
of doing portlets in Plone 3.0 is new, let's write this out:

- Make a new python file here.

- Add an interface class inheriting from
  plone.portlets.interfaces.IPortletDataProvider

- Add a class Assignment:

  - inherit from plone.app.portlets.portlets.base.Assignment

  - claim that you implement the IPortletDataProvider interface

  - add a title property for showing in the Manage Portlets screen

- Add a class AddForm:

  - inherit from plone.app.portlets.portlets.base.NullAddForm
    (use base.AddForm if you have some configuration to do)

  - add a create method that instantiates an Assignment of the
    portlet.

- Maybe add a class EditForm, but I did not need it yet, as I did not
  need configuration yet.

- Add a class Renderer, inheriting from
  Products.PloneGetPaid.browser.portlets.base.GetPaidRenderer
  Follow instructions in that class (below).

- Hook this up with zcml.

- Add some lines in profiles/default/portlets.xml

"""

from plone.app.portlets.portlets import base
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from Products.PloneGetPaid.interfaces import PayableMarkerMap
from Products.PloneGetPaid.interfaces import IPayableMarker


class GetPaidRenderer(base.Renderer):
    """Base rendered useful for all/most getpaid portlets.

    This supplies the basic building blocks that the portlet templates
    expect.  Usage:

    - Inherit from this base class,

    - specify a 'marker' interface,

    - specify a 'render' attribute or method, probably pointing to a
      template,

    - add any other functionality you need for that template.
    """

    # Marker interface that this renderer is meant for.
    marker = IPayableMarker
    # Supply a template id in the inheriting class.
    render = ViewPageTemplateFile('../templates/portlet-content-none.pt')

    @property
    def available(self):
        """Portlet is available when a marker interface is provided.

        Overwrite this by picking a different interface.
        """
        return self.marker.providedBy(self.context)


    def isPayable(self):
        """When we are rendered, the context is always payable.

        Or shippable, etcetera.  Otherwise the 'available' method
        would return False already.  The current portlet templates
        expect this method to be here.

        """
        return True

    @property
    def payable(self):
        """Return the payable (shippable) version of the context.
        """
        iface = PayableMarkerMap.get(self.marker, None)
        if iface is None:
            # Something is badly wrong here.
            return None
        return iface( self.context )
