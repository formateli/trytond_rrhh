#This file is part of tryton-rrhh project. The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
from trytond.model import ModelView, ModelSQL, fields, Unique
from trytond.pool import Pool, PoolMeta
from datetime import datetime
from dateutil.relativedelta import relativedelta
from trytond.transaction import Transaction
from trytond.pyson import Bool, Eval, If

__all__ = [
        'Employee',
        'Department',
        'Position',
        'InstructionLevel',
        'Dependent',
        'DependentRelation',
        'DocumentType',
        'Document',
        'Qualification',
        'QualificationDegree',
        'ContractType',
        'PaymentType',
    ]


class Employee:
    __metaclass__ = PoolMeta
    __name__ = 'company.employee'
  
    first_name = fields.Char('First name', required=True)
    middle_name = fields.Char('Middle name')
    last_name = fields.Char('Last name', required=True)
    photo = fields.Binary('Photo')
    position = fields.Many2One('rrhh.position', 'Position', required=True, 
        domain=[('department.company', '=', Eval('company'))],
        depends=['company'])
    department = fields.Function(fields.Char('Department'), 'get_department')
    contract_type = fields.Many2One('rrhh.contract.type', 'Contract type', required=True,
        domain=[('company', '=', Eval('company'))],
        depends=['company'])
    payment_type = fields.Many2One('rrhh.payment.type', 'Payment type', required=True) 
    instruction_level = fields.Many2One('rrhh.instruction.level',
        'Instruction level', required=True)
    documents = fields.One2Many('rrhh.document', 'employee', 'Documents')
    qualifications = fields.One2Many('rrhh.qualification', 'employee', 'Qualification')
    supervisor = fields.Many2One('company.employee', 'Supervisor',
        domain=[('company', '=', Eval('company'))],
        depends=['company']) 
    subordinates = fields.One2Many('company.employee', 'supervisor',
        'Subordinates', readonly=True)
    marital_status = fields.Selection([
        ('single', 'Single'),
        ('married', 'Married'),
        ('divorced', 'Divorced'),
        ('widowed', 'Widowed'),
        ('other', 'Other'),
    ], 'Marital status', required=True)
    genre = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
    ], 'Genre', required=True)
    birth_date = fields.Date('Birth date', required=True)
    birth_country = fields.Many2One('country.country', 'Country of birth', required=True)
    nationality = fields.Many2One('country.country', 'Nationality', required=True)
    residence = fields.Many2One('country.country', 'Country of residence', required=True)
    age = fields.Function(fields.Char('Age'), 'get_age')
    dependents = fields.One2Many('rrhh.dependent', 'employee', 'Dependents')

    @staticmethod
    def default_company():
        return Transaction().context.get('company')

    @staticmethod
    def compute_age(party_dob):
        if not party_dob:
            return 'No Birth date!'

        now = datetime.now()
        dob = datetime.strptime(str(party_dob), '%Y-%m-%d')
        delta = relativedelta(now, dob)

        years_months_days = str(delta.years) + 'y ' \
                + str(delta.months) + 'm ' \
                + str(delta.days) + 'd'

        return years_months_days

    def get_age(self, name):
        return self.compute_age(self.birth_date)

    def get_department(self, name):
        if self.position:
            return self.position.department.name

    @fields.depends('company')
    def on_change_company(self):
        self.position = None


class Dependent(ModelSQL, ModelView):
    'Employee dependents'
    __name__ = 'rrhh.dependent'
    name = fields.Char('Name', required=True)
    employee = fields.Many2One('company.employee', 'Employee', required=True)
    relation = fields.Many2One('rrhh.dependent.relation', 'Relation', required=True)
    birth_date = fields.Date('Birth date', required=True)
    age = fields.Function(fields.Char('Age'), 'get_age')
    notes = fields.Text('Notes')

    def get_age(self, name):
        employee = Pool().get('company.employee')
        return employee.compute_age(self.birth_date)


class DependentRelation(ModelSQL, ModelView):
    'Dependent relation'
    __name__ = 'rrhh.dependent.relation'
    name = fields.Char('Name', required=True, translate=True)
    active = fields.Boolean('Active')

    @staticmethod
    def default_active():
        return True


class Department(ModelSQL, ModelView):
    'Company Department'
    __name__ = 'rrhh.department'

    company = fields.Many2One('company.company', 'Company', required=True,
        states={
            'readonly': True,
        },
        domain=[
            ('id', If(Eval('context', {}).contains('company'), '=', '!='),
                Eval('context', {}).get('company', -1)),
        ], select=True)
    name = fields.Char('Name', required=True, translate=True)
    parent = fields.Many2One('rrhh.department', 'Parent',
        domain=[
            If(Bool(Eval('company')),
                ('company', '=', Eval('company')),
                ('company', '=', None))],
        depends=['company'])
    childs = fields.One2Many('rrhh.department', 'parent', 'Children', readonly=True)
    positions = fields.One2Many('rrhh.position', 'department', 'Positions', readonly=True)
    active = fields.Boolean('Active')

    @staticmethod
    def default_active():
        return True

    @staticmethod
    def default_company():
        return Transaction().context.get('company')


class Position(ModelSQL, ModelView):
    'Company Position'
    __name__ = 'rrhh.position'

    name = fields.Char('Name', required=True, translate=True)
    department = fields.Many2One('rrhh.department', 'Department', required=True)
    parent = fields.Many2One('rrhh.position', 'Parent',
        domain=[
            If(Bool(Eval('department')),
                ('department', '=', Eval('department')),
                ('department', '=', None)),
            ], depends=['department'])
    childs = fields.One2Many('rrhh.position', 'parent', 'Children', readonly=True)
    description = fields.Text('Description')
    active = fields.Boolean('Active')

    @staticmethod
    def default_active():
        return True

    @fields.depends('department', 'parent')
    def on_change_department(self):
        self.parent = None

    def get_rec_name(self, name):
        return self.department.name + ' / ' + self.name

    @classmethod
    def search_rec_name(cls, name, clause):
        domain = ['OR']
        domain.append(('department.name', clause[1], clause[2]))
        domain.append(('name', clause[1], clause[2]))
        return domain


class InstructionLevel(ModelSQL, ModelView):
    'Instruction level'
    __name__ = 'rrhh.instruction.level'
    name = fields.Char('Name', required=True, translate=True)
    active = fields.Boolean('Active')

    @staticmethod
    def default_active():
        return True


class DocumentType(ModelSQL, ModelView):
    'Document type'
    __name__ = 'rrhh.document.type'
    name = fields.Char('Name', required=True, translate=True)
    notes = fields.Text('Notes')


class Document(ModelSQL, ModelView):
    'Employee document'
    __name__ = 'rrhh.document'

    employee = fields.Many2One('company.employee', 'Employee', required=True)
    type = fields.Many2One('rrhh.document.type', 'Type', required=True)
    copy = fields.Binary('Copy')
    country = fields.Many2One('country.country', 'Country', required=True)
    description = fields.Char('Number', help="Document description or number")
    date_issue = fields.Date('Issue date')
    date_expiration = fields.Date('Expiration date')
    mandatory = fields.Boolean('Mandatory')
    notes = fields.Text('Notes')

    @classmethod
    def __setup__(cls):
        super(Document, cls).__setup__()
        t = cls.__table__()
        cls._sql_constraints += [
            ('rrhh_doc_uniq', 
                Unique(t, t.employee, t.type, t.country),
                'Employee document must be uniq per type and country!'),
        ]

    @staticmethod
    def default_mandatory():
        return False

    def get_rec_name(self, name):
        return self.type.rec_name


class Qualification(ModelSQL, ModelView):
    'Qualification'
    __name__ = 'rrhh.qualification'

    employee = fields.Many2One('company.employee', 'Employee', required=True)
    name = fields.Char('Name', required=True, translate=True)
    type = fields.Selection([
        ('education', 'Education'),
        ('certification', 'Certification'),
        ('work', 'Work experience'),
        ('skill', 'Skill'),
        ('language', 'Language'),
    ], 'Type', required=True, translate=True, help='Qualification type')
    degree = fields.Many2One('rrhh.qualification.degree', 'Degree', 
        help='The qualification degree, if applicable. It could be "None", "Unfinished" or any valid degree.')
    notes = fields.Text('Notes')

    @classmethod
    def __setup__(cls):
        super(Qualification, cls).__setup__()
        cls._order = [
                ('type', 'DESC'),
            ]


class QualificationDegree(ModelSQL, ModelView):
    'Qualification degree'
    __name__ = 'rrhh.qualification.degree'
    name = fields.Char('Name', required=True, translate=True) 
    active = fields.Boolean('Active')

    @staticmethod
    def default_active():
        return True


class ContractType(ModelSQL, ModelView):
    'Contract type'
    __name__ = 'rrhh.contract.type'

    company = fields.Many2One('company.company', 'Company', required=True,
        states={
            'readonly': True,
            },
        domain=[
            ('id', If(Eval('context', {}).contains('company'), '=', '!='),
                Eval('context', {}).get('company', -1)),
            ], select=True)
    name = fields.Char('Name', required=True, translate=True)
    conditions = fields.Text('Conditions')

    @staticmethod
    def default_company():
        return Transaction().context.get('company')


class PaymentType(ModelSQL, ModelView):
    'Contract Payment type'
    __name__ = 'rrhh.payment.type'
    name = fields.Char('Name', required=True, translate=True)
    active = fields.Boolean('Active')

    @staticmethod
    def default_active():
        return True
