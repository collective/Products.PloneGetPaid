"""
collective.z3cform.wizard based checkout wizard

$Id:$
"""

from zope import component, interface, schema

from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile

from z3c.form import button, field, form
from z3c.form.interfaces import IFormLayer

from collective.z3cform.wizard import wizard
# from plone.z3cform.fieldsets import group


class CheckoutWizardStep(wizard.Step):
    def __init__(self, context, request, wizard):
        super(CheckoutWizardStep, self).__init__(context, request, wizard)
        interface.alsoProvides(request, IFormLayer)


class CheckoutWizardStepEnter(CheckoutWizardStep):
    prefix = 'enter'
    fields = field.Fields()


class CheckoutWizardStepReview(CheckoutWizardStep):
    prefix = 'review'
    fields = field.Fields()


class PaymentButtonManager(object):
#    def filter(self, viewlets):
#        """ filte by ... """
#        pass

#    def sort (self, viewlets ):
#        """ sort by ... """
#        viewlets.sort( lambda x,y: cmp( int(x[1].weight), int(y[1].weight) ) )
#        return viewlets

#    def update(self):
#        pass

    def render(self):
        return "".join([b() for b in self.viewlets])


class CheckoutWizard(wizard.Wizard):
    label = u"Checkout Wizard"
    steps = (CheckoutWizardStepEnter, CheckoutWizardStepReview)
    # the overwritten template can be found as self.index
    template = ZopeTwoPageTemplateFile("templates/checkout-wizard.pt")

    def __init__(self, context, request):
        super(CheckoutWizard, self).__init__(context, request)
        self.buttons["continue"].title = u"Tsiipaduup"
