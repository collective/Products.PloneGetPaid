

def install_ups( self ):
    from getpaid.ups import plugin
    plugin.UPSPlugin( self ).install()
    return "installed ups"

def install_warehouse( self ):
    from getpaid.warehouse import plugin
    plugin.WarehousePlugin( self ).install()
    return "warehouse installed"
