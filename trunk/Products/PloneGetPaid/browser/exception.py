"""
An exception view that looks good in our templates, basically sans html

$Id$
"""
from cgi import escape

from zope.interface import implements
from zope.i18n import translate

from zope.app.form.interfaces import IWidgetInputError
from zope.app.form.browser.interfaces import IWidgetInputErrorView

class WidgetInputErrorView(object):
    """Display an input error as a snippet of text."""
    implements(IWidgetInputErrorView)

    __used_for__ = IWidgetInputError

    def __init__(self, context, request):
        self.context, self.request = context, request

    def snippet(self):
        """Convert a widget input error to an html snippet
        """
        message = self.context.doc()
        translated = translate(message, context=self.request, default=message)
        return unicode( escape(translated) )
