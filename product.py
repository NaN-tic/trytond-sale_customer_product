#This file is part of sale_customer_product module for Tryton.  The COPYRIGHT
#file at the top level of this repository contains the full copyright
#notices and license terms.

import datetime

from trytond.model import ModelView, ModelSQL, fields
from trytond.pyson import Eval, If
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction
from trytond import backend

__all__ = ['Template', 'ProductCustomer']
__metaclass__ = PoolMeta


class Template:
    __name__ = "product.template"
    product_customers = fields.One2Many('sale.product_customer',
        'product', 'Customers', states={
            'readonly': ~Eval('active', True),
            'invisible': (~Eval('salable', False)
                | ~Eval('context', {}).get('company')),
            }, depends=['active', 'salable'])


class ProductCustomer(ModelSQL, ModelView):
    'Product Customer'

    __name__ = 'sale.product_customer'

    product = fields.Many2One('product.template', 'Product', required=True,
            ondelete='CASCADE', select=True)
    party = fields.Many2One('party.party', 'Customer', required=True,
            ondelete='CASCADE', select=True)
    name = fields.Char('Name', size=None, translate=True, select=True)
    code = fields.Char('Code', size=None, select=True)
    company = fields.Many2One('company.company', 'Company', required=True,
        ondelete='CASCADE', select=True,
        domain=[
            ('id', If(Eval('context', {}).contains('company'), '=', '!='),
                Eval('context', {}).get('company', -1)),
            ])

    @staticmethod
    def default_company():
        return Transaction().context.get('company')

    def get_rec_name(self, name):
        if self.code:
            return '[' + self.code + '] ' + self.name
        else:
            return self.name

    @classmethod
    def search_rec_name(cls, name, clause):
        ids = map(int, cls.search([('code',) + tuple(clause[1:])], order=[]))
        if ids:
            ids += map(int,
                cls.search([('name',) + tuple(clause[1:])], order=[]))
            return [('id', 'in', ids)]
        return super(ProductCustomer, cls).search_rec_name(name, clause)
