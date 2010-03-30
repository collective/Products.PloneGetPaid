from zope.location.interfaces import ISite
from zope.app.intid.interfaces import IIntIds
from zope.component import getUtility

from getpaid.core.interfaces import IOrderManager, IStore

from base import PloneGetPaidTestCase



class TestProductInstall(PloneGetPaidTestCase):
    # XXX need test for teardown_store (and all uninstallers)

    def test_portal_is_a_site(self):
        self.assert_(ISite.providedBy(self.portal))

    def test_portal_is_a_store(self):
        self.assert_(IStore.providedBy(self.portal))

    def test_order_manager_is_setup(self):
        sm = self.portal.getSiteManager()
        self.assert_(list(sm.getUtilitiesFor(IOrderManager)))

    def test_intid_is_setup(self):
        self.assert_(getUtility(IIntIds, context=self.portal) is not None)

    def test_plone3_portlets_are_installed(self):
        from zope.component import getUtility, getMultiAdapter
        from plone.portlets.interfaces import IPortletManager, IPortletAssignmentMapping

        # Get some definitions.
        column = getUtility(IPortletManager, name="plone.rightcolumn", context=self.portal)
        manager = getMultiAdapter((self.portal, column), IPortletAssignmentMapping)
        portletnames = [v.title for v in manager.values()]

        self.failUnless(u'Shopping Cart' in portletnames)
        self.failUnless(u'Buyable' in portletnames)
        self.failUnless(u'Donatable' in portletnames)
        self.failUnless(u'Shippable' in portletnames)
        self.failUnless(u'Premium' in portletnames)


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestProductInstall))
    return suite
