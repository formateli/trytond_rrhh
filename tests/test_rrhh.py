# This file is part of RRHH module.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
import unittest
import datetime
import trytond.tests.test_tryton
from trytond.pool import Pool
from trytond.tests.test_tryton import ModuleTestCase, with_transaction
from trytond.modules.company.tests import create_company, set_company

__all__ = ['create_employee']


class RRHHTestCase(ModuleTestCase):
    'Test rrhh module'
    module = 'rrhh'

    @with_transaction()
    def test_rrhh(self):
        pool = Pool()
        Dependent = pool.get('rrhh.dependent')
        DependentRelation = pool.get('rrhh.dependent.relation')
        DocumentType = pool.get('rrhh.document.type')
        Document = pool.get('rrhh.document')
        Qualification = pool.get('rrhh.qualification')
        QualificationDegree = pool.get('rrhh.qualification.degree')

        company = create_company()
        with set_company(company):
            employee = create_employee('Employee 1')
            employee.save()
            self.assertTrue(employee.id)


def create_employee(name):
    pool = Pool()
    Party = pool.get('party.party')
    Country = pool.get('country.country')
    Employee = pool.get('company.employee')
    Department = pool.get('rrhh.department')
    Position = pool.get('rrhh.position')
    ContractType = pool.get('rrhh.contract.type')
    PaymentType = pool.get('rrhh.payment.type')
    InstructionLevel = pool.get('rrhh.instruction.level')

    party = Party(
        name=name,
        party_type='person',
        gender='male',
        person_legal_state='single',
        dob=datetime.date(year=1969, month=8, day=29),
        )
    party.save()

    department = Department(name='Department')
    department.save()

    position = Position(name='Position', department=department)
    position.save()

    contract_type = ContractType(name='Full Time')
    contract_type.save()

    country = Country(name='Panama')
    country.save()

    employee = Employee(
        party=party,
        start_date=datetime.date(year=2020, month=1, day=1),
        position=position,
        contract_type=contract_type,
        payment_type=PaymentType.search([
            ('name', '=', 'ACH')])[0],
        instruction_level=InstructionLevel.search([
            ('name', '=', 'University')])[0],
        birth_country=country,
        nationality=country,
        residence=country,
        )

    return employee


def suite():
    suite = trytond.tests.test_tryton.suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
        RRHHTestCase))
    return suite
