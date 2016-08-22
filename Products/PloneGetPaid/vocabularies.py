"""
$Id$

vocabularies for getpaid
"""

from zope import component
from zope.interface import implements
from os import path
import datetime

from zope.schema import vocabulary
from getpaid.core import interfaces
from plone.registry.interfaces import IRegistry
from Products.CMFPlone.interfaces import ISearchSchema

from iso3166 import CountriesStatesParser
from Products.PloneGetPaid.interfaces import ICountriesStates, IMonthsAndYears

from Products.CMFCore.utils import getToolByName

from Products.PloneGetPaid.i18n import _

def PaymentMethods( context ):
    # context is the portal config options, whose context is the portal
    adapters = component.getAdapters( (context.context,), interfaces.IPaymentProcessor )
    payment_names = set( map(unicode, [ n for n,a in adapters]) )
    return vocabulary.SimpleVocabulary.fromValues( payment_names )

def ContentTypes( context ):
    # context is actually a preferences object, dig another level to get to the adapted context
    # which is acq wrapped.
    portal_types = getToolByName( context.context, 'portal_types' )
    terms = []
    # hmmm..
    types = filter( lambda x: x.global_allow, portal_types.objectValues() )

    properties = getToolByName( context.context, 'portal_properties')
    if hasattr(properties.site_properties, 'types_not_searched'):
        types_not_searched = set( properties.site_properties.types_not_searched )
    else:
        registry = component.getUtility(IRegistry)
        settings = registry.forInterface(ISearchSchema, prefix="plone")
        types_not_searched = set( settings.types_not_searched )
    for type in portal_types.objectValues():
        if type.getId() in types_not_searched:
            continue
        terms.append(
            vocabulary.SimpleTerm( unicode(type.getId()), title=unicode(type.title_or_id()) )
            )

    terms.sort( lambda x,y: cmp( x.title, y.title ) )

    return vocabulary.SimpleVocabulary( terms )

def TaxMethods( context ):
    return vocabulary.SimpleVocabulary.fromValues( (u"None",) )

def ShippingMethods( context ):
    adapters = component.getAdapters( (context.context,), interfaces.IShippingMethod )
    methods = set( map(unicode, [ n for n,a in adapters]) )
    return vocabulary.SimpleVocabulary.fromValues( methods )
    
def ShippingServices( context ):
    utilities = component.getUtilitiesFor( interfaces.IShippingRateService )
    services = set( map( unicode, [n for n,a in utilities ]))
    return vocabulary.SimpleVocabulary.fromValues( services )    

#def CreditCards( context ):
#    return vocabulary.SimpleVocabulary.fromValues( (u"Visa", u"Mastercard", u"Discover", u"American Express") )

def WeightUnits( context ):
    return vocabulary.SimpleVocabulary.fromValues( (_(u"Pounds"),) )

def Currencies( context ):
    return vocabulary.SimpleVocabulary.fromValues( (_(u"US Dollars"),) )

class TitledVocabulary(vocabulary.SimpleVocabulary):
    def fromTitles(cls, items, *interfaces):
        """Construct a vocabulary from a list of (value,title) pairs.

        The order of the items is preserved as the order of the terms
        in the vocabulary.  Terms are created by calling the class
        method createTerm() with the pair (value, title).

        One or more interfaces may also be provided so that alternate
        widgets may be bound without subclassing.
        """
        terms = [cls.createTerm(value,value,title) for (value,title) in items]
        return cls(terms, *interfaces)
    fromTitles = classmethod(fromTitles)

def CustomerNotificationChoices( context ):
    return TitledVocabulary.fromTitles(
        [
        ("no_notification", _(u"Do not send customer email notification of a completed transaction")),
        ("notification", _(u"Send customer email notification of a completed transaction"))
        ]
        )

def MerchantNotificationChoices( context ):
    return TitledVocabulary.fromTitles(
        [
        ("no_notification", _(u"Do not send merchant email notification of a completed transaction")),
        ("notification", _(u"Send merchant email notification when a transaction happens")),
        #("encrypted_notification", _u"Send merchant encrypted email notification when a transaction happens")]
        ]
        )

class CountriesStatesFromFile(object):
    """Countries utility that reads data from a file
    """
    implements(ICountriesStates)

    _no_values = [(u'(no values)',u'(no values)')]
    # Be careful, somewhere else, there is code that asumes that state values
    # length is <= 6. Don't modify this ones that are part of the vocabulary
    _not_aplicable = [(u'??NA',u'Not Applicable')]
    _allowed_no_values = [(u'??NV',u'(no values)')]

    def __init__(self):
        iso3166_path = path.join(path.dirname(__file__), 'iso3166')
        self.csparser = CountriesStatesParser(iso3166_path)
        self.csparser.parse()
        self.loaded_countries = []

    def special_values(self):
        return [self._no_values[0],
                self._not_aplicable[0],
                self._allowed_no_values[0]]
    special_values = property(special_values)

    def countries(self):
        if self.loaded_countries:
            return self.loaded_countries
        names =  self.csparser.getCountriesNameOrdered()
        res = []
        for n in names:
            if len(n[1]) < 18:
                res.append( n )
            elif ',' in n:
                res.append( ( n[0], n[1].split(',')[0] ) )
            else:
                #This may show the countries wrongly abbreviated (in fact i am
                #almost sure it will, but is better than not showing them at all
                res.append( ( n[0], n[1][:18] ) )

        # need to pick this up some list of strings property in the admin interface
        def sorter( x, y, order=['UNITED STATES', 'UNITED KINGDOM', 'CANADA']):
            if x[1] in order and y[1] in order:
                return cmp( order.index(x[1]), order.index(y[1]) )
            if x[1] in order:
                return -1
            if y[1] in order:
                return 1
            return cmp( x[1], y[1] )

        res.sort( sorter )
        self.loaded_countries = res
        return res

    countries = property(countries)

    def states(self, country=None, allow_no_values=False):
        if country is None:
            states = self._not_aplicable + self.allStates()
        else:
            states = self.csparser.getStatesOf(country)

        if len(states) == 0:
            states = self._not_aplicable
        elif allow_no_values:
            states = self._allowed_no_values + states
        else:
            states = self._no_values + states
        return states

    def allStates(self):
        return self.csparser.getStatesOfAllCountries()

    def allStateValues(self):
        all_states = self.csparser.getStatesOfAllCountries()
        return self._allowed_no_values + self._not_aplicable + all_states

def Countries( context ):
    utility = component.getUtility(ICountriesStates)
    return TitledVocabulary.fromTitles(utility.countries)

def States( context ):
    utility = component.getUtility(ICountriesStates)
    return TitledVocabulary.fromTitles(utility.allStateValues())

class MonthsAndYears(object):
    """Months-Years utility"""
    implements(IMonthsAndYears)

    def tuple_unicode_range(self,begin,end):
        return tuple([unicode('%02i' % i) for i in range(begin,end)])

    def months(self):
        return self.tuple_unicode_range(1,13)
    months = property(months)

    def years(self):
        start = int(datetime.datetime.today().strftime('%Y'))
        end = start + 30
        return self.tuple_unicode_range(start, end)
    years = property(years)
