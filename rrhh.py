# This file is part of RRHH module.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.model import ModelView, ModelSQL, fields, Unique, tree
from trytond.pool import Pool, PoolMeta
from datetime import datetime
from dateutil.relativedelta import relativedelta
from trytond.transaction import Transaction
from trytond.pyson import Bool, Eval, If


class Employee(metaclass=PoolMeta):
    __name__ = 'company.employee'
    photo = fields.Binary('Photo', file_id='photo_id')
    photo_id = fields.Char('Photo id', states={'invisible': True})
    position = fields.Many2One('rrhh.position', 'Position', required=True)
    department = fields.Many2One('rrhh.department', 'Department',
        required=True,
        domain=[
            ('company', '=', Eval('company'))
        ], depends=['company'])
    instruction_level = fields.Many2One('rrhh.instruction.level',
        'Instruction level', required=True)
    documents = fields.One2Many('rrhh.document', 'employee', 'Documents')
    qualifications = fields.One2Many('rrhh.qualification',
        'employee', 'Qualification')
    marital_status = fields.Function(fields.Char('Legal State'),
        'on_change_with_marital_status')
    gender = fields.Function(fields.Char('Gender'),
        'on_change_with_gender')
    birth_date = fields.Function(fields.Date('Birth date'),
        'on_change_with_birth_date')
    birth_country = fields.Many2One('country.country',
        'Country of birth', states={'required': True})
    nationality = fields.Many2One('country.country',
        'Nationality', states={'required': True})
    residence = fields.Many2One('country.country',
        'Country of residence', states={'required': True})
    age = fields.Function(fields.Char('Age'),
        'on_change_with_age')
    dependents = fields.One2Many('rrhh.dependent', 'employee', 'Dependents')
    contracts = fields.One2Many('rrhh.contract', 'employee', 'Contracts')

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

    @fields.depends('party', 'birth_date')
    def on_change_with_age(self, name=None):
        if self.party and self.birth_date:
            return self.compute_age(self.birth_date)

    @fields.depends('party')
    def on_change_with_marital_status(self, name=None):
        return self._get_party_selection_string('person_legal_state')

    @fields.depends('party')
    def on_change_with_gender(self, name=None):
        return self._get_party_selection_string('gender')

    def _get_party_selection_string(self, sel_name):
        pool = Pool()
        Trans = pool.get('ir.translation')
        Party = pool.get('party.party')
        if self.party:
            selection = getattr(Party, sel_name).selection
            sel = dict(selection)[getattr(self.party, sel_name)]
            lang = Transaction().context.get('language', None)
            if lang in (None, '', 'en'):
                return sel
            val = Trans.get_source(
                'party.party,' + sel_name,
                'selection',
                lang,
                sel)
            if not val:
                val = sel
            return val

    @fields.depends('party')
    def on_change_with_birth_date(self, name=None):
        if self.party:
            return self.party.dob

    @fields.depends('position')
    def on_change_company(self):
        self.department = None


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


class Department(tree(separator=' / '), ModelSQL, ModelView):
    'Company Department'
    __name__ = 'rrhh.department'
    company = fields.Many2One('company.company', 'Company', required=True,
        states={
            'readonly': True,
            },
        domain=[
            ('id', If(Eval('context', {}).contains('company'), '=', '!='),
                Eval('context', {}).get('company', -1)),
            ])
    name = fields.Char('Name', required=True, translate=True)
    parent = fields.Many2One('rrhh.department', 'Parent',
        domain=[
            ('id', '!=', Eval('id', -1)),
            If(Bool(Eval('company')),
                ('company', '=', Eval('company')),
                ('company', '=', -1)
                ),
        ],
        depends=['id', 'company'])
    childs = fields.One2Many('rrhh.department', 'parent',
        'Children', readonly=True)
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
    description = fields.Text('Description')
    active = fields.Boolean('Active')

    @staticmethod
    def default_active():
        return True


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
    employee = fields.Many2One('company.employee', 'Employee', required=True,
            ondelete='CASCADE')
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
            ])
    name = fields.Char('Name', required=True, translate=True)
    conditions = fields.Text('Conditions')

    @staticmethod
    def default_company():
        return Transaction().context.get('company')


class Contract(ModelSQL, ModelView):
    'Contract'
    __name__ = 'rrhh.contract'
    employee = fields.Many2One('company.employee', 'Employee', required=True,
        ondelete='CASCADE')
    type = fields.Many2One('rrhh.contract.type', 'Type', required=True,
        domain=[
            ('company', '=', Eval('context', {}).get('company', -1)),
            ])
    payment_type = fields.Many2One('rrhh.payment.type',
        'Payment type', required=True)
    start_date = fields.Date('Start date')
    end_date = fields.Date('End date')
    conditions = fields.Text('Conditions')
    active = fields.Boolean('Active')


class PaymentType(ModelSQL, ModelView):
    'Contract Payment type'
    __name__ = 'rrhh.payment.type'
    name = fields.Char('Name', required=True, translate=True)
    active = fields.Boolean('Active')

    @staticmethod
    def default_active():
        return True
