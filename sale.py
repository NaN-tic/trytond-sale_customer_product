# This file is part of sale_customer_product module for Tryton.  The COPYRIGHT
# file at the top level of this repository contains the full copyright
# notices and license terms.
from trytond.model import fields
from trytond.pyson import Eval
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction

__all__ = ['SaleLine']


class SaleLine(metaclass=PoolMeta):
    __name__ = 'sale.line'

    @classmethod
    def __setup__(cls):
        super(SaleLine, cls).__setup__()
        cls.product.context['sale_customer'] = Eval('_parent_sale',
            {}).get('party')
