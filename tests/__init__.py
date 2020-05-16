# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
try:
    from trytond.modules.rrhh.tests.test_rrhh import suite, create_employee
except ImportError:
    from .test_rrhh import suite, create_employee


__all__ = ['suite', 'create_employee']
