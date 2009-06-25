
from Products.Five.browser import BrowserView
from Products.PloneGetPaid import generations

class AdminUpgrade( BrowserView ):
    
    log = None
    
    def __call__( self ):
        if self.request.form.has_key('upgrade'):
            self.log = self._upgrade()
        return super( AdminUpgrade, self ).__call__()
        
    def _upgrade( self ):
        """ upgrade the application
        """
        return generations.upgrade(self.context)
        
    def softwareVersion( self ):
        return generations.getAppSoftwareVersion()
        
    def databaseVersion( self ):
        return generations.getAppVersion( self.context )
        
    def listUpgrades( self ):
        return generations.getUpgrades( self.context )