"""

REQUEST INPUT PROCESSING

five destructively processes list and tuple inputs, when converting to unicode
so we patch it to only happen once in the request.

"""

try:
    from five.formlib.formbase import FiveFormlibMixin
except ImportError:
    from Products.Five.formlib.formbase import FiveFormlibMixin
from Products.Five.browser import decode

def update( self ):
    if not getattr( self.request, '__inputs_processed', False ):        
        decode.processInputs( self.request )
        decode.setPageEncoding( self.request )
        self.request.__inputs_processed = True
    super( FiveFormlibMixin, self).update()

FiveFormlibMixin.update = update
