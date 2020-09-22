# This file is part of RRHH module.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.pool import Pool
from . import rrhh


def register():
    Pool.register(
        rrhh.Employee,
        rrhh.Department,
        rrhh.Position,
        rrhh.InstructionLevel,
        rrhh.DocumentType,
        rrhh.Document,
        rrhh.DependentRelation,
        rrhh.Dependent,
        rrhh.QualificationDegree,
        rrhh.Qualification,
        rrhh.ContractType,
        rrhh.PaymentType,
        module='rrhh', type_='model')
