#This file is part of tryton-rrhh project. The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.

from trytond.pool import Pool
from .rrhh import *


def register():
    Pool.register(
        Employee,
        Department,
        Position,
        InstructionLevel,
        DocumentType,
        Document,
        DependentRelation,
        Dependent,
        QualificationDegree,
        Qualification,
        ContractType, 
        PaymentType,
        module='rrhh', type_='model')
