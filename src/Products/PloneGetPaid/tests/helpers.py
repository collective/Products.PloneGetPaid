from Acquisition import Implicit
class FauxUser( Implicit ):

    def __init__( self, id, name=None, roles={}, groups={} ):

        self._id = id
        self._name = name
        self._roles = roles
        self._groups = groups

    def getId( self ):

        return self._id

    def getUserName( self ):

        return self._name

    def getRoles( self ):

        return self._roles.keys()

    def _addRoles(self, roles):
        for role in roles:
            self._roles[role] = 1

    def getGroups( self ):

        return self._groups.keys()

    def _addGroups(self, groups):
        for group in groups:
            self._groups[group] = 1

    def __repr__( self ):

        return '<FauxUser: %s>' % self._id