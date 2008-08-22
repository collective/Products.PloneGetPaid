from zope.app import zapi
from zope.app.form.browser import FloatWidget
from zope.app.form.browser.widget import SimpleInputWidget
from zope.app.form.browser.objectwidget import ObjectWidgetView as ObjectWidgetViewBase
from zope.app.form.browser.objectwidget import ObjectWidget as ObjectWidgetBase
from zope.app.form.browser.textwidgets import DateWidget
from zope.app.form.browser.itemswidgets import OrderedMultiSelectWidget as BaseSelection
from zope.app.pagetemplate.viewpagetemplatefile import ViewPageTemplateFile
from zope.i18n.interfaces import IUserPreferredCharsets
from Products.PloneGetPaid.config import PLONE3
from Products.PloneGetPaid.interfaces import IMonthsAndYears
from Products.PloneGetPaid.interfaces import ICountriesStates
from Products.PloneGetPaid.vocabularies import TitledVocabulary

from Products.Five.browser import decode

class ObjectWidgetView( ObjectWidgetViewBase ):    
    template = ViewPageTemplateFile('templates/objectwidget.pt')

class ObjectWidget( ObjectWidgetBase ):    
    def __init__( self, *args, **kw):
        super( ObjectWidget, self).__init__( *args, **kw )
        self.view = ObjectWidgetView( self, self.request)

class SequenceObjectWidget( ObjectWidgetBase ):
    def __init__( self, context, value_type, request, factory, **kw):
        super( ObjectWidget, self).__init__( context, request, factory, **kw )
        self.view = ObjectWidgetView( self, self.request)    
        
class WithTemplateWidget(SimpleInputWidget):
    def __call__( self ):
        # XXX dirty hack to make the values coming out of here encoded properly,
        # by default please fix me.
        envadapter = IUserPreferredCharsets( self.request)
        charsets = envadapter.getPreferredCharsets() or ['utf-8']
        value = self.template()
        if not isinstance(value, unicode):
            value = decode._decode( self.template(), charsets )
        return value
    

class CountrySelectionWidget(WithTemplateWidget):
    template = ViewPageTemplateFile('templates/country-selection-widget.pt')

    def getVocabulary(self):
        return self.context.vocabulary

class StateSelectionWidget(WithTemplateWidget):
    """State selection widget for non-Javascript.

    When Javascript is available, this widget is simply
    overwritten.
    """
    template = ViewPageTemplateFile('templates/state-selection-widget.pt')

    def getVocabulary(self):
        utility = zapi.getUtility(ICountriesStates)
        # US is a good default for country.
        country = 'US'

        # Try to get the country from the form.
        form_country = self.request.form.get('form.contact_country', '')

        # If a country is known we can safely ignore any possible
        # setting of the state and just return the states for that
        # country: if the chosen country is The Netherlands there is
        # no sense in believing that the state is the Japanese
        # province of Hokkaido.
        if form_country == '':
            # No country is known.
            # Try to get the state from the form.
            if PLONE3: # _getCurrentValue not in zope.app.form with zope 2.9
                state = self._getCurrentValue()
            else:
                state = self._getFormInput()
            if state and state != u'(no values)':
                # A state has been chosen.  Take the first two letters of
                # the state value as the country.
                country = state[:2]
        else:
            country = form_country
        states = utility.states(country)
        return TitledVocabulary.fromTitles(states)

class CCExpirationDateWidget(WithTemplateWidget,DateWidget):
    template = ViewPageTemplateFile('templates/cc-expiration-date-widget.pt')
    def months(self):
        utility = zapi.getUtility(IMonthsAndYears)
        return utility.months

    def years(self):
        utility = zapi.getUtility(IMonthsAndYears)
        return utility.years

    def getFormMonth(self):
        return self.request.get('%s_month' % self.name)

    def getFormYear(self):
        return self.request.get('%s_year' % self.name)

    def _getFormInput(self):
        return ('%s-%s'%(self.getFormYear(),self.getFormMonth()))

    def _toFieldValue(self,input):
        return super(CCExpirationDateWidget, self)._toFieldValue(input)

    def hasInput(self):
        return self.getFormMonth() and self.getFormYear()
        #return self.getFormMonth() in self.months() and\
               #self.getFormYear() in self.years()

class PriceWidget(FloatWidget):
    """ This is a widget for rendering the price.
    """
    def _toFormValue(self, value):
        """Converts a field value to a string used as an HTML form value.

        This method is used in the default rendering of widgets that can
        represent their values in a single HTML form value. Widgets whose
        fields have more complex data structures should disregard this
        method and override the default rendering method (__call__).
        """
        if value == self.context.missing_value:
            return self._missing
        else:
            #import pdb; pdb.set_trace()
            return '%.2f' % value



def SelectWidgetFactory( field, request ):
    vocabulary = field.value_type.vocabulary
    return OrderedMultiSelectionWidget( field, vocabulary, request ) 

class OrderedMultiSelectionWidget(BaseSelection):
    template = ViewPageTemplateFile('templates/ordered-selection.pt')

    def selected(self):
        """Return a list of tuples (text, value) that are selected."""
        # Get form values
        values = self._getFormValue()
        # Not all content objects must necessarily support the attributes
        if hasattr(self.context.context, self.context.__name__):
            # merge in values from content 
            for value in self.context.get(self.context.context):
                if value not in values:
                    values.append(value)
        terms = [self.vocabulary.getTerm(value)
                 for value in values if value in self.vocabulary ]
        return [{'text': self.textForValue(term), 'value': term.token}
                for term in terms]
