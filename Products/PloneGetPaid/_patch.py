"""

REQUEST HEADER

original source (zope 2.9.x) didn't match against normalized headers, which caused issues
between different template engines (z2/z3) stomping over each other's response header.

might still be applicable in zope 2.10

this patch should be filed as bug and go upstream into zope.


REQUEST INPUT PROCESSING

five destructively processes list and tuple inputs, when converting to unicode
so we patch it to only happen once in the request.

"""

from ZPublisher.HTTPResponse import HTTPResponse

def getHeader(self, name, literal=0):
    '''\
    Get a header value
    
    Returns the value associated with a HTTP return header, or
    "None" if no such header has been set in the response
    yet. If the literal flag is true, the case of the header name is
    preserved, otherwise the header name will be lowercased.'''
    key = name.lower()
    name = literal and name or key
    return self.headers.get(name, None)

HTTPResponse.getHeader = getHeader

from Products.Five.formlib.formbase import FiveFormlibMixin
from Products.Five.browser import decode

def update( self ):
    if getattr( self.request, '__inputs_processed', False ):        
        decode.processInputs( self.request )
        decode.setPageEncoding( self.request )
        request.__inputs_processed = True
    super( FiveFormlibMixin, self).update()

FiveFormlibMixin.update = update
    
    

    
    
    
