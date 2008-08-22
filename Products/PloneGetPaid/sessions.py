from Products.CMFPlone.utils import safe_unicode, getToolByName

def set_came_from_url(context):
    """
    Set a session variable for came_from to contexts url. Used to
    persist a context you may want to retrieve at subsequent point in
    the shopping process. For example: 'continue shopping' of the cart
    view will use it to locate where to return the user to if they
    elect to continue shopping.
    """
    session_manager = getToolByName(context, 'session_data_manager')
    session = session_manager.getSessionData()
    session['getpaid.camefrom'] = context.absolute_url()

def get_came_from_url(context):
    """
    get the current session variable came_from
    """
    session_manager = getToolByName(context, 'session_data_manager')
    if not session_manager.hasSessionData():
        return None
    session = session_manager.getSessionData()
    return session.get('getpaid.camefrom', None)
