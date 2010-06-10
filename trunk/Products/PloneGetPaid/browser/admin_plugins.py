"""
admin plugins

$Id: admin_processors.py 3449 2010-04-13 14:46:04Z datakurre $
"""
from zope import component, interface, schema

from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile

from z3c.form.interfaces import IFormLayer
from z3c.form import interfaces, form, button

from getpaid.core.interfaces import IPluginManager

from Products.PloneGetPaid.i18n import _


class PluginForm(form.Form):
    """ A simple z3c.form with install or uninstall button for an IPluginManager """
    ignoreContext = True # don't use context to get widget data  

    prefix = None
    manager = None

    def __init__(self, context, request, plugin_id, plugin_manager):
        """ Create form, use plugin_id as form prefix, store manager for actions, and update form widgets""" 
        super(PluginForm, self).__init__(context, request)        
        interface.alsoProvides(request, IFormLayer)
        self.prefix = plugin_id
        self.manager = plugin_manager
        self.update()

    def update(self):
        """ Update form widgets and hide the other button depending on the manager state """
        super(PluginForm, self).update()
        if self.manager.status():
            self.actions['install'].style = u"display: none;"
        else:
            self.actions['uninstall'].style = u"display: none;"

    @button.buttonAndHandler(_(u"Install"), name='install')
    def install(self, action):
        """ Try to install plugin via its plugin manager and set the portal message to display the results """
        if not self.manager.status():
            self.manager.install()
        if self.manager.status():
            self.context.plone_utils.addPortalMessage(u"Plugin successfully installed.")
            self.successMessage = _(u"Plugin successfully installed.")
        else:
            self.context.plone_utils.addPortalMessage(_(u"Cannot uninstall plugin."), type='error')
            self.noChangesMessage = _(u"Cannot install plugin.")

    @button.buttonAndHandler(_(u"Uninstall"), name='uninstall')
    def uninstall(self, action):
        """ Try to iunnstall plugin via its plugin manager and set the portal message to display the results """
        if self.manager.status():
            self.manager.uninstall()
        if not self.manager.status():
            self.context.plone_utils.addPortalMessage(_(u"Plugin successfully uninstalled."))
            self.successMessage = _(u"Plugin successfully uninstalled.")
        else:
            self.context.plone_utils.addPortalMessage(_(u"Cannot uninstall plugin."), type='error')
            self.noChangesMessage = _(u"Cannot uninstall plugin.")

class PluginsManagerForm(BrowserView):
    """ A browser view, which renders a z3c.form for each found plugin manager """
    __call__ = ZopeTwoPageTemplateFile("templates/settings-plugins.pt")

    def __init__(self, context, request):
        super(PluginsManagerForm, self).__init__(context, request)

        self.forms = [PluginForm(self.context, self.request, str(plugin_id), plugin_manager)
                      for plugin_id, plugin_manager in component.getAdapters((self.context,), IPluginManager)]
