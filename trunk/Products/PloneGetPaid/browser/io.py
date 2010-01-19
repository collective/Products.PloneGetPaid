"""
Import Export Management Views for GetPaid
"""

#from StringIO import StringIO
#from datetime import datetime
#from getpaid.io.interfaces import IStoreWriter, IStoreReader
#from zope.formlib import form
#from base import BaseFormView
#from zope import interface, schema
#from ZPublisher.Iterators import IStreamIterator
#from Products.PloneGetPaid.i18n import _
#from Products.CMFCore.utils import getToolByName
#from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
#
#class IAdminImportExportOptions( interface.Interface ):
#    
#    data_file = schema.Bytes( description=_(u"Data File to Import"), required=False)
#
#class StreamIterator(object):
#
#    __implements__ = (IStreamIterator)
#    
#    def __init__( self, stream, streamsize=1<<16):
#        self.stream = stream
#        self.stream.seek(0,0)
#        self.streamsize = streamsize
#    
#    def next( self ):
#        data = self.stream.read(self.streamsize)
#        if not data:
#            raise StopIteration
#        return data
#        
#    def __len__(self):
#        cur_pos = self.stream.tell()
#        self.stream.seek(0, 2)
#        size = self.stream.tell()
#        self.stream.seek(cur_pos, 0)    
#        return size
#    
#class AdminImportExport( BaseFormView ):
#    """ management view to import or export the state of the store instance
#    """
#
#    form_fields = form.Fields( IAdminImportExportOptions )
#    template = ZopeTwoPageTemplateFile('templates/settings-page.pt')
#    
#    _download_stream = None
#        
#    def __call__( self ):
#        """ """
#        self.update()
#        if self._download_stream is not None:
#            return self._download_stream
#        return self.render()
#        
#    def setUpWidgets(self, ignore_request=False):
#        self.adapters = {}
#        self.widgets = form.setUpDataWidgets(
#            self.form_fields, self.prefix, self.context, self.request,
#            ignore_request=ignore_request
#            )        
#    
#    @form.action(_(u"Export"), condition=form.haveInputWidgets)
#    def handle_export( self, action, data ):
#        store = getToolByName( self.context, 'portal_url').getPortalObject()
#        writer = IStoreWriter( store )
#        stream = writer.toArchiveStream()        
#        self._download_stream = StreamIterator( stream )
#        now = datetime.now()
#        filename = "store-export--%s-%s-%s.tgz"%(now.year, now.month, now.day)
#        self.request.response.setHeader('Content-Type', 'application/octet-stream')
#        self.request.response.setHeader("Content-Disposition", "attachment; filename=%s"%filename)
#        self.request.response.setHeader('Content-Length', len( self._download_stream) )        
#        
#    @form.action(_(u"Import"), condition=form.haveInputWidgets)
#    def handle_import( self, action, data ):#
#        store = getToolByName( self.context, 'portal_url').getPortalObject()
#        reader = IStoreReader( store )        
#        stream = StringIO( data['data_file'])
#        reader.importArchiveStream( stream )
#        self.status = _(u"Data Imported")
