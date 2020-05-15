# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
import unittest
import trytond.tests.test_tryton
from trytond.pool import Pool
from trytond.tests.test_tryton import ModuleTestCase, with_transaction
from trytond.modules.company.tests import create_company, set_company


class RRHHTestCase(ModuleTestCase):
    'Test rrhh module'
    module = 'rrhh'

    @with_transaction()
    def test_rrhh(self):
        pool = Pool()
        Employee = pool.get('company.employee')
        Department = pool.get('rrhh.department')
        Position = pool.get('rrhh.position')
        InstructionLevel = pool.get('rrhh.instruction.level')
        Dependent = pool.get('rrhh.dependent')
        DependentRelation = pool.get('rrhh.dependent.relation')
        DocumentType = pool.get('rrhh.document.type')
        Document = pool.get('rrhh.document')
        Qualification = pool.get('rrhh.qualification')
        QualificationDegree = pool.get('rrhh.qualification.degree')
        ContractType = pool.get('rrhh.contract.type')
        PaymentType = pool.get('rrhh.payment.type')

        company = create_company()
        with set_company(company):
            pass

def suite():
    suite = trytond.tests.test_tryton.suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
        RRHHTestCase))
    return suite
