"""

our base view, formlib view, and viewlet. mostly this consists of work arounds for zope2, and
some utilities.

$Id$
"""


from zope.i18n.interfaces import IUserPreferredLanguages
from zope.i18n.locales import locales, LoadLocaleError

from ZTUtils import make_hidden_input

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.Five.formlib import formbase

from zope.formlib import form
from Products.Five.viewlet import viewlet


class BaseView( object ):
    # so this mixin fixes some issues with doing zope3 in zope2 for views
    # specifically it puts a debug attribute on the request which some view machinery checks for
    # secondly it lookups the user locale, and attaches it as an attribute on the request
    # where the i10n widget machinery expects to find it.

    def setupEnvironment( self, request ):
        if not hasattr( request, 'debug'): request.debug = False

    def setupLocale( self, request ):
        # slightly adapted from zope.publisher.http.HTTPRequest.setupLocale
        if getattr( request, 'locale', None) is not None:
            return
        
        envadapter = IUserPreferredLanguages(request, None)
        if envadapter is None:
            request.locale = locales.getLocale(None, None, None)            
            return

        langs = envadapter.getPreferredLanguages()
        for httplang in langs:
            parts = (httplang.split('-') + [None, None])[:3]
            try:
                request.locale = locales.getLocale(*parts)
                return
            except LoadLocaleError:
                # Just try the next combination
                pass
        else:
            # No combination gave us an existing locale, so use the default,
            # which is guaranteed to exist
            request.locale = locales.getLocale(None, None, None)


class BaseFormView( formbase.EditForm, BaseView ):

    template = ViewPageTemplateFile('templates/form.pt')

    adapters = None
    action_url = "" # NEEDED
    hidden_form_vars = None # mapping of hidden variables to pass through on the form

    def hidden_inputs( self ):
        if not self.hidden_form_vars: return ''
        return make_hidden_input( **self.hidden_form_vars )

    hidden_inputs = property( hidden_inputs )
    
    def __init__( self, context, request ):
        # setup some compatiblity
        self.setupLocale( request )
        self.setupEnvironment( request )
        super( BaseFormView, self).__init__( context, request )
        
    def setUpWidgets( self, ignore_request=False ):
        self.adapters = self.adapters is not None and self.adapters or {}
        self.widgets = form.setUpEditWidgets(
            self.form_fields, self.prefix, self.context, self.request,
            adapters=self.adapters, ignore_request=ignore_request
            )        

class FormViewlet( viewlet.SimpleAttributeViewlet, formbase.SubPageForm, BaseView ):
    """ a viewlet which utilize formlib
    """
    form_template = formbase.FormBase.template    
    renderForm = formbase.FormBase.render
    
    __page_attribute__ = "template"
    
    def __init__(self, context, request, view, manager):    
        self.setupLocale( request )
        self.setupEnvironment( request )
        super( FormViewlet, self).__init__( context, request, view, manager )
    
    def update( self ):
        super( viewlet.SimpleAttributeViewlet, self).update()
        super( formbase.SubPageForm, self).update()

class StockFormViewlet( FormViewlet ):
    
    template = ViewPageTemplateFile('templates/form.pt')    
    
    def render( self ):
        return self.template()

class EditFormViewlet( StockFormViewlet, formbase.EditForm ): pass
