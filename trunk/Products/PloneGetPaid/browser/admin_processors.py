"""
Payment Processor Options Form
"""

__version__ = "$Revision$"
# $Id$
# $URL$

from zope import component, event, interface, lifecycleevent

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.CMFCore.utils import getToolByName

from z3c.form import field, group, form
from z3c.form.interfaces import IFormLayer, IGroup 

from getpaid.core import interfaces

from Products.PloneGetPaid.interfaces import IGetPaidManagementOptions, IGetPaidManagementPaymentOptions
from Products.PloneGetPaid.browser.interfaces import IDontShowGetPaidPortlets
from Products.PloneGetPaid import _


class PaymentProcessorOptionsBase(group.Group):
    """ Base sheet for payment processor options """

    def getContent(self):
        return component.getUtility(interfaces.IPaymentProcessor, name=self.prefix)


class EnabledPaymentProcessors(PaymentProcessorOptionsBase):
    """ Fixed sheet to enable and disable installed payment processor """
    prefix = "enabled_processors"
    label = _(u"Enabled Processors")
    weight = 0
    fields = field.Fields(IGetPaidManagementPaymentOptions)

    def getContent(self):
        site = getToolByName(self.context, 'portal_url').getPortalObject()
        return IGetPaidManagementOptions(site)


class IPaymentProcessorOptions(interface.Interface):
    """ Marker interface for procsessor options """


class PaymentProcessorOptionsForm(group.GroupForm, form.EditForm):
    """ 
    Options form for enabling and configuring installed payment
    processor plugins.

    FIXME: This and LineItemCointainerEditForm cointain a lot of
    similar code. Especially extractData() and applyChanges(). 
    A common base class should be created
    """
    interface.implements(IPaymentProcessorOptions,
                         IDontShowGetPaidPortlets)
    groups = None
    fields = field.Fields()

    render = ViewPageTemplateFile("templates/settings-processors.pt")

    def __init__(self, context, request):
        super(PaymentProcessorOptionsForm, self).__init__(context, request)
        # Adds IFormLayer for request to support z3c.form
        interface.alsoProvides(self.request, IFormLayer)

    def updateGroups(self):
        site = getToolByName(self.context, 'portal_url').getPortalObject()
        enabled_processors = sorted(IGetPaidManagementOptions(site).payment_processors)

        if self.groups is None \
                or sorted([g.prefix for g in self.groups]) != enabled_processors:
            groups = []
            for name, group in component.getAdapters((self.context, self.request, self), IGroup):
                if name in enabled_processors or name == "enabled_processors":
                    groups.append(group)
            self.groups = tuple(sorted(groups, lambda x,y: cmp(int(getattr(x, 'weight', 100)), int(getattr(y, 'weight', 100)))))

        for group in self.groups:
            group.update()
                
    def update(self):
        self.updateWidgets()
        self.updateGroups()
        self.updateActions()
        self.actions.execute()
        if self.refreshActions:
            self.updateActions()
        self.updateGroups() # enabled processors may have changed

    def extractData(self, setErrors=True):
        """See interfaces.IEditForm and group.GroupForm's implementation """
        data, errors = form.EditForm.extractData(self, setErrors=setErrors)
        for group in self.groups:
            groupData, groupErrors = group.extractData(setErrors=setErrors)
            data.update({group.prefix: groupData}) # (!)
            if groupErrors:
                if errors:
                    errors += groupErrors
                else:
                    errors = groupErrors
        return data, errors

    def applyChanges(self, data):
        """See interfaces.IEditForm and group.GroupForm's implementation """
        changes = {}
        for group in self.groups:
            groupData = data.has_key(group.prefix) and data[group.prefix] or {}
            groupChanges = group.applyChanges(groupData) # (!)
            groupContent = group.getContent()
            for interface, names in groupChanges.items():
                if not changes.has_key(groupContent):
                    changes[groupContent] = {}
                changes[groupContent][interface] = changes[groupContent].get(interface, []) + names
        if changes:
            for groupContent, groupChanges in changes.items():
                descriptions = []
                for interface, names in groupChanges.items():
                    descriptions.append(
                        lifecycleevent.Attributes(interface, *names))
                # Send out a detailed object-modified event for every modified object
                event.notify(
                    lifecycleevent.ObjectModifiedEvent(groupContent,
                        *descriptions))
        # content = self.getContent()
        # changes.update(form.applyChanges(self, content, data))
        return changes
