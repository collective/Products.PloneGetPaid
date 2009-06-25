GLOBALS = globals()
try:
    import Products.CMFPlone.migrations.v3_0
    PLONE3 = True
except ImportError:
    PLONE3 = False
