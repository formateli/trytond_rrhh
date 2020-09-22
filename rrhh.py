# This file is part of RRHH module.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.model import ModelView, ModelSQL, fields, Unique
from trytond.pool import Pool, PoolMeta
from datetime import datetime
from dateutil.relativedelta import relativedelta
from trytond.transaction import Transaction
from trytond.pyson import Bool, Eval, If


class Employee(metaclass=PoolMeta):
    __name__ = 'company.employee'
    photo = fields.Binary('Photo', file_id='photo_id')
    photo_id = fields.Char('Photo id', states={'invisible': True})
    position = fields.Many2One('rrhh.position', 'Position', required=True,
        domain=[('department.company', '=', Eval('company'))],
        depends=['company'])
    department = fields.Function(fields.Char('Department'), 'get_department')
    contract_type = fields.Many2One('rrhh.contract.type',
        'Contract type', required=True,
        domain=[('company', '=', Eval('company'))],
        depends=['company'])
    payment_type = fields.Many2One('rrhh.payment.type',
        'Payment type', required=True)
    instruction_level = fields.Many2One('rrhh.instruction.level',
        'Instruction level', required=True)
    documents = fields.One2Many('rrhh.document', 'employee', 'Documents')
    qualifications = fields.One2Many('rrhh.qualification',
        'employee', 'Qualification')
    marital_status = fields.Function(fields.Char('Legal State'),
        'get_marital_status')
    gender = fields.Function(fields.Char('Gender'),
        'get_gender')
    birth_date = fields.Function(fields.Date('Birth date'),
        'get_birth_date')
    birth_country = fields.Many2One('country.country',
        'Country of birth', states={'required': True})
    nationality = fields.Many2One('country.country',
        'Nationality', states={'required': True})
    residence = fields.Many2One('country.country',
        'Country of residence', states={'required': True})
    age = fields.Function(fields.Char('Age'), 'get_age')
    dependents = fields.One2Many('rrhh.dependent', 'employee', 'Dependents')

    @classmethod
    def __register__(cls, module_name):
        super(Employee, cls).__register__(module_name)

        table = cls.__table_handler__(module_name)
        # To 5.2
        if table.column_exist('first_name'):
            table.drop_column('first_name')
            table.drop_column('middle_name')
            table.drop_column('last_name')

        # To 5.6.1
        if table.column_exist('birth_date'):
            table.drop_column('birth_date')
            table.drop_column('genre')
            table.drop_column('marital_status')

    @classmethod
    def __setup__(cls):
        super(Employee, cls).__setup__()

        cls.company.states['readonly'] = True

        cls.party.domain = [
                ('party_type', '=', 'person')
            ]

    @staticmethod
    def default_company():
        return Transaction().context.get('company')

    @staticmethod
    def compute_age(party_dob):
        # TODO Translate with gettext
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

    def get_marital_status(self, name):
        return self._get_party_selection_string('person_legal_state')

    def get_gender(self, name):
        return self._get_party_selection_string('gender')

    def _get_party_selection_string(self, sel_name):
        pool = Pool()
        Trans = pool.get('ir.translation')
        Party = pool.get('party.party')
        if self.party:
            selection = getattr(Party, sel_name).selection
            sel = dict(selection)[getattr(self.party, sel_name)]
            lang = Transaction().context.get('language', None)
            val = Trans.get_source(
                'party.party,' + sel_name,
                'selection',
                lang,
                sel)
            if not val:
                val = sel
            return val

    def get_birth_date(self, name):
        if self.party:
            return self.party.dob

    @fields.depends('position')
    def on_change_company(self):
        self.position = None


class Dependent(ModelSQL, ModelView):
    'Employee dependents'
    __name__ = 'rrhh.dependent'
    name = fields.Char('Name', required=True)
    employee = fields.Many2One('company.employee',
        'Employee', required=True)
    relation = fields.Many2One('rrhh.dependent.relation',
        'Relation', required=True)
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
            ],
        select=True)
    name = fields.Char('Name', required=True, translate=True)
    parent = fields.Many2One('rrhh.department', 'Parent',
        domain=[
            If(Bool(Eval('company')),
                ('company', '=', Eval('company')),
                ('company', '=', None))
            ],
        depends=['company'])
    childs = fields.One2Many('rrhh.department', 'parent',
        'Children', readonly=True)
    positions = fields.One2Many('rrhh.position', 'department',
        'Positions', readonly=True)
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
    department = fields.Many2One('rrhh.department',
        'Department', required=True)
    parent = fields.Many2One('rrhh.position', 'Parent',
        domain=[
            If(Bool(Eval('department')),
                ('department', '=', Eval('department')),
                ('department', '=', None)),
            ], depends=['department'])
    childs = fields.One2Many('rrhh.position', 'parent',
        'Children', readonly=True)
    description = fields.Text('Description')
    active = fields.Boolean('Active')

    @staticmethod
    def default_active():
        return True

    @fields.depends()
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
    copy_image = fields.Binary('Copy', file_id='copy_id')
    copy_id = fields.Char('Copy id', states={'invisible': True})
    country = fields.Many2One('country.country', 'Country', required=True)
    description = fields.Char('Number', help="Document description or number")
    date_issue = fields.Date('Issue date')
    date_expiration = fields.Date('Expiration date')
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
        ], 'Type', required=True,
        translate=True, help='Qualification type')
    degree = fields.Many2One('rrhh.qualification.degree', 'Degree',
        help='The qualification degree, if applicable. '
             'It could be "None", "Unfinished" or any valid degree.')
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
