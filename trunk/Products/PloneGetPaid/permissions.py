from AccessControl import ModuleSecurityInfo
from Products.CMFCore.permissions import setDefaultRoles

security = ModuleSecurityInfo('Products.PloneGetPaid')

ManageOrders = 'PloneGetPaid: Manage Orders'
security.declarePublic(ManageOrders)
setDefaultRoles(ManageOrders, ('Manager',))
